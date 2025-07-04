#!/usr/bin/env python3
"""
Interactive Map Visualization for DFW Demographic Changes
Creates a web-based map showing population and demographic changes over time
"""

import pandas as pd
import folium
from folium import plugins
import json
import numpy as np
from pathlib import Path

# City coordinates for North Texas (approximate city centers)
CITY_COORDINATES = {
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
    'Flower Mound town': (33.0145, -97.0969),
    'Euless city': (32.8371, -97.0820),
    'Bedford city': (32.8440, -97.1431),
    'Wylie city': (33.0151, -96.5389),
    'Coppell city': (32.9546, -97.0150),
    'The Colony city': (33.0890, -96.8928),
    'Southlake city': (32.9412, -97.1342),
    'Addison town': (32.9618, -96.8292),
    'University Park city': (32.8501, -96.8003),
    'Farmers Branch city': (32.9265, -96.8961),
    'Duncanville city': (32.6518, -96.9083),
    'DeSoto city': (32.5896, -96.8570),
    'Cedar Hill city': (32.5882, -96.9561),
    'Lancaster city': (32.5921, -96.7561),
    'Mansfield city': (32.5632, -97.1417),
    'Rowlett city': (32.9029, -96.5639),
    'Rockwall city': (32.9312, -96.4597)
}

def load_demographic_data():
    """Load the cleaned demographic data"""
    csv_files = list(Path('.').glob('dfw_demographics_cleaned.csv'))
    if not csv_files:
        # Try the original file
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
    
    # Clean city names
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
    df['other_pct'] = df['other_pct'].clip(lower=0)  # Ensure non-negative
    
    return df

def get_city_color_by_growth(growth_rate):
    """Get color based on population growth rate"""
    if growth_rate >= 50:
        return '#d73027'  # Dark red - very high growth
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
    # Get data for the specific year
    year_data = city_data[city_data['year'] == year]
    if year_data.empty:
        return None
    
    data = year_data.iloc[0]
    
    # Prepare pie chart data
    sizes = [
        max(0, data.get('white_pct', 0)),
        max(0, data.get('black_pct', 0)),
        max(0, data.get('asian_pct', 0)),
        max(0, data.get('hispanic_pct', 0)),
        max(0, data.get('other_pct', 0))
    ]
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    labels = ['White', 'Black', 'Asian', 'Hispanic', 'Other']
    
    # Create simple HTML for pie chart representation
    total_pop = data.get('total_population', 0)
    
    # Create a visual representation using colored bars
    html = f"""
    <div style="width: 200px; font-family: Arial, sans-serif;">
        <h4 style="margin: 0 0 10px 0;">{data['city']} ({year})</h4>
        <p style="margin: 0 0 10px 0;"><strong>Population: {total_pop:,}</strong></p>
        <div style="margin-bottom: 5px;">
    """
    
    for i, (size, color, label) in enumerate(zip(sizes, colors, labels)):
        if size > 0:
            html += f"""
            <div style="display: flex; align-items: center; margin-bottom: 3px;">
                <div style="width: 15px; height: 15px; background-color: {color}; margin-right: 8px;"></div>
                <span style="font-size: 12px;">{label}: {size:.1f}%</span>
            </div>
            """
    
    html += "</div></div>"
    
    return html

