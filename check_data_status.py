#!/usr/bin/env python3
"""
Check Data Status Script
Shows what data has already been collected and what's missing
"""

import pandas as pd
from pathlib import Path
import numpy as np

def check_existing_data():
    """Check what data already exists"""
    print("🔍 CHECKING EXISTING DATA STATUS")
    print("=" * 50)
    
    # Look for expanded data files
    expanded_files = list(Path('.').glob('north_texas_expanded_demographics_*.csv'))
    
    if not expanded_files:
        print("❌ No expanded data files found")
        print("💡 Run: python expanded_city_collector_resume.py")
        return
    
    # Load the most recent file
    latest_file = max(expanded_files, key=lambda x: x.stat().st_mtime)
    print(f"📂 Found data file: {latest_file}")
    
    try:
        df = pd.read_csv(latest_file)
        print(f"✅ Loaded {len(df):,} records")
        
        # Basic statistics
        cities = df['city'].nunique() if 'city' in df.columns else df['name'].str.replace(', Texas', '').nunique()
        years = sorted(df['year'].unique())
        
        print(f"\n📊 DATA OVERVIEW:")
        print(f"  • Cities: {cities}")
        print(f"  • Years: {years[0]}-{years[-1]} ({len(years)} years)")
        print(f"  • Total records: {len(df):,}")
        
        # Check completeness
        expected_records_per_city = len(years)
        city_col = 'city' if 'city' in df.columns else df['name'].str.replace(', Texas', '')
        
        print(f"\n🎯 COMPLETENESS CHECK:")
        city_counts = df.groupby(city_col)['year'].count()
        
        complete_cities = city_counts[city_counts == expected_records_per_city]
        incomplete_cities = city_counts[city_counts < expected_records_per_city]
        
        print(f"  • Complete cities: {len(complete_cities)} (all {expected_records_per_city} years)")
        print(f"  • Incomplete cities: {len(incomplete_cities)}")
        
        if len(incomplete_cities) > 0:
            print(f"\n⚠️ INCOMPLETE CITIES:")
            for city, count in incomplete_cities.head(10).items():
                missing = expected_records_per_city - count
                print(f"  • {city:<25} {count:>2}/{expected_records_per_city} years ({missing} missing)")
            
            if len(incomplete_cities) > 10:
                print(f"  • ... and {len(incomplete_cities) - 10} more")
        
        # Show progress by city size
        if 'total_population' in df.columns:
            print(f"\n🏙️ LARGEST CITIES STATUS:")
            latest_year = max(years)
            latest_data = df[df['year'] == latest_year]
            
            if not latest_data.empty:
                top_cities = latest_data.nlargest(10, 'total_population')
                for i, (_, row) in enumerate(top_cities.iterrows(), 1):
                    city_name = row['city'] if 'city' in row else row['name'].replace(', Texas', '')
                    city_records = len(df[city_col == city_name])
                    status = "✅" if city_records == expected_records_per_city else f"⚠️ {city_records}/{expected_records_per_city}"
                    print(f"  {i:2d}. {city_name:<25} {row['total_population']:>8,} {status}")
        
        # Show last processed city (approximate)
        if len(incomplete_cities) > 0:
            # Find the city with the most recent partial data
            last_city = incomplete_cities.index[-1]  # Last incomplete city alphabetically
            print(f"\n🔄 RESUME POINT:")
            print(f"  • Last incomplete city: {last_city}")
            print(f"  • Records for this city: {incomplete_cities[last_city]}/{expected_records_per_city}")
            print(f"  • Missing years: {expected_records_per_city - incomplete_cities[last_city]}")
        
        print(f"\n💡 NEXT STEPS:")
        if len(incomplete_cities) > 0:
            print(f"  • Run: python expanded_city_collector_resume.py")
            print(f"  • This will resume from where it left off")
            print(f"  • Only missing data will be collected")
        else:
            print(f"  • Data collection is complete!")
            print(f"  • Run: python create_expanded_map_visualization.py")
        
    except Exception as e:
        print(f"❌ Error reading data file: {e}")

def show_file_info():
    """Show information about all data files"""
    print(f"\n📁 ALL DATA FILES:")
    print("-" * 30)
    
    # Check for all types of data files
    file_patterns = [
        'north_texas_expanded_demographics_*.csv',
        'dfw_major_cities_demographics_*.csv',
        'dfw_demographics_cleaned.csv'
    ]
    
    for pattern in file_patterns:
        files = list(Path('.').glob(pattern))
        if files:
            for file in sorted(files):
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  • {file.name:<40} {size_mb:>6.1f} MB")

if __name__ == "__main__":
    check_existing_data()
    show_file_info()
