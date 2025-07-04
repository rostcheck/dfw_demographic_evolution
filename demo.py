#!/usr/bin/env python3
"""
Demo script to showcase DFW Demographic Evolution project features
"""

import pandas as pd
import webbrowser
import time
import os
from pathlib import Path

def print_banner():
    """Print project banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                 DFW DEMOGRAPHIC EVOLUTION                    ║
║              Interactive Analysis & Visualization            ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def demo_data_overview():
    """Demonstrate data overview"""
    print("📊 DATA OVERVIEW")
    print("=" * 50)
    
    # Load data
    df = pd.read_csv('dfw_demographics_cleaned.csv')
    
    print(f"✓ Cities analyzed: {df['city'].nunique()}")
    print(f"✓ Years covered: {df['year'].min()}-{df['year'].max()}")
    print(f"✓ Total records: {len(df):,}")
    print(f"✓ Counties: {', '.join(sorted(df['county'].unique()))}")
    
    # Show sample data
    print(f"\n📋 Sample Data (Dallas):")
    dallas_sample = df[df['city'] == 'Dallas city'][['year', 'total_population', 'white_pct', 'hispanic_pct']].head(3)
    print(dallas_sample.to_string(index=False))

def demo_growth_analysis():
    """Demonstrate growth analysis"""
    print(f"\n🚀 POPULATION GROWTH ANALYSIS")
    print("=" * 50)
    
    df = pd.read_csv('dfw_demographics_cleaned.csv')
    
    # Calculate growth rates
    df_2009 = df[df['year'] == 2009].set_index('city')
    df_2022 = df[df['year'] == 2022].set_index('city')
    
    growth_data = []
    for city in df_2009.index:
        if city in df_2022.index:
            pop_2009 = df_2009.loc[city, 'total_population']
            pop_2022 = df_2022.loc[city, 'total_population']
            if pop_2009 > 0:
                growth_rate = ((pop_2022 - pop_2009) / pop_2009) * 100
                growth_data.append({
                    'city': city,
                    'growth_rate': growth_rate,
                    'pop_2009': pop_2009,
                    'pop_2022': pop_2022
                })
    
    growth_df = pd.DataFrame(growth_data).sort_values('growth_rate', ascending=False)
    
    print("🏆 Top 5 Fastest Growing Cities:")
    for i, row in growth_df.head(5).iterrows():
        print(f"  {row['city']:<25} {row['growth_rate']:>6.1f}% ({row['pop_2009']:,} → {row['pop_2022']:,})")

def demo_demographic_changes():
    """Demonstrate demographic composition changes"""
    print(f"\n🌈 DEMOGRAPHIC COMPOSITION CHANGES")
    print("=" * 50)
    
    df = pd.read_csv('dfw_demographics_cleaned.csv')
    
    # Focus on major cities
    major_cities = ['Dallas city', 'Fort Worth city', 'Plano city', 'Frisco city']
    
    for city in major_cities:
        city_data = df[df['city'] == city]
        if city_data.empty:
            continue
        
        data_2009 = city_data[city_data['year'] == 2009]
        data_2022 = city_data[city_data['year'] == 2022]
        
        if not data_2009.empty and not data_2022.empty:
            print(f"\n📍 {city}:")
            
            # Calculate changes
            asian_change = data_2022.iloc[0]['asian_pct'] - data_2009.iloc[0]['asian_pct']
            hispanic_change = data_2022.iloc[0]['hispanic_pct'] - data_2009.iloc[0]['hispanic_pct']
            
            print(f"   Asian population: {data_2009.iloc[0]['asian_pct']:.1f}% → {data_2022.iloc[0]['asian_pct']:.1f}% ({asian_change:+.1f}%)")
            print(f"   Hispanic population: {data_2009.iloc[0]['hispanic_pct']:.1f}% → {data_2022.iloc[0]['hispanic_pct']:.1f}% ({hispanic_change:+.1f}%)")

def demo_visualizations():
    """Demonstrate visualization features"""
    print(f"\n🗺️  INTERACTIVE VISUALIZATIONS")
    print("=" * 50)
    
    print("📱 Available Visualizations:")
    print("  • Interactive Demographic Map - Toggle between 2009/2022 data")
    print("  • Population Timeline Map - See growth over time")
    print("  • Comprehensive Dashboard - All visualizations in one place")
    
    print(f"\n🌐 Web Features:")
    print("  • Click any city marker for detailed demographics")
    print("  • Layer controls to switch between different views")
    print("  • Color-coded growth rates with legend")
    print("  • Responsive design for desktop and mobile")
    
    # Check if HTML files exist
    html_files = ['dfw_demographic_dashboard.html', 'dfw_demographic_map.html', 'dfw_population_timeline.html']
    existing_files = [f for f in html_files if Path(f).exists()]
    
    print(f"\n✅ Generated Files ({len(existing_files)}/{len(html_files)}):")
    for file in existing_files:
        size_kb = Path(file).stat().st_size / 1024
        print(f"  • {file} ({size_kb:.1f} KB)")

def demo_launch_browser():
    """Offer to launch the visualization in browser"""
    print(f"\n🚀 LAUNCH DEMONSTRATION")
    print("=" * 50)
    
    if Path('dfw_demographic_dashboard.html').exists():
        print("Ready to launch interactive dashboard!")
        
        response = input("\n🌐 Would you like to start the web server and view the visualizations? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            print("\n🔄 Starting web server...")
            print("📊 Dashboard will open in your default browser")
            print("💡 Press Ctrl+C in the terminal to stop the server when done")
            
            # Import and run the server
            try:
                import subprocess
                import sys
                
                # Start the server in a new process
                subprocess.run([sys.executable, 'serve_maps.py'])
                
            except KeyboardInterrupt:
                print("\n👋 Demo completed!")
            except Exception as e:
                print(f"\n❌ Error starting server: {e}")
                print("💡 You can manually run: python serve_maps.py")
        else:
            print("\n💡 To view visualizations later, run: python serve_maps.py")
    else:
        print("❌ Visualization files not found. Please run: python create_map_visualization.py")

def main():
    """Main demo function"""
    print_banner()
    
    try:
        demo_data_overview()
        demo_growth_analysis()
        demo_demographic_changes()
        demo_visualizations()
        demo_launch_browser()
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: Required data files not found.")
        print(f"💡 Please run the data collection script first:")
        print(f"   python census_data_collector_simple.py")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        print(f"💡 Please check that all required files are present")
    
    print(f"\n🎉 Thank you for exploring the DFW Demographic Evolution project!")

if __name__ == "__main__":
    main()
