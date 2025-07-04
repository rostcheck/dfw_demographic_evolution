#!/usr/bin/env python3
"""
Clean City Data Script
Removes cities that are not actually in the DFW region and fixes data mismatches
"""

import pandas as pd
import math

def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates in miles"""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in miles
    r = 3956
    return c * r

def clean_dataset():
    """Clean the dataset by removing cities that are clearly not in DFW region"""
    
    # Load the dataset
    df = pd.read_csv('north_texas_expanded_demographics_incremental.csv')
    print(f"Original dataset: {len(df)} records, {df['city'].nunique()} cities")
    
    # Dallas coordinates for distance calculation
    dallas_coords = (32.7767, -96.7970)
    
    # Cities that are clearly NOT in the DFW region (too far or wrong location)
    cities_to_remove = [
        'Abilene city',      # West Texas, ~180 miles from Dallas
        'College Station city', # Southeast Texas, ~100 miles from Dallas  
        'Conroe city',       # North of Houston, ~200 miles from Dallas
        'Del Rio city',      # Southwest Texas, ~300 miles from Dallas
        'Eagle Pass city',   # Southwest Texas, ~300 miles from Dallas
        'Galveston city',    # Gulf Coast, ~300 miles from Dallas
        'Huntsville city',   # East Texas, ~150 miles from Dallas
        'Sealy city'         # Southeast Texas, ~200 miles from Dallas
    ]
    
    print(f"\nRemoving cities that are not in DFW region:")
    for city in cities_to_remove:
        city_data = df[df['city'] == city]
        if not city_data.empty:
            print(f"  • {city}: {len(city_data)} records")
    
    # Filter out the non-DFW cities
    df_clean = df[~df['city'].isin(cities_to_remove)]
    
    print(f"\nCleaned dataset: {len(df_clean)} records, {df_clean['city'].nunique()} cities")
    
    # Show remaining cities
    print(f"\nRemaining cities:")
    cities = sorted(df_clean['city'].unique())
    for i, city in enumerate(cities, 1):
        print(f"  {i:2d}. {city}")
    
    # Save cleaned dataset
    output_file = 'north_texas_demographics_cleaned_fixed.csv'
    df_clean.to_csv(output_file, index=False)
    print(f"\nCleaned dataset saved to: {output_file}")
    
    return df_clean

def verify_distances(df):
    """Verify that remaining cities are within reasonable distance of Dallas"""
    dallas_coords = (32.7767, -96.7970)
    
    print(f"\nDistance verification:")
    cities_with_issues = []
    
    for city in df['city'].unique():
        city_data = df[df['city'] == city]
        if not city_data.empty:
            sample = city_data.iloc[0]
            try:
                # Parse coordinates
                coords_str = sample['coordinates']
                if isinstance(coords_str, str):
                    coords = eval(coords_str)
                    distance = calculate_distance(dallas_coords, coords)
                    
                    if distance > 100:  # More than 100 miles from Dallas
                        cities_with_issues.append((city, distance))
                        print(f"  ⚠️  {city}: {distance:.1f} miles (may be too far)")
                    elif distance > 80:
                        print(f"  🟡 {city}: {distance:.1f} miles (borderline)")
                    else:
                        print(f"  ✅ {city}: {distance:.1f} miles")
            except:
                print(f"  ❌ {city}: Could not parse coordinates")
    
    if cities_with_issues:
        print(f"\nCities that may need review:")
        for city, distance in cities_with_issues:
            print(f"  • {city}: {distance:.1f} miles from Dallas")

if __name__ == "__main__":
    print("🧹 CLEANING DFW DEMOGRAPHIC DATA")
    print("=" * 40)
    
    df_clean = clean_dataset()
    verify_distances(df_clean)
    
    print(f"\n✅ Data cleaning complete!")
    print(f"💡 Use 'north_texas_demographics_cleaned_fixed.csv' for accurate visualizations")
