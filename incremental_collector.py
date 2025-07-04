#!/usr/bin/env python3
"""
County-Based Data Collector
- Queries all cities within specified North Texas counties
- Uses counties.json configuration file
- Ensures complete data collection with retry logic
- Prompts for API key if not available
- Saves progress after every city to prevent data loss
"""

import requests
import pandas as pd
import time
import json
import os
import getpass
from typing import List, Dict, Tuple, Set
from pathlib import Path

class CountyBasedDataCollector:
    def __init__(self, api_key: str = None):
        self.base_url = "https://api.census.gov/data"
        self.counties = self.load_counties_config()
        self.coordinates_lookup = self.load_coordinates_lookup()
        self.api_key = self.get_api_key(api_key)
        self.dallas_coords = (32.7767, -96.7970)  # Dallas coordinates for distance calculation
        
    def load_coordinates_lookup(self) -> Dict[int, Dict]:
        """Load place coordinates from the Texas places coordinate file"""
        try:
            import pandas as pd
            coords_df = pd.read_csv('texas_place_coordinates.csv')
            
            # Create lookup dictionary: place_fips -> {lat, lon, coordinates}
            lookup = {}
            for _, row in coords_df.iterrows():
                lookup[int(row['place_fips'])] = {
                    'latitude': row['latitude'],
                    'longitude': row['longitude'], 
                    'coordinates': row['coordinates']
                }
                
            print(f"📍 Loaded coordinates for {len(lookup)} Texas places")
            return lookup
            
        except FileNotFoundError:
            print("⚠️ texas_place_coordinates.csv not found - coordinates will be missing")
            return {}
        except Exception as e:
            print(f"⚠️ Error loading coordinates: {e}")
            return {}
            
    def calculate_distance(self, coord1, coord2):
        """Calculate distance between two coordinates in miles"""
        import math
        
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
        
    def get_api_key(self, provided_key: str = None) -> str:
        """Get API key from environment, parameter, or user prompt"""
        
        # Check environment variable first
        env_key = os.getenv('CENSUS_API_KEY')
        if env_key:
            print(f"🔑 Using Census API key from environment variable")
            return env_key
            
        # Check provided parameter
        if provided_key:
            print(f"🔑 Using provided Census API key")
            return provided_key
            
        # Prompt user for API key
        print("\n📋 Census API Key Setup")
        print("=" * 40)
        print("An API key significantly improves collection speed and reliability:")
        print("  • 5x faster data collection")
        print("  • Reduced timeout errors")
        print("  • Higher success rate")
        print("\nGet a free key at: https://api.census.gov/data/key_signup.html")
        
        while True:
            choice = input("\nDo you have a Census API key? [y/N]: ").lower().strip()
            
            if choice in ['y', 'yes']:
                api_key = getpass.getpass("Enter your Census API key: ").strip()
                if api_key:
                    print("🔑 API key configured - using enhanced collection mode")
                    return api_key
                else:
                    print("❌ No key entered")
                    continue
                    
            elif choice in ['n', 'no', '']:
                print("⚠️ Continuing without API key - collection will be slower with more potential timeouts")
                confirm = input("Continue anyway? [y/N]: ").lower().strip()
                if confirm in ['y', 'yes']:
                    return None
                else:
                    print("Please get an API key and try again.")
                    continue
            else:
                print("Please enter 'y' for yes or 'n' for no")
                
    def load_counties_config(self) -> Dict[str, str]:
        """Load county configuration from JSON file"""
        config_file = Path("counties.json")
        if not config_file.exists():
            raise FileNotFoundError("counties.json configuration file not found")
            
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        counties = config.get('north_texas_counties', {})
        print(f"📍 Loaded {len(counties)} counties from configuration")
        return counties
        
    def get_all_places_in_counties(self) -> List[Dict]:
        """Get all places (cities) in the configured counties using the Texas places file"""
        
        # Load the Texas places file
        places_file = "st48_tx_place2020.txt"
        if not Path(places_file).exists():
            raise FileNotFoundError(f"Texas places file not found: {places_file}")
            
        print(f"📍 Loading Texas places from {places_file}...")
        
        try:
            import pandas as pd
            df = pd.read_csv(places_file, sep='|')
            print(f"   Loaded {len(df)} total places in Texas")
            
        except Exception as e:
            raise Exception(f"Error reading places file: {e}")
            
        # Filter places to only those in our target counties
        target_county_names = [f"{name} County" for name in self.counties.keys()]
        target_places = []
        
        print(f"\n🔍 Filtering places in target counties...")
        for county_name in target_county_names:
            # Find places that have this county in their COUNTIES field
            county_places = df[df['COUNTIES'].str.contains(county_name, na=False)]
            
            for _, place in county_places.iterrows():
                place_name = place['PLACENAME']
                place_fips = place['PLACEFP']
                place_type = place['TYPE']
                counties_list = place['COUNTIES']
                
                # Skip Census Designated Places (CDPs) - focus on incorporated places
                if place_type == 'CENSUS DESIGNATED PLACE':
                    continue
                    
                # Determine primary county (first one listed, or the one we're processing)
                counties = [c.strip() for c in counties_list.split('~~~')]
                primary_county = county_name.replace(' County', '')
                
                # If this place spans multiple counties, we might already have it
                existing = next((p for p in target_places if p['place_fips'] == place_fips), None)
                if existing:
                    # Add this county to the existing entry
                    if primary_county not in existing['counties']:
                        existing['counties'].append(primary_county)
                else:
                    # New place
                    target_places.append({
                        'name': place_name,
                        'place_fips': place_fips,
                        'counties': [primary_county],
                        'all_counties': counties_list,
                        'type': place_type
                    })
                    
        print(f"✅ Found {len(target_places)} unique places in target counties")
        
        # Verify target cities are included
        missing_cities = ['Celina', 'Melissa', 'Sherman']
        found_targets = []
        for city in missing_cities:
            found = [p for p in target_places if city.lower() in p['name'].lower()]
            if found:
                for f in found:
                    counties_str = ', '.join(f['counties'])
                    found_targets.append(f"{f['name']} ({counties_str})")
            
        if found_targets:
            print(f"✅ Verified target cities: {', '.join(found_targets)}")
                
        return target_places
        
    def backfill_missing_data(self, output_file: str = "north_texas_county_demographics.csv"):
        """Add missing coordinates and distance data to existing records"""
        
        if not Path(output_file).exists():
            return  # No existing file to backfill
            
        print(f"🔄 Checking for missing coordinate/distance data...")
        
        try:
            import pandas as pd
            df = pd.read_csv(output_file)
            
            # Check what columns are missing
            required_columns = ['latitude', 'longitude', 'coordinates', 'distance_from_dallas']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if not missing_columns:
                missing_coords = df['coordinates'].isna().sum()
                if missing_coords == 0:
                    print("   ✅ All records have complete coordinate data")
                    return
                    
            print(f"   📍 Adding missing data to {len(df)} records...")
            
            # Add missing columns
            for col in missing_columns:
                if col in ['latitude', 'longitude', 'distance_from_dallas']:
                    df[col] = 0.0
                else:
                    df[col] = None
                    
            # Fill in missing coordinate and distance data
            updated_count = 0
            for idx, row in df.iterrows():
                place_fips_int = int(row['place_fips'])
                
                # Check if this record needs coordinate data
                needs_update = (pd.isna(row.get('coordinates')) or 
                              row.get('coordinates') == '' or
                              pd.isna(row.get('distance_from_dallas')) or
                              row.get('distance_from_dallas') == 0)
                
                if needs_update and place_fips_int in self.coordinates_lookup:
                    coord_data = self.coordinates_lookup[place_fips_int]
                    df.at[idx, 'latitude'] = coord_data['latitude']
                    df.at[idx, 'longitude'] = coord_data['longitude']
                    df.at[idx, 'coordinates'] = coord_data['coordinates']
                    
                    # Calculate distance from Dallas
                    city_coords = (coord_data['latitude'], coord_data['longitude'])
                    distance = self.calculate_distance(self.dallas_coords, city_coords)
                    df.at[idx, 'distance_from_dallas'] = round(distance, 1)
                    
                    updated_count += 1
                elif needs_update:
                    # Default to Dallas coordinates
                    df.at[idx, 'latitude'] = self.dallas_coords[0]
                    df.at[idx, 'longitude'] = self.dallas_coords[1]
                    df.at[idx, 'coordinates'] = f"({self.dallas_coords[0]}, {self.dallas_coords[1]})"
                    df.at[idx, 'distance_from_dallas'] = 0.0
                    
            # Save updated dataset
            df.to_csv(output_file, index=False)
            print(f"   ✅ Updated {updated_count} records with coordinate/distance data")
            
        except Exception as e:
            print(f"   ⚠️ Error backfilling data: {e}")
            
    def get_demographic_data(self, place_fips, year: int, max_retries: int = 3) -> Dict:
        """Get demographic data for a specific place and year with retry logic"""
        
        # Ensure FIPS code is zero-padded to 5 digits (handle both string and int input)
        place_fips_padded = str(place_fips).zfill(5)
        
        # Define the variables we want to collect
        variables = [
            'B01003_001E',  # Total population
            'B02001_002E',  # White alone
            'B02001_003E',  # Black alone
            'B02001_005E',  # Asian alone
            'B02001_008E',  # Two or more races
            'B03003_003E',  # Hispanic or Latino
            'B04006_047E',  # German ancestry
            'B04006_018E',  # Irish ancestry
            'B04006_010E',  # English ancestry
            'B04006_065E',  # Mexican ancestry
            'B04006_001E',  # Total ancestry (for Indian calculation)
            'B02001_006E',  # American Indian and Alaska Native alone
            'B04006_077E',  # Chinese ancestry
            'B04006_024E',  # French ancestry
            'B04006_039E',  # Italian ancestry
            'B04006_079E',  # Korean ancestry
        ]
        
        url = f"{self.base_url}/{year}/acs/acs5"
        params = {
            'get': ','.join(['NAME'] + variables),
            'for': f'place:{place_fips_padded}',
            'in': 'state:48'
        }
        
        if self.api_key:
            params['key'] = self.api_key
            
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                timeout = 30 + (attempt * 10)  # Increase timeout with each retry
                response = requests.get(url, params=params, timeout=timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if len(data) > 1:  # Has data beyond header
                        row = data[1]  # First data row
                        
                        # Map the response to our expected format
                        result = {
                            'name': row[0],
                            'total_population': int(row[1]) if row[1] and row[1] != '-666666666' else 0,
                            'white_alone': int(row[2]) if row[2] and row[2] != '-666666666' else 0,
                            'black_alone': int(row[3]) if row[3] and row[3] != '-666666666' else 0,
                            'asian_alone': int(row[4]) if row[4] and row[4] != '-666666666' else 0,
                            'two_or_more_races': int(row[5]) if row[5] and row[5] != '-666666666' else 0,
                            'hispanic_latino': int(row[6]) if row[6] and row[6] != '-666666666' else 0,
                            'german': int(row[7]) if row[7] and row[7] != '-666666666' else 0,
                            'irish': int(row[8]) if row[8] and row[8] != '-666666666' else 0,
                            'english': int(row[9]) if row[9] and row[9] != '-666666666' else 0,
                            'mexican': int(row[10]) if row[10] and row[10] != '-666666666' else 0,
                            'indian': int(row[12]) if row[12] and row[12] != '-666666666' else 0,
                            'chinese': int(row[13]) if row[13] and row[13] != '-666666666' else 0,
                            'vietnamese': 0,  # Not available in current ACS
                            'french': int(row[14]) if row[14] and row[14] != '-666666666' else 0,
                            'italian': int(row[15]) if row[15] and row[15] != '-666666666' else 0,
                            'korean': int(row[16]) if row[16] and row[16] != '-666666666' else 0,
                            'place_fips': place_fips,  # Store original FIPS for consistency
                            'year': year
                        }
                        
                        return result
                        
                elif response.status_code == 204:
                    # No data available for this place/year combination (legitimate)
                    return None
                else:
                    # API error - retry
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        time.sleep(wait_time)
                        continue
                    else:
                        return None
                        
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    time.sleep(wait_time)
                    continue
                else:
                    return None
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    return None
                    
        return None
            
    def collect_data_for_places(self, places: List[Dict], years: List[int]) -> pd.DataFrame:
        """Collect demographic data for all places across all years with gap tracking"""
        
        output_file = "north_texas_county_demographics.csv"
        
        # Load existing data if available
        existing_data = []
        if Path(output_file).exists():
            existing_df = pd.read_csv(output_file)
            existing_data = existing_df.to_dict('records')
            print(f"📂 Loaded {len(existing_data)} existing records")
            
        # Track what we already have
        existing_keys = set()
        for record in existing_data:
            key = f"{record['place_fips']}_{record['year']}"
            existing_keys.add(key)
            
        all_data = existing_data.copy()
        total_combinations = len(places) * len(years)
        completed = len(existing_data)
        
        print(f"\n🔄 Data Collection Plan:")
        print(f"   • Places: {len(places)}")
        print(f"   • Years: {len(years)} ({min(years)}-{max(years)})")
        print(f"   • Total combinations: {total_combinations}")
        print(f"   • Already completed: {completed}")
        print(f"   • Remaining: {total_combinations - completed}")
        
        # Track failures for reporting
        failed_records = []
        timeout_records = []
        no_data_records = []
        
        for i, place in enumerate(places, 1):
            place_name = place['name']
            place_fips = place['place_fips']
            counties = place['counties']  # List of counties this place is in
            primary_county = counties[0]  # Use first county as primary
            
            print(f"\n[{i}/{len(places)}] 🏙️ {place_name} ({', '.join(counties)} County)")
            
            for year in years:
                key = f"{place_fips}_{year}"
                
                if key in existing_keys:
                    print(f"   {year}: ✓", end="")
                    continue
                    
                print(f"   {year}: ", end="", flush=True)
                
                data = self.get_demographic_data(place_fips, year)
                
                if data:
                    # Add place metadata
                    data['city'] = place_name
                    data['county'] = primary_county
                    data['county_fips'] = self.counties[primary_county]
                    data['all_counties'] = ', '.join(counties)
                    
                    # Add coordinates and distance if available
                    place_fips_int = int(place_fips)
                    if place_fips_int in self.coordinates_lookup:
                        coord_data = self.coordinates_lookup[place_fips_int]
                        data['latitude'] = coord_data['latitude']
                        data['longitude'] = coord_data['longitude']
                        data['coordinates'] = coord_data['coordinates']
                        
                        # Calculate distance from Dallas
                        city_coords = (coord_data['latitude'], coord_data['longitude'])
                        distance = self.calculate_distance(self.dallas_coords, city_coords)
                        data['distance_from_dallas'] = round(distance, 1)
                    else:
                        # Default to Dallas coordinates if not found
                        data['latitude'] = self.dallas_coords[0]
                        data['longitude'] = self.dallas_coords[1]
                        data['coordinates'] = f"({self.dallas_coords[0]}, {self.dallas_coords[1]})"
                        data['distance_from_dallas'] = 0.0
                    
                    all_data.append(data)
                    existing_keys.add(key)
                    completed += 1
                    print("✅", end="")
                    
                    # Save progress after each successful collection
                    df = pd.DataFrame(all_data)
                    df.to_csv(output_file, index=False)
                    
                else:
                    # Determine failure type for reporting
                    failed_records.append((place_name, year))
                    print("❌", end="")
                    
                # Rate limiting
                time.sleep(0.1 if self.api_key else 0.5)
                
            print()  # New line after each city
                
        # Final data quality report
        print(f"\n📊 Data Collection Complete!")
        print(f"   • Total records: {len(all_data)}")
        print(f"   • Success rate: {(len(all_data)/total_combinations)*100:.1f}%")
        
        if failed_records:
            print(f"   • Failed records: {len(failed_records)}")
            print(f"     (These may be legitimately unavailable for small places)")
            
        # Data completeness check
        df = pd.DataFrame(all_data)
        completeness = len(df) / total_combinations
        
        if completeness >= 0.95:
            print(f"✅ Dataset is {completeness*100:.1f}% complete - ready for analysis")
        elif completeness >= 0.90:
            print(f"⚠️ Dataset is {completeness*100:.1f}% complete - usable but some gaps")
        else:
            print(f"❌ Dataset is {completeness*100:.1f}% complete - significant gaps detected")
            
        return df
        
    def run_collection(self, years: List[int] = None):
        """Main collection process"""
        if years is None:
            years = list(range(2009, 2023))  # 2009-2022
            
        print("🌟 COUNTY-BASED DEMOGRAPHIC DATA COLLECTION")
        print("=" * 50)
        
        # Step 1: Backfill any missing coordinate/distance data
        self.backfill_missing_data()
        
        # Step 2: Discover all places in counties
        places = self.get_all_places_in_counties()
        
        if not places:
            print("❌ No places found in configured counties")
            return
            
        # Step 3: Collect demographic data
        df = self.collect_data_for_places(places, years)
        
        print(f"\n🎉 Collection Summary:")
        print(f"   • Places: {df['city'].nunique()}")
        print(f"   • Years: {len(df['year'].unique())}")
        print(f"   • Total records: {len(df)}")
        print(f"   • Counties: {', '.join(sorted(df['county'].unique()))}")
        print(f"   • Output file: north_texas_county_demographics.csv")
        print(f"\n✅ Ready for visualization!")

def main():
    """Main execution function"""
    try:
        collector = CountyBasedDataCollector()
        collector.run_collection()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Collection interrupted by user")
        print("💡 Progress has been saved - you can resume by running the script again")
        
    except Exception as e:
        print(f"\n❌ Error during collection: {e}")
        print("💡 Check your internet connection and configuration files")

if __name__ == "__main__":
    main()
