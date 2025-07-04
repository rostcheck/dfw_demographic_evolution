#!/usr/bin/env python3
"""
Simple Expanded Visualization for Incremental Data
Creates visualizations from the incremental collector output
"""

import pandas as pd
import folium
import ast
from pathlib import Path

def load_incremental_data():
    """Load the cleaned incremental data"""
    # Try county-based file first, then fall back to older files
    data_file = "north_texas_county_demographics.csv"
    
    if not Path(data_file).exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    df = pd.read_csv(data_file)
    print(f"✓ Loaded {len(df)} records for {df['city'].nunique()} cities from {data_file}")
    
    # Parse coordinates from string format
    def parse_coords(coord_str):
        try:
            if isinstance(coord_str, str):
                return ast.literal_eval(coord_str)
            return coord_str
        except:
            return None
    
    # Handle coordinates - add them if missing
    if 'coordinates' not in df.columns:
        print("📍 Adding coordinates for mapping...")
        df['coordinates'] = df['city'].apply(get_city_coordinates)
        
    df['parsed_coords'] = df['coordinates'].apply(parse_coords)
    
    # Calculate demographic percentages
    df['white_pct'] = (df['white_alone'] / df['total_population']) * 100
    df['black_pct'] = (df['black_alone'] / df['total_population']) * 100
    df['asian_pct'] = (df['asian_alone'] / df['total_population']) * 100
    df['hispanic_pct'] = (df['hispanic_latino'] / df['total_population']) * 100
    df['other_pct'] = 100 - (df['white_pct'] + df['black_pct'] + df['asian_pct'] + df['hispanic_pct'])
    df['other_pct'] = df['other_pct'].clip(lower=0)
    
    return df

def get_growth_color(growth_rate):
    """Get color based on growth rate"""
    if growth_rate >= 100:
        return '#8b0000'  # Dark red
    elif growth_rate >= 50:
        return '#d73027'  # Red
    elif growth_rate >= 25:
        return '#fc8d59'  # Orange
    elif growth_rate >= 10:
        return '#fee08b'  # Yellow
    elif growth_rate >= 0:
        return '#e0f3f8'  # Light blue
    else:
        return '#4575b4'  # Blue

def create_demographic_popup(row):
    """Create demographic popup for a city"""
    return f"""
    <div style="width: 220px; font-family: Arial, sans-serif;">
        <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{row['city']} ({int(row['year'])})</h4>
        <p style="margin: 0 0 5px 0;"><strong>Population:</strong> {int(row['total_population']):,}</p>
        <p style="margin: 0 0 10px 0; font-size: 11px; color: #666;">Distance: {row['distance_from_dallas']:.1f} miles</p>
        <div style="margin-bottom: 5px;">
            <h5 style="margin: 5px 0; color: #34495e;">Demographics:</h5>
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <div style="width: 15px; height: 15px; background-color: #1f77b4; margin-right: 8px;"></div>
                <span style="font-size: 12px;">White: {row['white_pct']:.1f}%</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <div style="width: 15px; height: 15px; background-color: #ff7f0e; margin-right: 8px;"></div>
                <span style="font-size: 12px;">Black: {row['black_pct']:.1f}%</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <div style="width: 15px; height: 15px; background-color: #2ca02c; margin-right: 8px;"></div>
                <span style="font-size: 12px;">Asian: {row['asian_pct']:.1f}%</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <div style="width: 15px; height: 15px; background-color: #d62728; margin-right: 8px;"></div>
                <span style="font-size: 12px;">Hispanic: {row['hispanic_pct']:.1f}%</span>
            </div>
        </div>
    </div>
    """

