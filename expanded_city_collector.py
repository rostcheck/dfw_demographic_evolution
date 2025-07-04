#!/usr/bin/env python3
"""
Expanded City Collector for Dallas-Denison Radius Area
Collects all cities within the radius from Dallas to Denison (~60 miles)
"""

import requests
import pandas as pd
import time
import math
from typing import List, Dict, Tuple
import os

class ExpandedCityCollector:
    def __init__(self, api_key: str = None):
        """
        Initialize the Expanded City Collector
        
        Args:
            api_key: Census API key (optional but recommended for higher rate limits)
        """
        self.api_key = api_key
        self.base_url = "https://api.census.gov/data"
        
        # Dallas coordinates (center point)
        self.dallas_coords = (32.7767, -96.7970)
        # Denison coordinates (northern boundary)
        self.denison_coords = (33.7557, -96.5367)
        
        # Calculate radius (Dallas to Denison distance)
        self.radius_miles = self.calculate_distance(self.dallas_coords, self.denison_coords)
        print(f"Search radius: {self.radius_miles:.1f} miles from Dallas")
        
        # Expanded North Texas counties (including surrounding areas)
        self.expanded_counties = {
            # Core DFW
            'Dallas': '113',
            'Tarrant': '439', 
            'Collin': '085',
            'Denton': '121',
            'Rockwall': '397',
            'Ellis': '139',
            'Johnson': '251',
            'Kaufman': '257',
            'Parker': '367',
            'Wise': '497',
            
            # Extended radius counties
            'Hunt': '231',      # Greenville, Commerce
            'Hopkins': '223',   # Sulphur Springs
            'Grayson': '181',   # Sherman, Denison
            'Cooke': '097',     # Gainesville
            'Montague': '337',  # Bowie
            'Clay': '077',      # Henrietta
            'Jack': '237',      # Jacksboro
            'Palo Pinto': '363', # Mineral Wells
            'Hood': '221',      # Granbury
            'Somervell': '425', # Glen Rose
            'Hill': '217',      # Hillsboro
            'Navarro': '349',   # Corsicana
            'Henderson': '213', # Athens
            'Van Zandt': '467', # Canton
            'Rains': '379',     # Emory
            'Wood': '499',      # Quitman
            'Smith': '423',     # Tyler (partial)
            'Cherokee': '073',  # Rusk (partial)
            'Anderson': '001',  # Palestine (partial)
            'Freestone': '161', # Fairfield
            'Limestone': '293', # Groesbeck
            'McLennan': '309'   # Waco (northern part)
        }
        
        # Census variables (same as before but optimized)
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

    def get_all_texas_places(self, year: int = 2022) -> List[Dict]:
        """Get all places in Texas with coordinates"""
        print(f"Fetching all Texas cities for {year}...")
        
        url = f"{self.base_url}/{year}/acs/acs5"
        
        params = {
            'get': 'NAME,B01003_001E',  # Name and population
            'for': 'place:*',
            'in': 'state:48'  # Texas
        }
        
        if self.api_key:
            params['key'] = self.api_key
            
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            places = []
            for row in data[1:]:  # Skip header row
                if len(row) >= 4:
                    name = row[0]
                    population = row[1]
                    state = row[2]
                    place_fips = row[3]
                    
                    # Only include places with reasonable population
                    try:
                        pop_num = int(population) if population not in ['-999999999', None, ''] else 0
                        if pop_num >= 1000:  # Minimum population threshold
                            places.append({
                                'name': name,
                                'population': pop_num,
                                'state': state,
                                'place_fips': place_fips
                            })
                    except (ValueError, TypeError):
                        continue
            
            print(f"Found {len(places)} Texas cities with population >= 1,000")
            return places
            
        except Exception as e:
            print(f"Error getting Texas places: {e}")
            return []

    def get_city_coordinates(self, city_name: str) -> Tuple[float, float]:
        """Get approximate coordinates for a city (simplified mapping)"""
        
        # Expanded coordinate database for North Texas region
        city_coords = {
            # Core DFW (existing)
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
            
            # Extended North Texas cities
            'Sherman city': (33.6356, -96.6089),
            'Denison city': (33.7557, -96.5367),
            'Gainesville city': (33.6262, -97.1336),
            'Greenville city': (33.1384, -96.1106),
            'Commerce city': (33.2465, -95.9000),
            'Sulphur Springs city': (33.1384, -95.6011),
            'Tyler city': (32.3513, -95.3011),
            'Athens city': (32.2049, -95.8555),
            'Canton city': (32.5568, -95.8619),
            'Corsicana city': (32.0954, -96.4689),
            'Waxahachie city': (32.3865, -96.8489),
            'Ennis city': (32.3293, -96.6253),
            'Hillsboro city': (32.0107, -97.1281),
            'Cleburne city': (32.3476, -97.3867),
            'Granbury city': (32.4421, -97.7947),
            'Weatherford city': (32.7593, -97.7975),
            'Mineral Wells city': (32.8085, -98.1128),
            'Jacksboro city': (33.2187, -98.1589),
            'Bowie city': (33.5587, -97.8486),
            'Decatur city': (33.2342, -97.5864),
            'Bridgeport city': (33.2081, -97.7522),
            'Azle city': (32.8946, -97.5453),
            'Burleson city': (32.5421, -97.3208),
            'Crowley city': (32.5793, -97.3625),
            'Forest Hill city': (32.6712, -97.2697),
            'Haltom City city': (32.7996, -97.2692),
            'Keller city': (32.9346, -97.2514),
            'North Richland Hills city': (32.8343, -97.2289),
            'Richland Hills city': (32.8151, -97.2281),
            'Watauga city': (32.8579, -97.2547),
            'White Settlement city': (32.7593, -97.4503),
            'Benbrook city': (32.6732, -97.4606),
            'Saginaw city': (32.8579, -97.3697),
            'Haslet city': (32.9707, -97.3403),
            'Justin city': (33.0851, -97.2961),
            'Roanoke city': (33.0040, -97.2264),
            'Trophy Club town': (32.9918, -97.1831),
            'Westlake town': (32.9918, -97.1831),
            'Southlake city': (32.9412, -97.1342),
            'Grapevine city': (32.9343, -97.0781),
            'Colleyville city': (32.9090, -97.1550),
            'Bedford city': (32.8440, -97.1431),
            'Hurst city': (32.8235, -97.1706),
            'Euless city': (32.8371, -97.0820),
            
            # Additional smaller cities
            'Terrell city': (32.7357, -96.2753),
            'Forney city': (32.7479, -96.4719),
            'Seagoville city': (32.6390, -96.5386),
            'Balch Springs city': (32.7290, -96.6228),
            'Sunnyvale town': (32.7968, -96.5581),
            'Fate city': (32.9373, -96.3869),
            'Royse City city': (32.9751, -96.3303),
            'Rockwall city': (32.9312, -96.4597),
            'Heath city': (32.8390, -96.4764),
            'McLendon-Chisholm city': (32.8179, -96.3719),
            'Rowlett city': (32.9029, -96.5639),
            'Sachse city': (32.9779, -96.5908),
            'Wylie city': (33.0151, -96.5389),
            'Murphy city': (33.0151, -96.6131),
            'Parker city': (33.0568, -96.6253),
            'Lucas city': (33.0868, -96.5731),
            'Fairview town': (33.1579, -96.6317),
            'Lowry Crossing city': (33.1968, -96.5497),
            'Princeton city': (33.1801, -96.4989),
            'Farmersville city': (33.1637, -96.3597),
            'Nevada city': (33.0418, -96.3731),
            'Josephine city': (33.0651, -96.3097),
            'Celina city': (33.3246, -96.7847),
            'Prosper town': (33.2362, -96.8011),
            'Little Elm city': (33.1626, -96.9375),
            'The Colony city': (33.0890, -96.8928),
            'Lake Dallas city': (33.1179, -97.0203),
            'Hickory Creek town': (33.1218, -97.0403),
            'Shady Shores town': (33.1651, -97.0203),
            'Corinth city': (33.1540, -97.0647),
            'Lake Worth city': (32.8068, -97.4442),
            'Sansom Park city': (32.8018, -97.4031),
            'River Oaks city': (32.7782, -97.3939),
            'Westworth Village city': (32.7518, -97.4281),
            'Everman city': (32.6318, -97.2889),
            'Kennedale city': (32.6468, -97.2267),
            'Pantego town': (32.7146, -97.1564),
            'Dalworthington Gardens city': (32.7018, -97.1531),
            'Grand Prairie city': (32.7459, -96.9978),
            'Cedar Hill city': (32.5882, -96.9561),
            'DeSoto city': (32.5896, -96.8570),
            'Duncanville city': (32.6518, -96.9083),
            'Lancaster city': (32.5921, -96.7561),
            'Red Oak city': (32.5182, -96.8003),
            'Ovilla city': (32.5218, -96.8831),
            'Glenn Heights city': (32.5493, -96.8567),
            'Ferris city': (32.5343, -96.6831),
            'Palmer city': (32.4329, -96.6831),
            'Waxahachie city': (32.3865, -96.8489),
            'Midlothian city': (32.4821, -97.1042),
            'Mansfield city': (32.5632, -97.1417),
            'Venus town': (32.4329, -97.1025),
            'Alvarado city': (32.4065, -97.2103),
            'Keene city': (32.3968, -97.3236),
            'Joshua city': (32.4615, -97.3881),
            'Godley city': (32.4482, -97.5281),
            'Granbury city': (32.4421, -97.7947)
        }
        
        # Clean city name for lookup
        clean_name = city_name.replace(', Texas', '').strip()
        
        if clean_name in city_coords:
            return city_coords[clean_name]
        
        # If not found, try to estimate based on county or return None
        return None

    def filter_cities_by_radius(self, places: List[Dict]) -> List[Dict]:
        """Filter cities to only include those within the Dallas-Denison radius"""
        print(f"Filtering cities within {self.radius_miles:.1f} miles of Dallas...")
        
        filtered_places = []
        
        for place in places:
            city_name = place['name']
            coords = self.get_city_coordinates(city_name)
            
            if coords:
                distance = self.calculate_distance(self.dallas_coords, coords)
                if distance <= self.radius_miles:
                    place['coordinates'] = coords
                    place['distance_from_dallas'] = distance
                    filtered_places.append(place)
        
        # Sort by population (largest first)
        filtered_places.sort(key=lambda x: x['population'], reverse=True)
        
        print(f"Found {len(filtered_places)} cities within radius")
        return filtered_places

    def get_demographic_data(self, place_fips: str, year: int) -> Dict:
        """Get demographic data for a specific place"""
        url = f"{self.base_url}/{year}/acs/acs5"
        
        variables_str = ','.join(self.variables.keys())
        
        params = {
            'get': f'NAME,{variables_str}',
            'for': f'place:{place_fips}',
            'in': 'state:48'
        }
        
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
            print(f"Error getting data for place {place_fips} in {year}: {e}")
            return None

    def collect_expanded_data(self, start_year: int = 2009, end_year: int = 2022) -> pd.DataFrame:
        """Collect demographic data for all cities in the expanded radius"""
        print("Starting expanded data collection for Dallas-Denison radius...")
        
        # Get all Texas places and filter by radius
        all_places = self.get_all_texas_places(2022)  # Use 2022 as reference year
        filtered_places = self.filter_cities_by_radius(all_places)
        
        if not filtered_places:
            print("No cities found within radius!")
            return pd.DataFrame()
        
        print(f"Collecting data for {len(filtered_places)} cities across {end_year - start_year + 1} years...")
        
        all_data = []
        total_requests = len(filtered_places) * (end_year - start_year + 1)
        current_request = 0
        
        for place in filtered_places:
            place_name = place['name']
            place_fips = place['place_fips']
            coords = place.get('coordinates')
            distance = place.get('distance_from_dallas', 0)
            
            print(f"\nProcessing {place_name} (pop: {place['population']:,}, distance: {distance:.1f} mi)...")
            
            for year in range(start_year, end_year + 1):
                current_request += 1
                
                if current_request % 10 == 0:  # Progress update every 10 requests
                    print(f"Progress: {current_request}/{total_requests} ({current_request/total_requests*100:.1f}%)")
                
                # Skip years before ACS 5-year estimates
                if year < 2009:
                    continue
                    
                data = self.get_demographic_data(place_fips, year)
                if data:
                    data['place_fips'] = place_fips
                    data['coordinates'] = coords
                    data['distance_from_dallas'] = distance
                    data['reference_population'] = place['population']  # 2022 reference
                    all_data.append(data)
                
                time.sleep(0.05)  # Reduced rate limiting for more cities
        
        df = pd.DataFrame(all_data)
        
        if not df.empty:
            # Clean city names
            df['city'] = df['name'].str.replace(r', Texas$', '', regex=True)
            
            # Add county information (simplified)
            df['county'] = df['city'].apply(self.estimate_county)
        
        return df

    def estimate_county(self, city_name: str) -> str:
        """Estimate county based on city name and location"""
        # Simplified county mapping for major cities
        county_map = {
            'Dallas': 'Dallas', 'Fort Worth': 'Tarrant', 'Arlington': 'Tarrant',
            'Plano': 'Collin', 'Irving': 'Dallas', 'Garland': 'Dallas',
            'Frisco': 'Collin', 'McKinney': 'Collin', 'Denton': 'Denton',
            'Sherman': 'Grayson', 'Denison': 'Grayson', 'Gainesville': 'Cooke',
            'Greenville': 'Hunt', 'Tyler': 'Smith', 'Athens': 'Henderson',
            'Corsicana': 'Navarro', 'Waxahachie': 'Ellis', 'Cleburne': 'Johnson',
            'Granbury': 'Hood', 'Weatherford': 'Parker', 'Mineral Wells': 'Palo Pinto'
        }
        
        for city_key, county in county_map.items():
            if city_key.lower() in city_name.lower():
                return county
        
        return 'Other'

    def save_expanded_data(self, df: pd.DataFrame, filename: str = None):
        """Save the expanded dataset"""
        if filename is None:
            filename = f"north_texas_expanded_demographics_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = os.path.join(os.getcwd(), filename)
        df.to_csv(filepath, index=False)
        print(f"Expanded data saved to: {filepath}")
        return filepath

