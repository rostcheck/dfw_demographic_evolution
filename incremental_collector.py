#!/usr/bin/env python3
"""
County-Based Data Collector
- Queries all cities within specified North Texas counties
- Uses counties.json configuration file
- Saves progress after every city to prevent data loss
- Checks for existing data before making API calls
"""

import requests
import pandas as pd
import time
import json
import os
from typing import List, Dict, Tuple, Set
from pathlib import Path

class CountyBasedDataCollector:
    def __init__(self, api_key: str = None):
        # Check for API key in environment variable first
        self.api_key = os.getenv('CENSUS_API_KEY') or api_key
        if self.api_key:
            print(f"🔑 Using Census API key (from {'environment' if os.getenv('CENSUS_API_KEY') else 'parameter'})")
        else:
            print("⚠️ No API key found - using slower rate limits")
            
        self.base_url = "https://api.census.gov/data"
        self.counties = self.load_counties_config()
        
    def load_counties_config(self) -> Dict[str, str]:
        """Load county configuration from JSON file"""
        config_file = Path("counties.json")
        if not config_file.exists():
            raise FileNotFoundError("counties.json configuration file not found")
            
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        counties = config.get('north_texas_counties', {})
        print(f"📍 Loaded {len(counties)} counties from configuration")
        for name, fips in counties.items():
            print(f"   • {name} County (FIPS: {fips})")
            
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
            print(f"   Checking {county_name}...")
            
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
                    
            print(f"      Found {len(county_places)} places in {county_name}")
            
        print(f"\n✅ Total unique places in target counties: {len(target_places)}")
        
        # Show some examples
        print(f"\nSample places found:")
        for place in sorted(target_places, key=lambda x: x['name'])[:10]:
            counties_str = ', '.join(place['counties'])
            print(f"   • {place['name']} (FIPS: {place['place_fips']}) - {counties_str}")
            
        # Check for our specific missing cities
        missing_cities = ['Celina', 'Melissa', 'Sherman']
        print(f"\nChecking for previously missing cities:")
        for city in missing_cities:
            found = [p for p in target_places if city.lower() in p['name'].lower()]
            if found:
                for f in found:
                    counties_str = ', '.join(f['counties'])
                    print(f"   ✅ {f['name']} (FIPS: {f['place_fips']}) in {counties_str}")
            else:
                print(f"   ❌ {city} not found")
                
        return target_places
        
    def get_demographic_data(self, place_fips, year: int) -> Dict:
        """Get demographic data for a specific place and year"""
        
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
            
        try:
            response = requests.get(url, params=params, timeout=30)
            
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
                # No data available for this place/year combination
                print(f"(no data available)")
                return None
            else:
                print(f"(API error: {response.status_code})")
                return None
                    
        except Exception as e:
            print(f"(exception: {e})")
            return None
            
    def collect_data_for_places(self, places: List[Dict], years: List[int]) -> pd.DataFrame:
        """Collect demographic data for all places across all years"""
        
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
        
        print(f"\n🔄 Collecting data for {len(places)} places across {len(years)} years")
        print(f"📊 Total combinations: {total_combinations}")
        print(f"✅ Already completed: {completed}")
        print(f"🎯 Remaining: {total_combinations - completed}")
        
        for i, place in enumerate(places, 1):
            place_name = place['name']
            place_fips = place['place_fips']
            counties = place['counties']  # List of counties this place is in
            primary_county = counties[0]  # Use first county as primary
            
            print(f"\n[{i}/{len(places)}] 🏙️ {place_name} ({', '.join(counties)} County)")
            
            for year in years:
                key = f"{place_fips}_{year}"
                
                if key in existing_keys:
                    print(f"   {year}: ✓ (already collected)")
                    continue
                    
                print(f"   {year}: Collecting...", end=" ")
                
                data = self.get_demographic_data(place_fips, year)
                
                if data:
                    # Add place metadata
                    data['city'] = place_name
                    data['county'] = primary_county
                    data['county_fips'] = self.counties[primary_county]
                    data['all_counties'] = ', '.join(counties)
                    
                    all_data.append(data)
                    existing_keys.add(key)
                    completed += 1
                    print("✅")
                    
                    # Save progress after each successful collection
                    df = pd.DataFrame(all_data)
                    df.to_csv(output_file, index=False)
                    
                else:
                    print("❌")
                    
                # Rate limiting
                time.sleep(0.2 if self.api_key else 1.0)
                
        print(f"\n🎉 Data collection complete!")
        print(f"📊 Total records collected: {len(all_data)}")
        print(f"💾 Saved to: {output_file}")
        
        return pd.DataFrame(all_data)
        
    def run_collection(self, years: List[int] = None):
        """Main collection process"""
        if years is None:
            years = list(range(2009, 2023))  # 2009-2022
            
        print("🌟 COUNTY-BASED DEMOGRAPHIC DATA COLLECTION")
        print("=" * 50)
        
        # Step 1: Discover all places in counties
        places = self.get_all_places_in_counties()
        
        if not places:
            print("❌ No places found in configured counties")
            return
            
        # Step 2: Collect demographic data
        df = self.collect_data_for_places(places, years)
        
        print(f"\n📈 Collection Summary:")
        print(f"   • Places: {df['city'].nunique()}")
        print(f"   • Years: {len(df['year'].unique())}")
        print(f"   • Total records: {len(df)}")
        print(f"   • Counties: {', '.join(sorted(df['county'].unique()))}")

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
        print("💡 Check your internet connection and API key")

if __name__ == "__main__":
    main()
