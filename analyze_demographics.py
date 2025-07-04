#!/usr/bin/env python3
"""
DFW Demographic Data Analysis
Analyzes the collected Census data for demographic trends
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_and_clean_data(csv_file):
    """Load and clean the demographic data"""
    df = pd.read_csv(csv_file)
    
    # Convert numeric columns to proper types
    numeric_columns = ['year', 'total_population', 'white_alone', 'black_alone', 
                      'asian_alone', 'two_or_more_races', 'hispanic_latino',
                      'german', 'irish', 'english', 'mexican', 'indian', 
                      'chinese', 'vietnamese', 'french', 'italian', 'korean']
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Clean city names (remove state suffix)
    df['city'] = df['name'].str.replace(r', Texas$', '', regex=True)
    
    return df

def analyze_population_growth(df):
    """Analyze population growth trends"""
    print("=== POPULATION GROWTH ANALYSIS ===\n")
    
    # Get 2009 and 2022 data for comparison
    pop_2009 = df[df['year'] == 2009][['city', 'total_population', 'county']].copy()
    pop_2022 = df[df['year'] == 2022][['city', 'total_population', 'county']].copy()
    
    # Merge and calculate growth
    growth = pop_2009.merge(pop_2022, on=['city', 'county'], suffixes=('_2009', '_2022'))
    growth['population_change'] = growth['total_population_2022'] - growth['total_population_2009']
    growth['growth_rate'] = (growth['population_change'] / growth['total_population_2009']) * 100
    
    # Sort by growth rate
    growth = growth.sort_values('growth_rate', ascending=False)
    
    print("Top 10 Fastest Growing Cities (2009-2022):")
    print("-" * 60)
    for _, row in growth.head(10).iterrows():
        print(f"{row['city']:<25} {row['growth_rate']:>6.1f}% ({row['population_change']:>+7,})")
    
    print(f"\nTop 10 Largest Cities in 2022:")
    print("-" * 50)
    largest_2022 = df[df['year'] == 2022].nlargest(10, 'total_population')
    for _, row in largest_2022.iterrows():
        print(f"{row['city']:<25} {row['total_population']:>8,}")
    
    return growth

def analyze_demographic_composition(df):
    """Analyze racial/ethnic composition changes"""
    print("\n=== DEMOGRAPHIC COMPOSITION ANALYSIS ===\n")
    
    # Calculate percentages for major cities
    major_cities = ['Dallas city', 'Fort Worth city', 'Arlington city', 'Plano city', 'Frisco city']
    
    for city in major_cities:
        city_data = df[df['city'] == city].copy()
        if city_data.empty:
            continue
            
        print(f"{city} Demographic Changes (2009 vs 2022):")
        print("-" * 50)
        
        # Get 2009 and 2022 data
        data_2009 = city_data[city_data['year'] == 2009].iloc[0] if len(city_data[city_data['year'] == 2009]) > 0 else None
        data_2022 = city_data[city_data['year'] == 2022].iloc[0] if len(city_data[city_data['year'] == 2022]) > 0 else None
        
        if data_2009 is not None and data_2022 is not None:
            # Calculate percentages
            for year, data in [('2009', data_2009), ('2022', data_2022)]:
                total = data['total_population']
                white_pct = (data['white_alone'] / total) * 100
                black_pct = (data['black_alone'] / total) * 100
                asian_pct = (data['asian_alone'] / total) * 100
                hispanic_pct = (data['hispanic_latino'] / total) * 100
                
                print(f"  {year}: White {white_pct:.1f}%, Black {black_pct:.1f}%, Asian {asian_pct:.1f}%, Hispanic {hispanic_pct:.1f}%")
        print()

def analyze_ancestry_trends(df):
    """Analyze ancestry/national origin trends"""
    print("=== ANCESTRY TRENDS ANALYSIS ===\n")
    
    # Focus on major ancestry groups
    ancestry_cols = ['german', 'irish', 'english', 'mexican', 'indian', 'chinese', 'vietnamese']
    
    # Get 2022 data and sum across all cities
    df_2022 = df[df['year'] == 2022].copy()
    
    print("Top Ancestry Groups in DFW (2022 totals):")
    print("-" * 40)
    
    ancestry_totals = {}
    for col in ancestry_cols:
        if col in df_2022.columns:
            total = df_2022[col].sum()
            ancestry_totals[col] = total
    
    # Sort by total
    sorted_ancestry = sorted(ancestry_totals.items(), key=lambda x: x[1], reverse=True)
    
    for ancestry, total in sorted_ancestry:
        print(f"{ancestry.capitalize():<12} {total:>8,}")

def create_summary_report(df, growth_data):
    """Create a summary report"""
    print("\n" + "="*60)
    print("DFW DEMOGRAPHIC EVOLUTION SUMMARY REPORT")
    print("="*60)
    
    print(f"\nData Coverage:")
    print(f"  • Cities analyzed: {df['city'].nunique()}")
    print(f"  • Years covered: {df['year'].min()}-{df['year'].max()}")
    print(f"  • Counties: {', '.join(sorted(df['county'].unique()))}")
    print(f"  • Total records: {len(df):,}")
    
    # Overall metro growth
    total_2009 = df[df['year'] == 2009]['total_population'].sum()
    total_2022 = df[df['year'] == 2022]['total_population'].sum()
    metro_growth = ((total_2022 - total_2009) / total_2009) * 100
    
    print(f"\nOverall Metro Growth (2009-2022):")
    print(f"  • 2009 population: {total_2009:,}")
    print(f"  • 2022 population: {total_2022:,}")
    print(f"  • Growth rate: {metro_growth:.1f}%")
    print(f"  • Population added: {total_2022 - total_2009:,}")
    
    print(f"\nFastest Growing Cities:")
    for i, (_, row) in enumerate(growth_data.head(5).iterrows(), 1):
        print(f"  {i}. {row['city']} ({row['growth_rate']:.1f}%)")

def main():
    """Main analysis function"""
    # Find the most recent CSV file
    csv_files = list(Path('.').glob('dfw_major_cities_demographics_*.csv'))
    if not csv_files:
        print("No demographic data files found. Please run the data collection script first.")
        return
    
    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"Analyzing data from: {latest_file}")
    
    # Load and analyze data
    df = load_and_clean_data(latest_file)
    growth_data = analyze_population_growth(df)
    analyze_demographic_composition(df)
    analyze_ancestry_trends(df)
    create_summary_report(df, growth_data)
    
    # Save cleaned data
    cleaned_file = 'dfw_demographics_cleaned.csv'
    df.to_csv(cleaned_file, index=False)
    print(f"\nCleaned data saved to: {cleaned_file}")

if __name__ == "__main__":
    main()