def main():
    """Main function to collect expanded data"""
    print("🌟 EXPANDED NORTH TEXAS DEMOGRAPHIC COLLECTION")
    print("=" * 60)
    
    # Get API key
    api_key = input("Enter your Census API key (or press Enter to skip): ").strip()
    if not api_key:
        api_key = None
        print("Using without API key (slower rate limits)")
    
    collector = ExpandedCityCollector(api_key=api_key)
    
    # Collect data
    print("\nStarting expanded data collection...")
    df = collector.collect_expanded_data(start_year=2009, end_year=2022)
    
    if not df.empty:
        # Save data
        filepath = collector.save_expanded_data(df)
        
        # Display summary
        print(f"\n🎉 EXPANDED DATA COLLECTION COMPLETE!")
        print(f"=" * 50)
        print(f"Total records: {len(df):,}")
        print(f"Cities covered: {df['city'].nunique()}")
        print(f"Years covered: {sorted(df['year'].unique())}")
        print(f"Counties represented: {sorted(df['county'].unique())}")
        
        # Show largest cities
        print(f"\nTop 10 largest cities by 2022 population:")
        latest_year = df['year'].max()
        top_cities = df[df['year'] == latest_year].nlargest(10, 'total_population')
        for i, (_, row) in enumerate(top_cities.iterrows(), 1):
            print(f"  {i:2d}. {row['city']:<25} {row['total_population']:>8,} ({row['distance_from_dallas']:>4.1f} mi)")
        
        print(f"\n💡 Next steps:")
        print(f"  • Run: python create_expanded_map_visualization.py")
        print(f"  • This will create updated maps with all {df['city'].nunique()} cities!")
        
    else:
        print("❌ No data collected. Please check your API key and internet connection.")

if __name__ == "__main__":
    main()
