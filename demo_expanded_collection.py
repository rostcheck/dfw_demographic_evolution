#!/usr/bin/env python3
"""
Demo script showing expanded data collection capabilities
Shows what cities would be included in the Dallas-Denison radius
"""

import math
from typing import Tuple

def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
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

def demo_expanded_coverage():
    """Demonstrate what cities would be included in expanded coverage"""
    
    # Dallas coordinates (center point)
    dallas_coords = (32.7767, -96.7970)
    # Denison coordinates (northern boundary)
    denison_coords = (33.7557, -96.5367)
    
    # Calculate radius
    radius_miles = calculate_distance(dallas_coords, denison_coords)
    
    print("🌟 EXPANDED NORTH TEXAS COVERAGE DEMONSTRATION")
    print("=" * 60)
    print(f"📍 Center Point: Dallas, Texas")
    print(f"📏 Search Radius: {radius_miles:.1f} miles (Dallas to Denison distance)")
    print(f"🗺️ Coverage Area: ~{math.pi * radius_miles**2:,.0f} square miles")
    
    # Sample of cities that would be included (with approximate coordinates and populations)
    sample_cities = [
        # Core DFW (already included)
        ("Dallas", (32.7767, -96.7970), 1300000, "Dallas"),
        ("Fort Worth", (32.7555, -97.3308), 925000, "Tarrant"),
        ("Arlington", (32.7357, -97.1081), 394000, "Tarrant"),
        ("Plano", (33.0198, -96.6989), 285000, "Collin"),
        ("Irving", (32.8140, -96.9489), 255000, "Dallas"),
        ("Garland", (32.9126, -96.6389), 244000, "Dallas"),
        ("Frisco", (33.1507, -96.8236), 202000, "Collin"),
        ("McKinney", (33.1972, -96.6153), 196000, "Collin"),
        
        # Extended region (new additions)
        ("Sherman", (33.6356, -96.6089), 43000, "Grayson"),
        ("Denison", (33.7557, -96.5367), 25000, "Grayson"),
        ("Gainesville", (33.6262, -97.1336), 17000, "Cooke"),
        ("Greenville", (33.1384, -96.1106), 28000, "Hunt"),
        ("Commerce", (33.2465, -95.9000), 9000, "Hunt"),
        ("Sulphur Springs", (33.1384, -95.6011), 16000, "Hopkins"),
        ("Tyler", (32.3513, -95.3011), 106000, "Smith"),
        ("Athens", (32.2049, -95.8555), 13000, "Henderson"),
        ("Canton", (32.5568, -95.8619), 4000, "Van Zandt"),
        ("Corsicana", (32.0954, -96.4689), 25000, "Navarro"),
        ("Waxahachie", (32.3865, -96.8489), 41000, "Ellis"),
        ("Ennis", (32.3293, -96.6253), 20000, "Ellis"),
        ("Hillsboro", (32.0107, -97.1281), 8500, "Hill"),
        ("Cleburne", (32.3476, -97.3867), 31000, "Johnson"),
        ("Granbury", (32.4421, -97.7947), 10000, "Hood"),
        ("Weatherford", (32.7593, -97.7975), 31000, "Parker"),
        ("Mineral Wells", (32.8085, -98.1128), 14000, "Palo Pinto"),
        ("Jacksboro", (33.2187, -98.1589), 4500, "Jack"),
        ("Bowie", (33.5587, -97.8486), 5200, "Montague"),
        ("Decatur", (33.2342, -97.5864), 7000, "Wise"),
        ("Bridgeport", (33.2081, -97.7522), 6000, "Wise"),
        
        # Additional smaller cities
        ("Terrell", (32.7357, -96.2753), 18000, "Kaufman"),
        ("Forney", (32.7479, -96.4719), 24000, "Kaufman"),
        ("Rockwall", (32.9312, -96.4597), 47000, "Rockwall"),
        ("Wylie", (33.0151, -96.5389), 57000, "Collin"),
        ("Rowlett", (32.9029, -96.5639), 66000, "Dallas"),
        ("The Colony", (33.0890, -96.8928), 45000, "Denton"),
        ("Flower Mound", (33.0145, -97.0969), 78000, "Denton"),
        ("Southlake", (32.9412, -97.1342), 31000, "Tarrant"),
        ("Grapevine", (32.9343, -97.0781), 54000, "Tarrant"),
        ("Euless", (32.8371, -97.0820), 60000, "Tarrant"),
        ("Bedford", (32.8440, -97.1431), 49000, "Tarrant"),
        ("Hurst", (32.8235, -97.1706), 40000, "Tarrant"),
        ("Keller", (32.9346, -97.2514), 48000, "Tarrant"),
        ("North Richland Hills", (32.8343, -97.2289), 70000, "Tarrant"),
        ("Mansfield", (32.5632, -97.1417), 73000, "Tarrant"),
        ("Cedar Hill", (32.5882, -96.9561), 48000, "Dallas"),
        ("DeSoto", (32.5896, -96.8570), 54000, "Dallas"),
        ("Duncanville", (32.6518, -96.9083), 40000, "Dallas"),
        ("Lancaster", (32.5921, -96.7561), 41000, "Dallas"),
        ("Burleson", (32.5421, -97.3208), 49000, "Johnson/Tarrant"),
    ]
    
    # Filter cities within radius and categorize
    cities_in_radius = []
    cities_outside_radius = []
    
    for city_name, coords, population, county in sample_cities:
        distance = calculate_distance(dallas_coords, coords)
        if distance <= radius_miles:
            cities_in_radius.append((city_name, coords, population, county, distance))
        else:
            cities_outside_radius.append((city_name, coords, population, county, distance))
    
    # Sort by population
    cities_in_radius.sort(key=lambda x: x[2], reverse=True)
    
    print(f"\n✅ CITIES WITHIN {radius_miles:.1f} MILE RADIUS ({len(cities_in_radius)} cities):")
    print("-" * 80)
    
    total_population = 0
    population_categories = {
        "Major Cities (100K+)": [],
        "Large Cities (50K-100K)": [],
        "Medium Cities (25K-50K)": [],
        "Small Cities (10K-25K)": [],
        "Towns (<10K)": []
    }
    
    for city_name, coords, population, county, distance in cities_in_radius:
        total_population += population
        
        # Categorize by population
        if population >= 100000:
            population_categories["Major Cities (100K+)"].append((city_name, population, county, distance))
        elif population >= 50000:
            population_categories["Large Cities (50K-100K)"].append((city_name, population, county, distance))
        elif population >= 25000:
            population_categories["Medium Cities (25K-50K)"].append((city_name, population, county, distance))
        elif population >= 10000:
            population_categories["Small Cities (10K-25K)"].append((city_name, population, county, distance))
        else:
            population_categories["Towns (<10K)"].append((city_name, population, county, distance))
        
        print(f"{city_name:<25} {population:>8,} {county:<12} {distance:>5.1f} mi")
    
    print(f"\n📊 POPULATION BREAKDOWN:")
    print("-" * 40)
    for category, cities in population_categories.items():
        if cities:
            print(f"{category}: {len(cities)} cities")
            for city_name, population, county, distance in cities[:3]:  # Show top 3 in each category
                print(f"  • {city_name} ({population:,})")
            if len(cities) > 3:
                print(f"  • ... and {len(cities) - 3} more")
            print()
    
    print(f"📈 REGIONAL STATISTICS:")
    print("-" * 30)
    print(f"Total Population: {total_population:,}")
    print(f"Average Distance from Dallas: {sum(d[4] for d in cities_in_radius) / len(cities_in_radius):.1f} miles")
    print(f"Counties Represented: {len(set(d[3] for d in cities_in_radius))}")
    
    print(f"\n🚫 CITIES OUTSIDE RADIUS ({len(cities_outside_radius)} cities):")
    if cities_outside_radius:
        for city_name, coords, population, county, distance in cities_outside_radius[:5]:
            print(f"  • {city_name} ({distance:.1f} mi) - Too far")
    
    print(f"\n💡 EXPANDED DATA COLLECTION BENEFITS:")
    print("-" * 45)
    print(f"• Comprehensive regional analysis beyond core DFW")
    print(f"• Include smaller communities and rural areas")
    print(f"• Show suburban sprawl and growth patterns")
    print(f"• Capture demographic diversity across the region")
    print(f"• Analyze economic corridors and transportation impacts")
    
    print(f"\n🔄 TO COLLECT EXPANDED DATA:")
    print("-" * 35)
    print(f"1. Run: python expanded_city_collector.py")
    print(f"2. Wait for data collection (may take 30-60 minutes)")
    print(f"3. Run: python create_expanded_map_visualization.py")
    print(f"4. Open: north_texas_expanded_dashboard.html")
    
    print(f"\n⚡ CURRENT STATUS:")
    print("-" * 20)
    print(f"• Original dataset: 32 major cities")
    print(f"• Expanded potential: {len(cities_in_radius)}+ cities")
    print(f"• Coverage increase: ~{len(cities_in_radius)/32*100:.0f}% more cities")

if __name__ == "__main__":
    demo_expanded_coverage()