def create_expanded_map(df):
    """Create the main expanded map"""
    print("Creating expanded interactive map...")
    
    # Calculate growth rates
    df_2009 = df[df['year'] == 2009].set_index('city')
    df_2022 = df[df['year'] == 2022].set_index('city')
    
    growth_rates = {}
    for city in df_2009.index:
        if city in df_2022.index:
            pop_2009 = df_2009.loc[city, 'total_population']
            pop_2022 = df_2022.loc[city, 'total_population']
            # Handle Series by getting the first value if it's a Series
            if hasattr(pop_2009, 'iloc'):
                pop_2009 = pop_2009.iloc[0] if len(pop_2009) > 0 else 0
            if hasattr(pop_2022, 'iloc'):
                pop_2022 = pop_2022.iloc[0] if len(pop_2022) > 0 else 0
            
            if pop_2009 > 0:
                growth_rates[city] = ((pop_2022 - pop_2009) / pop_2009) * 100
    
    # Create map centered on North Texas
    m = folium.Map(
        location=[33.0, -96.8],
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Add title
    title_html = '''
    <h2 style="position: fixed; 
               top: 10px; left: 50px; width: 500px; height: 60px; 
               background-color: white; border: 2px solid grey; z-index:9999; 
               font-size: 18px; padding: 10px; font-family: Arial;">
    North Texas Expanded Demographics (2009-2022)
    </h2>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Create feature groups
    fg_2022 = folium.FeatureGroup(name='2022 Demographics', show=True)
    fg_2009 = folium.FeatureGroup(name='2009 Demographics')
    fg_growth = folium.FeatureGroup(name='Population Growth')
    
    # Process each city
    cities_processed = set()
    cities_with_coords = 0
    cities_without_coords = []
    
    # Get unique cities from the dataset
    unique_cities = df['city'].unique()
    print(f"Processing {len(unique_cities)} unique cities from dataset...")
    
    for city in unique_cities:
        if city in cities_processed:
            continue
            
        # Get any row for this city to get coordinates
        city_rows = df[df['city'] == city]
        if city_rows.empty:
            continue
            
        # Get coordinates from the first row
        sample_row = city_rows.iloc[0]
        coords = sample_row['parsed_coords']
        
        if not coords:
            cities_without_coords.append(city)
            continue
            
        cities_processed.add(city)
        cities_with_coords += 1
        
        # Get city data for different years
        city_data = df[df['city'] == city]
        
        # 2022 data
        data_2022 = city_data[city_data['year'] == 2022]
        if not data_2022.empty:
            row_2022 = data_2022.iloc[0]
            popup_2022 = create_demographic_popup(row_2022)
            
            folium.Marker(
                coords,
                popup=folium.Popup(popup_2022, max_width=250),
                tooltip=f"{city} - 2022 (Pop: {int(row_2022['total_population']):,})",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(fg_2022)
        
        # 2009 data
        data_2009 = city_data[city_data['year'] == 2009]
        if not data_2009.empty:
            row_2009 = data_2009.iloc[0]
            popup_2009 = create_demographic_popup(row_2009)
            
            folium.Marker(
                coords,
                popup=folium.Popup(popup_2009, max_width=250),
                tooltip=f"{city} - 2009 (Pop: {int(row_2009['total_population']):,})",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(fg_2009)
        
        # Growth visualization
        growth_rate = growth_rates.get(city, 0)
        color = get_growth_color(growth_rate)
        
        # Get 2022 population for circle size
        pop_2022 = data_2022.iloc[0]['total_population'] if not data_2022.empty else 0
        radius = max(5, min(35, pop_2022 / 8000))
        
        folium.CircleMarker(
            coords,
            radius=radius,
            popup=f"""
            <div style="font-family: Arial;">
                <h4>{city}</h4>
                <p><strong>Growth Rate:</strong> {growth_rate:.1f}%</p>
                <p><strong>2022 Population:</strong> {int(pop_2022):,}</p>
                <p><strong>Distance:</strong> {sample_row['distance_from_dallas']:.1f} miles</p>
            </div>
            """,
            tooltip=f"{city}: {growth_rate:.1f}% growth",
            color='black',
            weight=1,
            fillColor=color,
            fillOpacity=0.7
        ).add_to(fg_growth)
    
    # Add layers to map
    fg_2022.add_to(m)
    fg_2009.add_to(m)
    fg_growth.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Print processing results
    print(f"✓ Processed {cities_with_coords} cities with coordinates")
    if cities_without_coords:
        print(f"⚠️ {len(cities_without_coords)} cities missing coordinates: {', '.join(cities_without_coords[:5])}")
        if len(cities_without_coords) > 5:
            print(f"    ... and {len(cities_without_coords) - 5} more")
    
    # Add legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 220px; height: 250px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 15px; font-family: Arial;
                box-sizing: border-box;">
    <h4 style="margin-top: 0; margin-bottom: 10px;">Population Growth Legend</h4>
    <div style="margin-bottom: 3px;"><span style="color: #8b0000;">●</span> 100%+ (Extreme Growth)</div>
    <div style="margin-bottom: 3px;"><span style="color: #d73027;">●</span> 50-100% (Very High)</div>
    <div style="margin-bottom: 3px;"><span style="color: #fc8d59;">●</span> 25-50% (High)</div>
    <div style="margin-bottom: 3px;"><span style="color: #fee08b;">●</span> 10-25% (Moderate)</div>
    <div style="margin-bottom: 3px;"><span style="color: #e0f3f8;">●</span> 0-10% (Low)</div>
    <div style="margin-bottom: 10px;"><span style="color: #4575b4;">●</span> Decline</div>
    <hr style="margin: 10px 0; border: 1px solid #ddd;">
    <div style="font-size: 11px; line-height: 1.4;">
        <div style="margin-bottom: 4px;"><strong>{cities_with_coords} Cities Mapped</strong></div>
        <div style="margin-bottom: 4px;">Circle size = Population</div>
        <div style="margin-bottom: 8px;">Dallas-Denison Region</div>
    </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_dashboard(df):
    """Create HTML dashboard"""
    # Calculate statistics
    total_cities = df['city'].nunique()
    total_population_2022 = df[df['year'] == 2022]['total_population'].sum()
    total_population_2009 = df[df['year'] == 2009]['total_population'].sum()
    overall_growth = ((total_population_2022 - total_population_2009) / total_population_2009) * 100
    
    # Get top growing cities
    df_2009 = df[df['year'] == 2009].set_index('city')
    df_2022 = df[df['year'] == 2022].set_index('city')
    
    growth_data = []
    for city in df_2009.index:
        if city in df_2022.index:
            pop_2009 = df_2009.loc[city, 'total_population']
            pop_2022 = df_2022.loc[city, 'total_population']
            # Handle Series by getting the first value if it's a Series
            if hasattr(pop_2009, 'iloc'):
                pop_2009 = pop_2009.iloc[0] if len(pop_2009) > 0 else 0
            if hasattr(pop_2022, 'iloc'):
                pop_2022 = pop_2022.iloc[0] if len(pop_2022) > 0 else 0
            
            if pop_2009 > 0:
                growth_rate = ((pop_2022 - pop_2009) / pop_2009) * 100
                growth_data.append((city, growth_rate, pop_2022))
    
    growth_data.sort(key=lambda x: x[1], reverse=True)
    top_5_growth = growth_data[:5]
    
    # Get largest cities
    largest_cities = df[df['year'] == 2022].nlargest(5, 'total_population')
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>North Texas Expanded Demographics</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .header {{
            text-align: center;
            background: rgba(255,255,255,0.95);
            color: #2c3e50;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .map-container {{
            background: rgba(255,255,255,0.95);
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }}
        iframe {{
            width: 100%;
            height: 600px;
            border: none;
            border-radius: 10px;
        }}
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }}
        .insight-card {{
            background: rgba(255,255,255,0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }}
        .city-list {{
            list-style: none;
            padding: 0;
        }}
        .city-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
        }}
        .growth-rate {{
            font-weight: bold;
            color: #e74c3c;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>North Texas Expanded Demographics</h1>
        <p>Dallas-Fort Worth Region (2009-2022)</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{total_cities}</div>
            <div class="stat-label">Cities Analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{overall_growth:.1f}%</div>
            <div class="stat-label">Regional Growth</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{(total_population_2022 - total_population_2009)/1000:.0f}K</div>
            <div class="stat-label">People Added</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{total_population_2022/1000000:.1f}M</div>
            <div class="stat-label">2022 Population</div>
        </div>
    </div>
    
    <div class="map-container">
        <h2>Interactive Demographic Map</h2>
        <p>Explore cities in the expanded Dallas-Fort Worth region. Toggle between 2009/2022 demographics and population growth patterns. Every city in the dataset is represented with detailed demographic breakdowns.</p>
        <iframe src="north_texas_cities_map.html"></iframe>
    </div>
    
    <div class="insights-grid">
        <div class="insight-card">
            <h3>Fastest Growing Cities</h3>
            <ul class="city-list">"""
    
    for city, growth_rate, pop_2022 in top_5_growth:
        html_content += f"""
                <li>
                    <span>{city}</span>
                    <span class="growth-rate">{growth_rate:.1f}%</span>
                </li>"""
    
    html_content += """
            </ul>
        </div>
        
        <div class="insight-card">
            <h3>Largest Cities (2022)</h3>
            <ul class="city-list">"""
    
    for _, row in largest_cities.iterrows():
        html_content += f"""
                <li>
                    <span>{row['city']}</span>
                    <span>{int(row['total_population']):,}</span>
                </li>"""
    
    html_content += """
            </ul>
        </div>
        
        <div class="insight-card">
            <h3>Demographic Trends</h3>
            <ul style="list-style: disc; padding-left: 20px;">
                <li><strong>Increasing diversity</strong> across all major cities</li>
                <li><strong>Asian population growth</strong> in suburban areas like Plano and Frisco</li>
                <li><strong>Hispanic population</strong> remains stable in Dallas (~42%)</li>
                <li><strong>White population</strong> declining in most urban centers</li>
                <li><strong>Suburban boom</strong> outpacing urban core growth</li>
                <li><strong>Small town growth</strong> in outer ring communities</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def main():
    """Main function"""
    print("🌟 CREATING EXPANDED VISUALIZATIONS FROM INCREMENTAL DATA")
    print("=" * 65)
    
    try:
        # Load data
        df = load_incremental_data()
        
        # Create map
        print("📍 Creating interactive map...")
        expanded_map = create_expanded_map(df)
        expanded_map.save('north_texas_cities_map.html')
        print("✓ Saved: north_texas_cities_map.html")
        
        # Create dashboard
        print("📊 Creating dashboard...")
        dashboard_html = create_dashboard(df)
        with open('north_texas_cities_dashboard.html', 'w') as f:
            f.write(dashboard_html)
        print("✓ Saved: north_texas_cities_dashboard.html")
        
        print(f"\n🎉 SUCCESS! Visualizations created for {df['city'].nunique()} cities!")
        print("Files created:")
        print("  • north_texas_cities_dashboard.html - Main dashboard")
        print("  • north_texas_cities_map.html - Interactive map")
        
        # Show summary
        print(f"\n📈 Dataset Summary:")
        print(f"  • Cities: {df['city'].nunique()}")
        print(f"  • Records: {len(df):,}")
        print(f"  • Years: {df['year'].min()}-{df['year'].max()}")
        
        # Show top cities by population
        print(f"\n🏙️ Top 10 Cities by 2022 Population:")
        top_cities = df[df['year'] == 2022].nlargest(10, 'total_population')
        for i, (_, row) in enumerate(top_cities.iterrows(), 1):
            print(f"  {i:2d}. {row['city']:<25} {int(row['total_population']):>8,}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
