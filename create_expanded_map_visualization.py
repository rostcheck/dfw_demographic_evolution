#!/usr/bin/env python3
"""
Expanded Interactive Map Visualization for North Texas Region
Creates web-based maps for all cities within Dallas-Denison radius
"""

import pandas as pd
import folium
from folium import plugins
import json
import numpy as np
from pathlib import Path

def load_expanded_data():
    """Load the expanded demographic data"""
    # Try to find the most recent expanded dataset
    expanded_files = list(Path('.').glob('north_texas_expanded_demographics_*.csv'))
    
    if expanded_files:
        latest_file = max(expanded_files, key=lambda x: x.stat().st_mtime)
        print(f"Loading expanded data from: {latest_file}")
        df = pd.read_csv(latest_file)
    else:
        # Fall back to original data if expanded not available
        print("Expanded data not found, using original dataset...")
        csv_files = list(Path('.').glob('dfw_demographics_cleaned.csv'))
        if not csv_files:
            csv_files = list(Path('.').glob('dfw_major_cities_demographics_*.csv'))
        
        if not csv_files:
            raise FileNotFoundError("No demographic data files found")
        
        df = pd.read_csv(csv_files[0])
    
    # Clean and prepare data
    numeric_columns = ['year', 'total_population', 'white_alone', 'black_alone', 
                      'asian_alone', 'hispanic_latino']
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Clean city names if needed
    if 'city' not in df.columns:
        df['city'] = df['name'].str.replace(r', Texas$', '', regex=True)
    
    return df

def calculate_demographic_percentages(df):
    """Calculate demographic percentages for each city/year"""
    df = df.copy()
    
    # Calculate percentages
    df['white_pct'] = (df['white_alone'] / df['total_population']) * 100
    df['black_pct'] = (df['black_alone'] / df['total_population']) * 100
    df['asian_pct'] = (df['asian_alone'] / df['total_population']) * 100
    df['hispanic_pct'] = (df['hispanic_latino'] / df['total_population']) * 100
    
    # Calculate other/mixed (remaining percentage)
    df['other_pct'] = 100 - (df['white_pct'] + df['black_pct'] + df['asian_pct'] + df['hispanic_pct'])
    df['other_pct'] = df['other_pct'].clip(lower=0)
    
    return df

