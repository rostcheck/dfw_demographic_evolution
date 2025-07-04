#!/usr/bin/env python3
"""
Simplified Census Data Collector for North Texas Cities
Collects population, race, and ancestry data from US Census API
"""

import requests
import pandas as pd
import time
from typing import List, Dict
import os

class SimpleCensusDataCollector:
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
        
        # Major DFW cities we'll focus on (with their FIPS codes)
        self.major_dfw_cities = {
            'Dallas city, Texas': '19000',
            'Fort Worth city, Texas': '27000',
            'Arlington city, Texas': '04000',
            'Plano city, Texas': '58016',
            'Garland city, Texas': '29000',
            'Irving city, Texas': '37000',
            'Grand Prairie city, Texas': '30644',
            'McKinney city, Texas': '45744',
            'Mesquite city, Texas': '47892',
            'Carrollton city, Texas': '13024',
            'Frisco city, Texas': '27684',
            'Denton city, Texas': '19972',
            'Richardson city, Texas': '61796',
            'Lewisville city, Texas': '42508',
            'Allen city, Texas': '01924',
            'Flower Mound town, Texas': '26232',
            'Euless city, Texas': '24768',
            'Bedford city, Texas': '07132',
            'Grapevine city, Texas': '30692',
            'Wylie city, Texas': '80356',
            'Coppell city, Texas': '16432',
            'The Colony city, Texas': '72530',
            'Southlake city, Texas': '69032',
            'Addison town, Texas': '01000',
            'University Park city, Texas': '74492',
            'Highland Park town, Texas': '33452',
            'Farmers Branch city, Texas': '25452',
            'Duncanville city, Texas': '21892',
            'DeSoto city, Texas': '19792',
            'Cedar Hill city, Texas': '13552',
            'Lancaster city, Texas': '41212',
            'Mansfield city, Texas': '46452',
            'Rowlett city, Texas': '63572',
            'Rockwall city, Texas': '62828'
        }
        
        # Census variables we want to collect (simplified set)
        self.variables = {
            # Total Population
            'B01003_001E': 'total_population',
            
            # Race (key categories)
            'B02001_002E': 'white_alone',
            'B02001_003E': 'black_alone',
            'B02001_005E': 'asian_alone',
            'B02001_008E': 'two_or_more_races',
            
            # Hispanic/Latino
            'B03003_003E': 'hispanic_latino',
            
            # Selected Ancestry (major groups)
            'B04006_039E': 'german',
            'B04006_052E': 'irish',
            'B04006_023E': 'english',
            'B04006_067E': 'mexican',
            'B04006_049E': 'indian',
            'B04006_017E': 'chinese',
            'B04006_102E': 'vietnamese',
            'B04006_025E': 'french',
            'B04006_054E': 'italian',
            'B04006_061E': 'korean'
        }

    def get_demographic_data(self, place_fips: str, year: int) -> Dict:
        """Get demographic data for a specific place"""
        url = f"{self.base_url}/{year}/acs/acs5"
        
        # Get all variables in one API call
        variables_str = ','.join(self.variables.keys())
        
        params = {
            'get': f'NAME,{variables_str}',
            'for': f'place:{place_fips}',
            'in': 'state:48'  # Texas
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
                    value = row[i] if i < len(row) else None
                    result[var_name] = value if value not in ['-999999999', None, ''] else 0
                    
                return result
            return None
            
        except Exception as e:
            print(f"Error getting data for place {place_fips} in {year}: {e}")
            return None

    def collect_all_data(self, start_year: int = 2009, end_year: int = 2022) -> pd.DataFrame:
        """Collect demographic data for major DFW cities across specified years"""
        all_data = []
        
        print("Collecting demographic data for major DFW cities...")
        print(f"Years: {start_year} to {end_year}")
        print(f"Cities: {len(self.major_dfw_cities)}")
        
        total_requests = len(self.major_dfw_cities) * (end_year - start_year + 1)
        current_request = 0
        
        for city_name, place_fips in self.major_dfw_cities.items():
            print(f"\nProcessing {city_name}...")
            
            for year in range(start_year, end_year + 1):
                current_request += 1
                print(f"Progress: {current_request}/{total_requests} - {city_name} ({year})")
                
                data = self.get_demographic_data(place_fips, year)
                if data:
                    data['place_fips'] = place_fips
                    # Determine county based on city
                    data['county'] = self.get_county_for_city(city_name)
                    all_data.append(data)
                
                time.sleep(0.1)  # Rate limiting
        
        return pd.DataFrame(all_data)

    def get_county_for_city(self, city_name: str) -> str:
        """Determine county for a city (simplified mapping)"""
        city_county_map = {
            'Dallas city, Texas': 'Dallas',
            'Fort Worth city, Texas': 'Tarrant',
            'Arlington city, Texas': 'Tarrant',
            'Plano city, Texas': 'Collin',
            'Garland city, Texas': 'Dallas',
            'Irving city, Texas': 'Dallas',
            'Grand Prairie city, Texas': 'Dallas',
            'McKinney city, Texas': 'Collin',
            'Mesquite city, Texas': 'Dallas',
            'Carrollton city, Texas': 'Dallas',
            'Frisco city, Texas': 'Collin',
            'Denton city, Texas': 'Denton',
            'Richardson city, Texas': 'Dallas',
            'Lewisville city, Texas': 'Denton',
            'Allen city, Texas': 'Collin',
            'Flower Mound town, Texas': 'Denton',
            'Euless city, Texas': 'Tarrant',
            'Bedford city, Texas': 'Tarrant',
            'Grapevine city, Texas': 'Tarrant',
            'Wylie city, Texas': 'Collin',
            'Coppell city, Texas': 'Dallas',
            'The Colony city, Texas': 'Denton',
            'Southlake city, Texas': 'Tarrant',
            'Addison town, Texas': 'Dallas',
            'University Park city, Texas': 'Dallas',
            'Highland Park town, Texas': 'Dallas',
            'Farmers Branch city, Texas': 'Dallas',
            'Duncanville city, Texas': 'Dallas',
            'DeSoto city, Texas': 'Dallas',
            'Cedar Hill city, Texas': 'Dallas',
            'Lancaster city, Texas': 'Dallas',
            'Mansfield city, Texas': 'Tarrant',
            'Rowlett city, Texas': 'Dallas',
            'Rockwall city, Texas': 'Rockwall'
        }
        return city_county_map.get(city_name, 'Unknown')

    def save_data(self, df: pd.DataFrame, filename: str = None):
        """Save collected data to CSV"""
        if filename is None:
            filename = f"dfw_major_cities_demographics_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
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
    
    collector = SimpleCensusDataCollector(api_key=api_key)
    
    # Collect data for the last 14 years (ACS 5-year estimates available from 2009)
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
        cols_to_show = ['name', 'county', 'year', 'total_population', 'white_alone', 'hispanic_latino']
        available_cols = [col for col in cols_to_show if col in df.columns]
        print(df[available_cols].head())
        
        # Show population trends for major cities
        print(f"\nPopulation trends for top 5 cities:")
        top_cities = df[df['year'] == 2022].nlargest(5, 'total_population')['name'].tolist()
        for city in top_cities:
            city_data = df[df['name'] == city].sort_values('year')
            if not city_data.empty:
                pop_2009 = city_data[city_data['year'] == 2009]['total_population'].iloc[0] if len(city_data[city_data['year'] == 2009]) > 0 else 'N/A'
                pop_2022 = city_data[city_data['year'] == 2022]['total_population'].iloc[0] if len(city_data[city_data['year'] == 2022]) > 0 else 'N/A'
                print(f"  {city}: {pop_2009} (2009) → {pop_2022} (2022)")
        
    else:
        print("No data collected. Please check your API key and internet connection.")

if __name__ == "__main__":
    main()
