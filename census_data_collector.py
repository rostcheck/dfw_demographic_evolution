#!/usr/bin/env python3
"""
Census Data Collector for North Texas Cities
Collects population, race, and ancestry data from US Census API
"""

import requests
import pandas as pd
import time
from typing import List, Dict
import os

class CensusDataCollector:
    def __init__(self, api_key: str = None):
        """
        Initialize the Census Data Collector
        
        Args:
            api_key: Census API key (optional but recommended for higher rate limits)
                    Get one free at: https://api.census.gov/data/key_signup.html
        """
        self.api_key = api_key
        self.base_url = "https://api.census.gov/data"
        
        # North Texas counties (FIPS codes)
        self.north_texas_counties = {
            'Dallas': '113',
            'Tarrant': '439', 
            'Collin': '085',
            'Denton': '121',
            'Rockwall': '397',
            'Ellis': '139',
            'Johnson': '251',
            'Kaufman': '257',
            'Parker': '367',
            'Wise': '497'
        }
        
        # Census variables we want to collect
        self.variables = {
            # Total Population
            'B01003_001E': 'total_population',
            
            # Race (detailed)
            'B02001_001E': 'total_race_population',
            'B02001_002E': 'white_alone',
            'B02001_003E': 'black_alone',
            'B02001_004E': 'american_indian_alaska_native',
            'B02001_005E': 'asian_alone',
            'B02001_006E': 'native_hawaiian_pacific_islander',
            'B02001_007E': 'other_race',
            'B02001_008E': 'two_or_more_races',
            
            # Hispanic/Latino
            'B03003_001E': 'total_hispanic_population',
            'B03003_002E': 'not_hispanic_latino',
            'B03003_003E': 'hispanic_latino',
            
            # Selected Ancestry (top groups in Texas)
            'B04006_001E': 'total_ancestry_population',
            'B04006_002E': 'afghan',
            'B04006_005E': 'arab',
            'B04006_009E': 'armenian',
            'B04006_017E': 'chinese',
            'B04006_023E': 'english',
            'B04006_024E': 'european',
            'B04006_025E': 'french',
            'B04006_039E': 'german',
            'B04006_049E': 'indian',
            'B04006_052E': 'irish',
            'B04006_054E': 'italian',
            'B04006_061E': 'korean',
            'B04006_067E': 'mexican',
            'B04006_074E': 'norwegian',
            'B04006_082E': 'polish',
            'B04006_087E': 'russian',
            'B04006_088E': 'scandinavian',
            'B04006_089E': 'scotch_irish',
            'B04006_090E': 'scottish',
            'B04006_097E': 'swedish',
            'B04006_102E': 'vietnamese'
        }

    def get_places_in_county(self, county_fips: str, year: int = 2022) -> List[Dict]:
        """Get all places (cities) in a specific county"""
        url = f"{self.base_url}/{year}/acs/acs5"
        
        params = {
            'get': 'NAME',
            'for': 'place:*',
            'in': f'state:48,county:{county_fips}'  # Fixed format: state:48,county:XXX
        }
        
        if self.api_key:
            params['key'] = self.api_key
            
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            places = []
            for row in data[1:]:  # Skip header row
                places.append({
                    'name': row[0],
                    'state': row[1],
                    'county': row[2],
                    'place': row[3]
                })
            return places
            
        except Exception as e:
            print(f"Error getting places for county {county_fips}: {e}")
            return []

    def get_demographic_data(self, place_fips: str, county_fips: str, year: int) -> Dict:
        """Get demographic data for a specific place"""
        url = f"{self.base_url}/{year}/acs/acs5"
        
        # Get all variables in one API call
        variables_str = ','.join(self.variables.keys())
        
        params = {
            'get': f'NAME,{variables_str}',
            'for': f'place:{place_fips}',
            'in': f'state:48,county:{county_fips}'  # Fixed format
        }
        
        if self.api_key:
            params['key'] = self.api_key
            
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if len(data) > 1:
                row = data[1]  # First data row (skip header)
                result = {'name': row[0], 'year': year}
                
                # Map census variables to readable names
                for i, var_code in enumerate(self.variables.keys(), 1):
                    var_name = self.variables[var_code]
                    result[var_name] = row[i] if row[i] != '-999999999' else None
                    
                return result
            return None
            
        except Exception as e:
            print(f"Error getting data for place {place_fips}: {e}")
            return None

    def collect_all_data(self, start_year: int = 2005, end_year: int = 2022) -> pd.DataFrame:
        """Collect demographic data for all North Texas cities across specified years"""
        all_data = []
        
        print("Collecting demographic data for North Texas cities...")
        print(f"Years: {start_year} to {end_year}")
        
        # Get all places in North Texas counties
        all_places = {}
        for county_name, county_fips in self.north_texas_counties.items():
            print(f"Getting places in {county_name} County...")
            places = self.get_places_in_county(county_fips)
            all_places[county_name] = places
            print(f"Found {len(places)} places in {county_name} County")
            time.sleep(0.1)  # Rate limiting
        
        # Collect data for each place and year
        total_requests = sum(len(places) for places in all_places.values()) * (end_year - start_year + 1)
        current_request = 0
        
        for county_name, places in all_places.items():
            county_fips = self.north_texas_counties[county_name]
            
            for place in places:
                place_name = place['name']
                place_fips = place['place']
                
                for year in range(start_year, end_year + 1):
                    current_request += 1
                    print(f"Progress: {current_request}/{total_requests} - {place_name} ({year})")
                    
                    # Skip years before ACS 5-year estimates were available
                    if year < 2009:
                        continue
                        
                    data = self.get_demographic_data(place_fips, county_fips, year)
                    if data:
                        data['county'] = county_name
                        data['place_fips'] = place_fips
                        data['county_fips'] = county_fips
                        all_data.append(data)
                    
                    time.sleep(0.1)  # Rate limiting
        
        return pd.DataFrame(all_data)

    def save_data(self, df: pd.DataFrame, filename: str = None):
        """Save collected data to CSV"""
        if filename is None:
            filename = f"north_texas_demographics_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Save in the current directory (dfw_demographic_evolution)
        filepath = os.path.join(os.getcwd(), filename)
        df.to_csv(filepath, index=False)
        print(f"Data saved to: {filepath}")
        return filepath

def main():
    """Main execution function"""
    # Initialize collector
    # Get a free API key at: https://api.census.gov/data/key_signup.html
    api_key = input("Enter your Census API key (or press Enter to skip): ").strip()
    if not api_key:
        api_key = None
        print("Using without API key (lower rate limits)")
    
    collector = CensusDataCollector(api_key=api_key)
    
    # Collect data for the last 20 years (ACS 5-year estimates available from 2009)
    print("Starting data collection...")
    df = collector.collect_all_data(start_year=2009, end_year=2022)
    
    if not df.empty:
        # Save to CSV
        filepath = collector.save_data(df)
        
        # Display summary
        print(f"\nData collection complete!")
        print(f"Total records: {len(df)}")
        print(f"Cities covered: {df['name'].nunique()}")
        print(f"Years covered: {sorted(df['year'].unique())}")
        print(f"Counties covered: {sorted(df['county'].unique())}")
        
        # Show sample data
        print(f"\nSample data (first 5 rows):")
        print(df[['name', 'county', 'year', 'total_population', 'white_alone', 'hispanic_latino']].head())
        
    else:
        print("No data collected. Please check your API key and internet connection.")

if __name__ == "__main__":
    main()