def get_city_coordinates_from_data(df):
    """Extract city coordinates from the data or use fallback mapping"""
    city_coords = {}
    
    # If coordinates are in the data, use them
    if 'coordinates' in df.columns:
        for _, row in df.iterrows():
            if pd.notna(row.get('coordinates')):
                try:
                    coords = eval(row['coordinates']) if isinstance(row['coordinates'], str) else row['coordinates']
                    if isinstance(coords, (list, tuple)) and len(coords) == 2:
                        city_coords[row['city']] = tuple(coords)
                except:
                    pass
    
    # Fallback coordinate mapping for cities not in data
    fallback_coords = {
        'Dallas city': (32.7767, -96.7970),
        'Fort Worth city': (32.7555, -97.3308),
        'Arlington city': (32.7357, -97.1081),
        'Plano city': (33.0198, -96.6989),
        'Irving city': (32.8140, -96.9489),
        'Garland city': (32.9126, -96.6389),
        'Grand Prairie city': (32.7459, -96.9978),
        'McKinney city': (33.1972, -96.6153),
        'Mesquite city': (32.7668, -96.5992),
        'Carrollton city': (32.9537, -96.8903),
        'Frisco city': (33.1507, -96.8236),
        'Denton city': (33.2148, -97.1331),
        'Richardson city': (32.9483, -96.7299),
        'Lewisville city': (33.0462, -96.9942),
        'Allen city': (33.1031, -96.6706),
        'Sherman city': (33.6356, -96.6089),
        'Denison city': (33.7557, -96.5367),
        'Gainesville city': (33.6262, -97.1336),
        'Greenville city': (33.1384, -96.1106),
        'Tyler city': (32.3513, -95.3011),
        'Athens city': (32.2049, -95.8555),
        'Corsicana city': (32.0954, -96.4689),
        'Waxahachie city': (32.3865, -96.8489),
        'Cleburne city': (32.3476, -97.3867),
        'Granbury city': (32.4421, -97.7947),
        'Weatherford city': (32.7593, -97.7975),
        'Mineral Wells city': (32.8085, -98.1128),
        'Terrell city': (32.7357, -96.2753),
        'Forney city': (32.7479, -96.4719),
        'Rockwall city': (32.9312, -96.4597),
        'Wylie city': (33.0151, -96.5389),
        'Rowlett city': (32.9029, -96.5639),
        'The Colony city': (33.0890, -96.8928),
        'Flower Mound town': (33.0145, -97.0969),
        'Southlake city': (32.9412, -97.1342),
        'Grapevine city': (32.9343, -97.0781),
        'Euless city': (32.8371, -97.0820),
        'Bedford city': (32.8440, -97.1431),
        'Hurst city': (32.8235, -97.1706),
        'Keller city': (32.9346, -97.2514),
        'North Richland Hills city': (32.8343, -97.2289),
        'Mansfield city': (32.5632, -97.1417),
        'Cedar Hill city': (32.5882, -96.9561),
        'DeSoto city': (32.5896, -96.8570),
        'Duncanville city': (32.6518, -96.9083),
        'Lancaster city': (32.5921, -96.7561),
        'Burleson city': (32.5421, -97.3208),
        'Ennis city': (32.3293, -96.6253),
        'Hillsboro city': (32.0107, -97.1281)
    }
    
    # Merge with fallback coordinates
    for city, coords in fallback_coords.items():
        if city not in city_coords:
            city_coords[city] = coords
    
    return city_coords

def get_city_color_by_growth(growth_rate):
    """Get color based on population growth rate"""
    if growth_rate >= 100:
        return '#8b0000'  # Dark red - extreme growth
    elif growth_rate >= 50:
        return '#d73027'  # Red - very high growth
    elif growth_rate >= 25:
        return '#fc8d59'  # Orange - high growth
    elif growth_rate >= 10:
        return '#fee08b'  # Yellow - moderate growth
    elif growth_rate >= 0:
        return '#e0f3f8'  # Light blue - low growth
    else:
        return '#4575b4'  # Blue - population decline

def create_pie_chart_marker(city_data, year):
    """Create a pie chart marker for demographic composition"""
    year_data = city_data[city_data['year'] == year]
    if year_data.empty:
        return None
    
    data = year_data.iloc[0]
    
    # Get demographic percentages
    white_pct = data.get('white_pct', 0) or 0
    black_pct = data.get('black_pct', 0) or 0
    asian_pct = data.get('asian_pct', 0) or 0
    hispanic_pct = data.get('hispanic_pct', 0) or 0
    other_pct = data.get('other_pct', 0) or 0
    
    total_pop = data.get('total_population', 0) or 0
    distance = data.get('distance_from_dallas', 0) or 0
    
    # Create HTML popup
    html = f"""
    <div style="width: 220px; font-family: Arial, sans-serif;">
        <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{data['city']} ({year})</h4>
        <p style="margin: 0 0 5px 0;"><strong>Population:</strong> {total_pop:,}</p>
        {f'<p style="margin: 0 0 10px 0; font-size: 11px; color: #666;">Distance from Dallas: {distance:.1f} miles</p>' if distance > 0 else ''}
        <div style="margin-bottom: 5px;">
            <h5 style="margin: 5px 0; color: #34495e;">Demographics:</h5>
    """
    
    demographics = [
        (white_pct, '#1f77b4', 'White'),
        (black_pct, '#ff7f0e', 'Black'),
        (asian_pct, '#2ca02c', 'Asian'),
        (hispanic_pct, '#d62728', 'Hispanic'),
        (other_pct, '#9467bd', 'Other/Mixed')
    ]
    
    for pct, color, label in demographics:
        if pct > 0:
            html += f"""
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <div style="width: 15px; height: 15px; background-color: {color}; margin-right: 8px; border-radius: 2px;"></div>
                <span style="font-size: 12px;">{label}: {pct:.1f}%</span>
            </div>
            """
    
    html += "</div></div>"
    return html