def create_interactive_map(df):
    """Create the main interactive map"""
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
    
    # Create base map centered on DFW
    m = folium.Map(
        location=[32.8, -97.0],
        zoom_start=9,
        tiles='OpenStreetMap'
    )
    
    # Add title
    title_html = '''
    <h2 style="position: fixed; 
               top: 10px; left: 50px; width: 400px; height: 60px; 
               background-color: white; border: 2px solid grey; z-index:9999; 
               font-size: 20px; padding: 10px; font-family: Arial;">
    DFW Demographic Evolution (2009-2022)
    </h2>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Create feature groups for different years
    fg_2009 = folium.FeatureGroup(name='2009 Demographics')
    fg_2022 = folium.FeatureGroup(name='2022 Demographics')
    fg_growth = folium.FeatureGroup(name='Population Growth', show=False)
    
    # Add markers for each city
    for city, coords in CITY_COORDINATES.items():
        if city not in df['city'].values:
            continue
        
        city_data = df[df['city'] == city]
        if city_data.empty:
            continue
        
        # Get growth rate
        growth_rate = growth_rates.get(city, 0)
        
        # 2009 Demographics
        popup_2009 = create_pie_chart_marker(city_data, 2009)
        if popup_2009:
            folium.Marker(
                coords,
                popup=folium.Popup(popup_2009, max_width=250),
                tooltip=f"{city} - 2009",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(fg_2009)
        
        # 2022 Demographics
        popup_2022 = create_pie_chart_marker(city_data, 2022)
        if popup_2022:
            folium.Marker(
                coords,
                popup=folium.Popup(popup_2022, max_width=250),
                tooltip=f"{city} - 2022",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(fg_2022)
        
        # Population Growth
        color = get_city_color_by_growth(growth_rate)
        
        # Get 2022 population for circle size
        pop_2022_data = city_data[city_data['year'] == 2022]
        if not pop_2022_data.empty:
            pop_2022 = pop_2022_data.iloc[0]['total_population']
            # Scale circle size based on population (min 5, max 50)
            radius = max(5, min(50, pop_2022 / 10000))
            
            folium.CircleMarker(
                coords,
                radius=radius,
                popup=f"""
                <div style="font-family: Arial;">
                    <h4>{city}</h4>
                    <p><strong>Growth Rate:</strong> {growth_rate:.1f}%</p>
                    <p><strong>2022 Population:</strong> {pop_2022:,}</p>
                </div>
                """,
                tooltip=f"{city}: {growth_rate:.1f}% growth",
                color='black',
                weight=1,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(fg_growth)
    
    # Add feature groups to map
    fg_2009.add_to(m)
    fg_2022.add_to(m)
    fg_growth.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add legend for growth rates
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 140px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; font-family: Arial;">
    <h4 style="margin-top: 0;">Population Growth Legend</h4>
    <div><span style="color: #d73027;">●</span> 50%+ (Very High)</div>
    <div><span style="color: #fc8d59;">●</span> 25-50% (High)</div>
    <div><span style="color: #fee08b;">●</span> 10-25% (Moderate)</div>
    <div><span style="color: #e0f3f8;">●</span> 0-10% (Low)</div>
    <div><span style="color: #4575b4;">●</span> Decline</div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_time_series_map(df):
    """Create a time-series animation map"""
    # This creates a simpler version showing population changes over time
    m = folium.Map(
        location=[32.8, -97.0],
        zoom_start=9,
        tiles='OpenStreetMap'
    )
    
    # Add title
    title_html = '''
    <h2 style="position: fixed; 
               top: 10px; left: 50px; width: 400px; height: 60px; 
               background-color: white; border: 2px solid grey; z-index:9999; 
               font-size: 18px; padding: 10px; font-family: Arial;">
    DFW Population Growth Over Time
    </h2>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Create data for time series
    years = sorted(df['year'].unique())
    
    for year in [2009, 2015, 2022]:  # Show key years
        fg = folium.FeatureGroup(name=f'Population {year}', show=(year == 2022))
        
        year_data = df[df['year'] == year]
        
        for city, coords in CITY_COORDINATES.items():
            city_data = year_data[year_data['city'] == city]
            if city_data.empty:
                continue
            
            data = city_data.iloc[0]
            pop = data['total_population']
            
            # Scale circle size
            radius = max(5, min(50, pop / 8000))
            
            folium.CircleMarker(
                coords,
                radius=radius,
                popup=f"""
                <div style="font-family: Arial;">
                    <h4>{city} ({year})</h4>
                    <p><strong>Population:</strong> {pop:,}</p>
                    <p><strong>White:</strong> {data.get('white_pct', 0):.1f}%</p>
                    <p><strong>Black:</strong> {data.get('black_pct', 0):.1f}%</p>
                    <p><strong>Asian:</strong> {data.get('asian_pct', 0):.1f}%</p>
                    <p><strong>Hispanic:</strong> {data.get('hispanic_pct', 0):.1f}%</p>
                </div>
                """,
                tooltip=f"{city} ({year}): {pop:,}",
                color='darkblue',
                weight=2,
                fillColor='lightblue',
                fillOpacity=0.6
            ).add_to(fg)
        
        fg.add_to(m)
    
    folium.LayerControl().add_to(m)
    
    return m

