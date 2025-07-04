#!/usr/bin/env python3
"""
Enhanced Incremental Data Collector
- Uses CENSUS_API_KEY environment variable
- Saves progress after every city to prevent data loss
- Checks for existing data before making API calls
"""

import requests
import pandas as pd
import time
import math
import os
from typing import List, Dict, Tuple, Set
from pathlib import Path

class IncrementalDataCollector:
    def __init__(self, api_key: str = None):
        # Check for API key in environment variable first
        self.api_key = os.getenv('CENSUS_API_KEY') or api_key
        if self.api_key:
            print(f"🔑 Using Census API key (from {'environment' if os.getenv('CENSUS_API_KEY') else 'parameter'})")
        else:
            print("⚠️ No API key found - using slower rate limits")
            
        self.base_url = "https://api.census.gov/data"
        self.dallas_coords = (32.7767, -96.7970)
        self.denison_coords = (33.7557, -96.5367)
        self.radius_miles = self.calculate_distance(self.dallas_coords, self.denison_coords)
        
        # Output file for incremental saves
        self.output_file = "north_texas_expanded_demographics_incremental.csv"
        
        # Census variables
        self.variables = {
            'B01003_001E': 'total_population',
            'B02001_002E': 'white_alone',
            'B02001_003E': 'black_alone',
            'B02001_005E': 'asian_alone',
            'B02001_008E': 'two_or_more_races',
            'B03003_003E': 'hispanic_latino',
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

    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
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

    def load_existing_data(self) -> Tuple[List[Dict], Set[Tuple[str, int]]]:
        """Load existing data and return both the data list and set of (city, year) combinations"""
        existing_data = []
        existing_combinations = set()
        
        if Path(self.output_file).exists():
            try:
                df = pd.read_csv(self.output_file)
                existing_data = df.to_dict('records')
                print(f"📂 Found existing incremental file with {len(df)} records")
                
                city_col = 'city' if 'city' in df.columns else 'name'
                
                for _, row in df.iterrows():
                    city = row[city_col].replace(', Texas', '') if ', Texas' in str(row[city_col]) else str(row[city_col])
                    year = int(row['year'])
                    existing_combinations.add((city, year))
                
                cities_count = len(set(combo[0] for combo in existing_combinations))
                years_count = len(set(combo[1] for combo in existing_combinations))
                print(f"📊 Existing data covers {cities_count} cities across {years_count} years")
                
                # Show which cities are complete
                years_expected = list(range(2009, 2023))  # 2009-2022
                city_year_counts = {}
                for city, year in existing_combinations:
                    city_year_counts[city] = city_year_counts.get(city, 0) + 1
                
                complete_cities = [city for city, count in city_year_counts.items() if count == len(years_expected)]
                incomplete_cities = [city for city, count in city_year_counts.items() if count < len(years_expected)]
                
                if complete_cities:
                    print(f"✅ Complete cities ({len(complete_cities)}): {', '.join(complete_cities[:5])}")
                    if len(complete_cities) > 5:
                        print(f"    ... and {len(complete_cities) - 5} more")
                
                if incomplete_cities:
                    print(f"⚠️ Incomplete cities ({len(incomplete_cities)}): {', '.join(incomplete_cities[:5])}")
                    if len(incomplete_cities) > 5:
                        print(f"    ... and {len(incomplete_cities) - 5} more")
                
                return existing_data, existing_combinations
                
            except Exception as e:
                print(f"⚠️ Error loading existing file: {e}")
                return [], set()
        else:
            print("📝 No existing incremental file found - starting fresh")
            return [], set()

    def get_target_cities(self) -> List[Dict]:
        """Get list of target cities in the region"""
        # Expanded list of cities in the Dallas-Denison radius with their info
        target_cities = [
            # Major cities (100K+)
            {'name': 'Dallas city, Texas', 'place_fips': '19000', 'population': 1300000, 'coords': (32.7767, -96.7970)},
            {'name': 'Fort Worth city, Texas', 'place_fips': '27000', 'population': 925000, 'coords': (32.7555, -97.3308)},
            {'name': 'Arlington city, Texas', 'place_fips': '04000', 'population': 394000, 'coords': (32.7357, -97.1081)},
            {'name': 'Plano city, Texas', 'place_fips': '58016', 'population': 285000, 'coords': (33.0198, -96.6989)},
            {'name': 'Irving city, Texas', 'place_fips': '37000', 'population': 255000, 'coords': (32.8140, -96.9489)},
            {'name': 'Garland city, Texas', 'place_fips': '29000', 'population': 244000, 'coords': (32.9126, -96.6389)},
            {'name': 'Grand Prairie city, Texas', 'place_fips': '30644', 'population': 196000, 'coords': (32.7459, -96.9978)},
            {'name': 'Frisco city, Texas', 'place_fips': '27684', 'population': 202000, 'coords': (33.1507, -96.8236)},
            {'name': 'McKinney city, Texas', 'place_fips': '45744', 'population': 196000, 'coords': (33.1972, -96.6153)},
            {'name': 'Mesquite city, Texas', 'place_fips': '47892', 'population': 149000, 'coords': (32.7668, -96.5992)},
            {'name': 'Denton city, Texas', 'place_fips': '19972', 'population': 142000, 'coords': (33.2148, -97.1331)},
            {'name': 'Carrollton city, Texas', 'place_fips': '13024', 'population': 133000, 'coords': (32.9537, -96.8903)},
            {'name': 'Richardson city, Texas', 'place_fips': '61796', 'population': 120000, 'coords': (32.9483, -96.7299)},
            {'name': 'Lewisville city, Texas', 'place_fips': '42508', 'population': 111000, 'coords': (33.0462, -96.9942)},
            {'name': 'Allen city, Texas', 'place_fips': '01924', 'population': 105000, 'coords': (33.1031, -96.6706)},
            
            # Large cities (50K-100K)
            {'name': 'Flower Mound town, Texas', 'place_fips': '26232', 'population': 78000, 'coords': (33.0145, -97.0969)},
            {'name': 'Mansfield city, Texas', 'place_fips': '46452', 'population': 73000, 'coords': (32.5632, -97.1417)},
            {'name': 'North Richland Hills city, Texas', 'place_fips': '52356', 'population': 70000, 'coords': (32.8343, -97.2289)},
            {'name': 'Rowlett city, Texas', 'place_fips': '63572', 'population': 66000, 'coords': (32.9029, -96.5639)},
            {'name': 'Euless city, Texas', 'place_fips': '24768', 'population': 60000, 'coords': (32.8371, -97.0820)},
            {'name': 'Wylie city, Texas', 'place_fips': '80356', 'population': 57000, 'coords': (33.0151, -96.5389)},
            {'name': 'Grapevine city, Texas', 'place_fips': '30692', 'population': 54000, 'coords': (32.9343, -97.0781)},
            {'name': 'DeSoto city, Texas', 'place_fips': '19792', 'population': 54000, 'coords': (32.5896, -96.8570)},
            {'name': 'Burleson city, Texas', 'place_fips': '11428', 'population': 49000, 'coords': (32.5421, -97.3208)},
            {'name': 'Bedford city, Texas', 'place_fips': '07132', 'population': 49000, 'coords': (32.8440, -97.1431)},
            {'name': 'Keller city, Texas', 'place_fips': '38128', 'population': 48000, 'coords': (32.9346, -97.2514)},
            {'name': 'Cedar Hill city, Texas', 'place_fips': '13552', 'population': 48000, 'coords': (32.5882, -96.9561)},
            {'name': 'Rockwall city, Texas', 'place_fips': '62828', 'population': 47000, 'coords': (32.9312, -96.4597)},
            
            # Medium cities (25K-50K)
            {'name': 'The Colony city, Texas', 'place_fips': '72530', 'population': 45000, 'coords': (33.0890, -96.8928)},
            {'name': 'Sherman city, Texas', 'place_fips': '66464', 'population': 43000, 'coords': (33.6356, -96.6089)},
            {'name': 'Waxahachie city, Texas', 'place_fips': '76816', 'population': 41000, 'coords': (32.3865, -96.8489)},
            {'name': 'Lancaster city, Texas', 'place_fips': '41212', 'population': 41000, 'coords': (32.5921, -96.7561)},
            {'name': 'Hurst city, Texas', 'place_fips': '35528', 'population': 40000, 'coords': (32.8235, -97.1706)},
            {'name': 'Duncanville city, Texas', 'place_fips': '21892', 'population': 40000, 'coords': (32.6518, -96.9083)},
            {'name': 'Addison town, Texas', 'place_fips': '01000', 'population': 16000, 'coords': (32.9618, -96.8292)},
            {'name': 'University Park city, Texas', 'place_fips': '74492', 'population': 25000, 'coords': (32.8501, -96.8003)},
            {'name': 'Farmers Branch city, Texas', 'place_fips': '25452', 'population': 36000, 'coords': (32.9265, -96.8961)},
            {'name': 'Coppell city, Texas', 'place_fips': '16432', 'population': 42000, 'coords': (32.9546, -97.0150)},
            {'name': 'Southlake city, Texas', 'place_fips': '69032', 'population': 31000, 'coords': (32.9412, -97.1342)},
            {'name': 'Cleburne city, Texas', 'place_fips': '15364', 'population': 31000, 'coords': (32.3476, -97.3867)},
            {'name': 'Weatherford city, Texas', 'place_fips': '76864', 'population': 31000, 'coords': (32.7593, -97.7975)},
            {'name': 'Greenville city, Texas', 'place_fips': '30692', 'population': 28000, 'coords': (33.1384, -96.1106)},
            {'name': 'Denison city, Texas', 'place_fips': '19792', 'population': 25000, 'coords': (33.7557, -96.5367)},
            {'name': 'Corsicana city, Texas', 'place_fips': '16432', 'population': 25000, 'coords': (32.0954, -96.4689)},
            
            # Smaller cities (10K-25K)
            {'name': 'Forney city, Texas', 'place_fips': '26232', 'population': 24000, 'coords': (32.7479, -96.4719)},
            {'name': 'Ennis city, Texas', 'place_fips': '24768', 'population': 20000, 'coords': (32.3293, -96.6253)},
            {'name': 'Terrell city, Texas', 'place_fips': '72284', 'population': 18000, 'coords': (32.7357, -96.2753)},
            {'name': 'Gainesville city, Texas', 'place_fips': '28068', 'population': 17000, 'coords': (33.6262, -97.1336)},
            {'name': 'Fate city, Texas', 'place_fips': '25452', 'population': 15000, 'coords': (32.9373, -96.3869)},
            {'name': 'Mineral Wells city, Texas', 'place_fips': '48684', 'population': 14000, 'coords': (32.8085, -98.1128)},
            {'name': 'Athens city, Texas', 'place_fips': '04768', 'population': 13000, 'coords': (32.2049, -95.8555)},
            {'name': 'Royse City city, Texas', 'place_fips': '63668', 'population': 13000, 'coords': (32.9751, -96.3303)},
            {'name': 'Granbury city, Texas', 'place_fips': '30644', 'population': 10000, 'coords': (32.4421, -97.7947)},
            {'name': 'Commerce city, Texas', 'place_fips': '15976', 'population': 9000, 'coords': (33.2465, -95.9000)},
            
            # Additional smaller cities and towns
            {'name': 'Sachse city, Texas', 'place_fips': '64064', 'population': 27000, 'coords': (32.9779, -96.5908)},
            {'name': 'Murphy city, Texas', 'place_fips': '50100', 'population': 21000, 'coords': (33.0151, -96.6131)},
            {'name': 'Lucas city, Texas', 'place_fips': '45012', 'population': 7000, 'coords': (33.0868, -96.5731)},
            {'name': 'Parker city, Texas', 'place_fips': '55152', 'population': 5000, 'coords': (33.0568, -96.6253)},
            {'name': 'Princeton city, Texas', 'place_fips': '59576', 'population': 17000, 'coords': (33.1801, -96.4989)},
            {'name': 'Farmersville city, Texas', 'place_fips': '25452', 'population': 3500, 'coords': (33.1637, -96.3597)},
            {'name': 'Nevada city, Texas', 'place_fips': '50760', 'population': 1000, 'coords': (33.0418, -96.3731)},
            {'name': 'Celina city, Texas', 'place_fips': '13576', 'population': 16000, 'coords': (33.3246, -96.7847)},
            {'name': 'Prosper town, Texas', 'place_fips': '59696', 'population': 30000, 'coords': (33.2362, -96.8011)},
            {'name': 'Little Elm city, Texas', 'place_fips': '43012', 'population': 52000, 'coords': (33.1626, -96.9375)},
        ]
        
        # Filter by radius and add distance
        filtered_cities = []
        for city in target_cities:
            distance = self.calculate_distance(self.dallas_coords, city['coords'])
            if distance <= self.radius_miles:
                city['distance_from_dallas'] = distance
                filtered_cities.append(city)
        
        # Sort by population (largest first) to prioritize major cities
        filtered_cities.sort(key=lambda x: x['population'], reverse=True)
        
        print(f"🎯 Target cities within {self.radius_miles:.1f} miles: {len(filtered_cities)}")
        return filtered_cities

    def get_demographic_data(self, place_fips: str, year: int) -> Dict:
        """Get demographic data for a specific place"""
        url = f"{self.base_url}/{year}/acs/acs5"
        
        variables_str = ','.join(self.variables.keys())
        
        params = {
            'get': f'NAME,{variables_str}',
            'for': f'place:{place_fips}',
            'in': 'state:48'
        }
        
        # Add API key if available
        if self.api_key:
            params['key'] = self.api_key
            
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if len(data) > 1:
                row = data[1]
                result = {'name': row[0], 'year': year}
                
                for i, var_code in enumerate(self.variables.keys(), 1):
                    var_name = self.variables[var_code]
                    value = row[i] if i < len(row) else None
                    result[var_name] = value if value not in ['-999999999', None, ''] else 0
                    
                return result
            return None
            
        except Exception as e:
            print(f"❌ Error getting data for place {place_fips} in {year}: {e}")
            return None

    def save_incremental_data(self, all_data: List[Dict]):
        """Save data incrementally"""
        if all_data:
            df = pd.DataFrame(all_data)
            # Ensure city column exists
            if 'city' not in df.columns:
                df['city'] = df['name'].str.replace(r', Texas$', '', regex=True)
            df.to_csv(self.output_file, index=False)
            print(f"💾 Saved {len(all_data)} records to {self.output_file}")

    def collect_data_incrementally(self, start_year: int = 2009, end_year: int = 2022):
        """Collect data with incremental saves and duplicate checking"""
        print("🔄 Starting incremental data collection with duplicate checking...")
        
        # Load existing data
        all_data, existing_combinations = self.load_existing_data()
        
        # Get target cities
        target_cities = self.get_target_cities()
        
        years = list(range(start_year, end_year + 1))
        years = [y for y in years if y >= 2009]  # Only ACS 5-year data
        
        total_possible = len(target_cities) * len(years)
        completed = len(existing_combinations)
        
        print(f"📊 Initial Progress: {completed}/{total_possible} ({completed/total_possible*100:.1f}%)")
        
        for i, city in enumerate(target_cities):
            city_name = city['name']
            city_clean = city_name.replace(', Texas', '')
            place_fips = city['place_fips']
            
            print(f"\n🏙️ [{i+1}/{len(target_cities)}] Processing {city_name}")
            print(f"   📍 Population: {city['population']:,}, Distance: {city['distance_from_dallas']:.1f} mi")
            
            # Check if this city is already complete
            city_existing_years = [year for (c, year) in existing_combinations if c == city_clean]
            missing_years = [year for year in years if year not in city_existing_years]
            
            if not missing_years:
                print(f"   ✅ City already complete - all {len(years)} years present")
                continue
            
            print(f"   📅 Missing years: {missing_years} ({len(missing_years)} of {len(years)})")
            
            city_data_added = 0
            
            for year in missing_years:
                print(f"   📊 Collecting {year} data...", end=' ')
                
                data = self.get_demographic_data(place_fips, year)
                if data:
                    # Add additional fields
                    data['place_fips'] = place_fips
                    data['coordinates'] = city['coords']
                    data['distance_from_dallas'] = city['distance_from_dallas']
                    data['reference_population'] = city['population']
                    
                    all_data.append(data)
                    existing_combinations.add((city_clean, year))
                    city_data_added += 1
                    print("✅")
                else:
                    print("❌ Failed")
                
                # Rate limiting - faster with API key
                time.sleep(0.05 if self.api_key else 0.1)
            
            # Save after each city
            if city_data_added > 0:
                self.save_incremental_data(all_data)
                print(f"   💾 Added {city_data_added} new records")
            
            # Show overall progress
            completed = len(existing_combinations)
            progress_pct = (completed / total_possible) * 100
            print(f"   🎯 Overall progress: {completed}/{total_possible} ({progress_pct:.1f}%)")
            
            # Show estimated time remaining
            if i > 0 and progress_pct > 0:
                cities_per_minute = (i + 1) / ((time.time() - self.start_time) / 60)
                remaining_cities = len(target_cities) - (i + 1)
                eta_minutes = remaining_cities / cities_per_minute if cities_per_minute > 0 else 0
                if eta_minutes > 0:
                    print(f"   ⏱️ ETA: ~{eta_minutes:.0f} minutes remaining")
        
        print(f"\n🎉 Collection complete! Final dataset: {len(all_data)} records")
        
        # Final save and summary
        if all_data:
            self.save_incremental_data(all_data)
            df = pd.DataFrame(all_data)
            
            # Ensure city column exists for summary
            if 'city' not in df.columns:
                df['city'] = df['name'].str.replace(r', Texas$', '', regex=True)
            
            print(f"\n📈 FINAL SUMMARY:")
            print(f"  • Total records: {len(df):,}")
            print(f"  • Cities: {df['city'].nunique()}")
            print(f"  • Years: {sorted(df['year'].unique())}")
            print(f"  • File: {self.output_file}")
            
            return df
        
        return pd.DataFrame()

def main():
    """Main function"""
    print("🌟 ENHANCED INCREMENTAL NORTH TEXAS DATA COLLECTOR")
    print("=" * 60)
    
    # Check for environment variable first
    api_key_from_env = os.getenv('CENSUS_API_KEY')
    if api_key_from_env:
        print(f"🔑 Found CENSUS_API_KEY environment variable")
        api_key = api_key_from_env
    else:
        # Fallback to manual input
        api_key = input("Enter your Census API key (or press Enter to skip): ").strip()
        if not api_key:
            api_key = None
            print("⚠️ No API key provided - using slower rate limits")
    
    collector = IncrementalDataCollector(api_key=api_key)
    collector.start_time = time.time()  # For ETA calculation
    
    try:
        df = collector.collect_data_incrementally(start_year=2009, end_year=2022)
        
        if not df.empty:
            print(f"\n💡 Next steps:")
            print(f"  • Run: python create_expanded_map_visualization.py")
            print(f"  • Your data is saved in: {collector.output_file}")
            print(f"  • You can also copy it to the standard name:")
            print(f"    cp {collector.output_file} north_texas_expanded_demographics_$(date +%Y%m%d_%H%M%S).csv")
        
    except KeyboardInterrupt:
        print(f"\n⏸️ Collection paused. Progress saved in: {collector.output_file}")
        print(f"💡 Run this script again to resume from where you left off!")
        print(f"🔑 Your API key will be remembered from the CENSUS_API_KEY environment variable")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