def create_expanded_interactive_map(df):
    """Create the main interactive map with all cities"""
    print("Creating expanded interactive map...")
    
    # Get city coordinates
    city_coords = get_city_coordinates_from_data(df)
    
    # Calculate growth rates
    df_2009 = df[df['year'] == 2009].set_index('city')
    df_2022 = df[df['year'] == 2022].set_index('city')
    
    growth_rates = {}
    for city in df_2009.index:
        if city in df_2022.index:
            pop_2009 = df_2009.loc[city, 'total_population']
            pop_2022 = df_2022.loc[city, 'total_population']
            if pop_2009 > 0:
                growth_rates[city] = ((pop_2022 - pop_2009) / pop_2009) * 100
    
    # Create base map centered on North Texas
    m = folium.Map(
        location=[33.0, -96.8],  # Centered between Dallas and Denison
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # Add title
    title_html = '''
    <h2 style="position: fixed; 
               top: 10px; left: 50px; width: 450px; height: 60px; 
               background-color: white; border: 2px solid grey; z-index:9999; 
               font-size: 18px; padding: 10px; font-family: Arial;">
    North Texas Demographic Evolution (Dallas-Denison Region)
    </h2>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Create feature groups
    fg_2009 = folium.FeatureGroup(name='2009 Demographics')
    fg_2022 = folium.FeatureGroup(name='2022 Demographics', show=True)
    fg_growth = folium.FeatureGroup(name='Population Growth')
    fg_major_cities = folium.FeatureGroup(name='Major Cities Only')
    
    # Define major cities (population > 50,000 in 2022)
    major_cities = set()
    df_2022_data = df[df['year'] == 2022]
    if not df_2022_data.empty:
        major_cities = set(df_2022_data[df_2022_data['total_population'] > 50000]['city'].tolist())
    
    # Add markers for each city
    cities_processed = set()
    
    for city in df['city'].unique():
        if city in cities_processed or city not in city_coords:
            continue
        
        cities_processed.add(city)
        coords = city_coords[city]
        city_data = df[df['city'] == city]
        
        if city_data.empty:
            continue
        
        # Get growth rate
        growth_rate = growth_rates.get(city, 0)
        
        # Get 2022 population for sizing
        pop_2022_data = city_data[city_data['year'] == 2022]
        pop_2022 = pop_2022_data.iloc[0]['total_population'] if not pop_2022_data.empty else 0
        
        # Determine if this is a major city
        is_major = city in major_cities
        
        # 2009 Demographics
        popup_2009 = create_pie_chart_marker(city_data, 2009)
        if popup_2009:
            icon_color = 'blue' if is_major else 'lightblue'
            pop_2009_str = f"{df_2009.loc[city, 'total_population']:,}" if city in df_2009.index else 'N/A'
            folium.Marker(
                coords,
                popup=folium.Popup(popup_2009, max_width=250),
                tooltip=f"{city} - 2009 (Pop: {pop_2009_str})",
                icon=folium.Icon(color=icon_color, icon='info-sign')
            ).add_to(fg_2009)
        
        # 2022 Demographics
        popup_2022 = create_pie_chart_marker(city_data, 2022)
        if popup_2022:
            icon_color = 'red' if is_major else 'pink'
            folium.Marker(
                coords,
                popup=folium.Popup(popup_2022, max_width=250),
                tooltip=f"{city} - 2022 (Pop: {pop_2022:,})",
                icon=folium.Icon(color=icon_color, icon='info-sign')
            ).add_to(fg_2022)
        
        # Population Growth circles
        color = get_city_color_by_growth(growth_rate)
        radius = max(3, min(30, pop_2022 / 8000))  # Scale circle size
        
        folium.CircleMarker(
            coords,
            radius=radius,
            popup=f"""
            <div style="font-family: Arial;">
                <h4>{city}</h4>
                <p><strong>Growth Rate:</strong> {growth_rate:.1f}%</p>
                <p><strong>2022 Population:</strong> {pop_2022:,}</p>
                <p><strong>Category:</strong> {'Major City' if is_major else 'Smaller City'}</p>
            </div>
            """,
            tooltip=f"{city}: {growth_rate:.1f}% growth",
            color='black',
            weight=1,
            fillColor=color,
            fillOpacity=0.7
        ).add_to(fg_growth)
        
        # Major cities only layer
        if is_major:
            folium.CircleMarker(
                coords,
                radius=radius * 1.2,  # Slightly larger for major cities
                popup=popup_2022,
                tooltip=f"{city} (Major City): {pop_2022:,}",
                color='darkred',
                weight=2,
                fillColor='red',
                fillOpacity=0.8
            ).add_to(fg_major_cities)
    
    # Add feature groups to map
    fg_2022.add_to(m)  # Show 2022 by default
    fg_2009.add_to(m)
    fg_growth.add_to(m)
    fg_major_cities.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add enhanced legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 220px; height: 180px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px; font-family: Arial;">
    <h4 style="margin-top: 0;">Population Growth Legend</h4>
    <div><span style="color: #8b0000;">●</span> 100%+ (Extreme Growth)</div>
    <div><span style="color: #d73027;">●</span> 50-100% (Very High)</div>
    <div><span style="color: #fc8d59;">●</span> 25-50% (High)</div>
    <div><span style="color: #fee08b;">●</span> 10-25% (Moderate)</div>
    <div><span style="color: #e0f3f8;">●</span> 0-10% (Low)</div>
    <div><span style="color: #4575b4;">●</span> Decline</div>
    <hr style="margin: 8px 0;">
    <div style="font-size: 11px;">
        <strong>Circle Size:</strong> Population<br>
        <strong>Coverage:</strong> Dallas-Denison Region
    </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_regional_overview_map(df):
    """Create a regional overview map showing city distribution"""
    print("Creating regional overview map...")
    
    city_coords = get_city_coordinates_from_data(df)
    
    # Create map
    m = folium.Map(
        location=[33.0, -96.8],
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Add title
    title_html = '''
    <h2 style="position: fixed; 
               top: 10px; left: 50px; width: 400px; height: 60px; 
               background-color: white; border: 2px solid grey; z-index:9999; 
               font-size: 18px; padding: 10px; font-family: Arial;">
    North Texas Regional Overview
    </h2>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Get 2022 data for current populations
    df_2022 = df[df['year'] == 2022]
    
    # Create population tiers
    population_tiers = [
        (500000, 'Metropolis', 'darkred', 25),
        (200000, 'Major City', 'red', 20),
        (100000, 'Large City', 'orange', 15),
        (50000, 'Medium City', 'yellow', 12),
        (25000, 'Small City', 'lightgreen', 10),
        (10000, 'Town', 'lightblue', 8),
        (0, 'Small Town', 'gray', 6)
    ]
    
    for _, city_data in df_2022.iterrows():
        city = city_data['city']
        if city not in city_coords:
            continue
        
        coords = city_coords[city]
        pop = city_data['total_population']
        
        # Determine tier
        tier_name = 'Small Town'
        tier_color = 'gray'
        tier_size = 6
        
        for min_pop, name, color, size in population_tiers:
            if pop >= min_pop:
                tier_name = name
                tier_color = color
                tier_size = size
                break
        
        # Add marker
        folium.CircleMarker(
            coords,
            radius=tier_size,
            popup=f"""
            <div style="font-family: Arial;">
                <h4>{city}</h4>
                <p><strong>Population:</strong> {pop:,}</p>
                <p><strong>Category:</strong> {tier_name}</p>
                <p><strong>Distance from Dallas:</strong> {city_data.get('distance_from_dallas', 0):.1f} miles</p>
            </div>
            """,
            tooltip=f"{city}: {pop:,} ({tier_name})",
            color='black',
            weight=1,
            fillColor=tier_color,
            fillOpacity=0.7
        ).add_to(m)
    
    # Add population tier legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 200px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px; font-family: Arial;">
    <h4 style="margin-top: 0;">City Size Categories</h4>
    <div><span style="color: darkred;">●</span> Metropolis (500K+)</div>
    <div><span style="color: red;">●</span> Major City (200K+)</div>
    <div><span style="color: orange;">●</span> Large City (100K+)</div>
    <div><span style="color: yellow;">●</span> Medium City (50K+)</div>
    <div><span style="color: lightgreen;">●</span> Small City (25K+)</div>
    <div><span style="color: lightblue;">●</span> Town (10K+)</div>
    <div><span style="color: gray;">●</span> Small Town (&lt;10K)</div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_expanded_dashboard(df):
    """Create an enhanced HTML dashboard for the expanded dataset"""
    
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
    <title>North Texas Demographic Evolution - Expanded Analysis</title>
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
            backdrop-filter: blur(10px);
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
            backdrop-filter: blur(10px);
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
    </style>
</head>
<body>
    <div class="header">
        <h1>North Texas Demographic Evolution</h1>
        <p>Comprehensive Analysis of the Dallas-Denison Region (2009-2022)</p>
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
    </div>
    
    <div class="map-container">
        <h2>🗺️ Interactive Regional Map</h2>
        <iframe src="north_texas_expanded_map.html"></iframe>
    </div>
    
    <div class="map-container">
        <h2>🏙️ Regional City Overview</h2>
        <iframe src="north_texas_regional_overview.html"></iframe>
    </div>
</body>
</html>
"""
    
    return html_content

def main():
    """Main function to create expanded visualizations"""
    print("🌟 CREATING EXPANDED NORTH TEXAS VISUALIZATIONS")
    print("=" * 60)
    
    try:
        # Load data
        df = load_expanded_data()
        df = calculate_demographic_percentages(df)
        print(f"✓ Loaded data for {df['city'].nunique()} cities across {len(df['year'].unique())} years")
        
        # Create expanded interactive map
        print("\n📍 Creating expanded interactive map...")
        expanded_map = create_expanded_interactive_map(df)
        expanded_map.save('north_texas_expanded_map.html')
        print("✓ Saved: north_texas_expanded_map.html")
        
        # Create regional overview map
        print("\n🗺️ Creating regional overview map...")
        overview_map = create_regional_overview_map(df)
        overview_map.save('north_texas_regional_overview.html')
        print("✓ Saved: north_texas_regional_overview.html")
        
        # Create expanded dashboard
        print("\n📊 Creating expanded dashboard...")
        dashboard_html = create_expanded_dashboard(df)
        with open('north_texas_expanded_dashboard.html', 'w') as f:
            f.write(dashboard_html)
        print("✓ Saved: north_texas_expanded_dashboard.html")
        
        print(f"\n🎉 EXPANDED VISUALIZATIONS COMPLETE!")
        print("Files created:")
        print("  • north_texas_expanded_dashboard.html - Main expanded dashboard")
        print("  • north_texas_expanded_map.html - Interactive regional map")
        print("  • north_texas_regional_overview.html - City size overview")
        print(f"\n🌐 Open 'north_texas_expanded_dashboard.html' to explore!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("💡 Please run the expanded data collection first:")
        print("   python expanded_city_collector.py")
    except Exception as e:
        print(f"❌ Error creating visualizations: {e}")

if __name__ == "__main__":
    main()