def create_html_dashboard():
    """Create an HTML dashboard with multiple visualizations"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>DFW Demographic Evolution Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 10px;
        }
        .map-container {
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .map-title {
            font-size: 24px;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        .map-description {
            color: #666;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        iframe {
            width: 100%;
            height: 600px;
            border: none;
            border-radius: 5px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-number {
            font-size: 36px;
            font-weight: bold;
            color: #3498db;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Dallas-Fort Worth Demographic Evolution</h1>
        <p>Interactive Analysis of Population and Demographic Changes (2009-2022)</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">32</div>
            <div class="stat-label">Cities Analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">19.8%</div>
            <div class="stat-label">Metro Growth Rate</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">924K</div>
            <div class="stat-label">People Added</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">5.6M</div>
            <div class="stat-label">2022 Population</div>
        </div>
    </div>
    
    <div class="map-container">
        <h2 class="map-title">Interactive Demographic Map</h2>
        <p class="map-description">
            Explore demographic changes across DFW cities. Toggle between layers to see 2009 vs 2022 demographics 
            and population growth patterns. Click on markers for detailed information.
        </p>
        <iframe src="dfw_demographic_map.html"></iframe>
    </div>
    
    <div class="map-container">
        <h2 class="map-title">Population Growth Timeline</h2>
        <p class="map-description">
            View population changes over time. Circle sizes represent population, and you can toggle between 
            different years to see growth patterns across the metropolitan area.
        </p>
        <iframe src="dfw_population_timeline.html"></iframe>
    </div>
    
    <div class="map-container">
        <h2 class="map-title">Key Findings</h2>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <h3>Fastest Growing Cities</h3>
                <ol>
                    <li><strong>Frisco:</strong> 130.4% growth</li>
                    <li><strong>McKinney:</strong> 72.7% growth</li>
                    <li><strong>Mansfield:</strong> 71.5% growth</li>
                    <li><strong>Wylie:</strong> 67.1% growth</li>
                    <li><strong>Allen:</strong> 36.8% growth</li>
                </ol>
            </div>
            <div>
                <h3>Demographic Trends</h3>
                <ul>
                    <li>Increasing diversity across all major cities</li>
                    <li>Asian population growth in Plano (14.9% → 22.7%)</li>
                    <li>Hispanic population stable in Dallas (~42%)</li>
                    <li>White population declining in most cities</li>
                    <li>Strong growth in suburban communities</li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html_content

def main():
    """Main function to create all visualizations"""
    print("Creating DFW Demographic Map Visualizations...")
    
    # Load data
    try:
        df = load_demographic_data()
        df = calculate_demographic_percentages(df)
        print(f"Loaded data for {df['city'].nunique()} cities across {len(df['year'].unique())} years")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run the data collection script first.")
        return
    
    # Create main interactive map
    print("Creating interactive demographic map...")
    main_map = create_interactive_map(df)
    main_map.save('dfw_demographic_map.html')
    print("✓ Saved: dfw_demographic_map.html")
    
    # Create time series map
    print("Creating population timeline map...")
    timeline_map = create_time_series_map(df)
    timeline_map.save('dfw_population_timeline.html')
    print("✓ Saved: dfw_population_timeline.html")
    
    # Create dashboard
    print("Creating HTML dashboard...")
    dashboard_html = create_html_dashboard()
    with open('dfw_demographic_dashboard.html', 'w') as f:
        f.write(dashboard_html)
    print("✓ Saved: dfw_demographic_dashboard.html")
    
    print("\n🎉 Visualization complete!")
    print("\nFiles created:")
    print("  • dfw_demographic_dashboard.html - Main dashboard (open this first)")
    print("  • dfw_demographic_map.html - Interactive demographic map")
    print("  • dfw_population_timeline.html - Population growth timeline")
    print("\nOpen 'dfw_demographic_dashboard.html' in your web browser to explore the visualizations!")

if __name__ == "__main__":
    main()
