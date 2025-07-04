# DFW Demographic Evolution

This project collects and analyzes demographic data for cities in the Dallas-Fort Worth metropolitan area over the past 20 years using U.S. Census Bureau data, with interactive web-based visualizations.

## Features

- **Data Collection**: Automated Census API data collection for 32+ DFW cities
- **Analysis**: Population growth, demographic composition, and ancestry trend analysis
- **Interactive Maps**: Web-based visualizations showing demographic changes over time
- **Dashboard**: Comprehensive HTML dashboard with multiple visualization layers

## Data Sources
- U.S. Census Bureau American Community Survey (ACS) 5-Year Estimates
- Years covered: 2009-2022
- Geographic coverage: 10 North Texas counties

## Counties Included
- Dallas County
- Tarrant County (Fort Worth)
- Collin County
- Denton County
- Rockwall County
- Ellis County
- Johnson County
- Kaufman County
- Parker County
- Wise County

## Data Collected
- **Population**: Total population by city over time
- **Race**: Detailed racial breakdown (White, Black, Asian, Hispanic/Latino, etc.)
- **National Origin/Ancestry**: 25+ ancestry groups including German, Irish, Mexican, Chinese, Indian, Vietnamese, and more

## Quick Start

1. **Setup Environment**:
   ```bash
   cd dfw_demographic_evolution
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Collect Data** (optional - data already included):
   ```bash
   python census_data_collector_simple.py
   ```

3. **Run Analysis**:
   ```bash
   python analyze_demographics.py
   ```

4. **View Interactive Maps**:
   ```bash
   python serve_maps.py
   ```
   This will start a local web server and open the dashboard in your browser.

## Files Overview

### Data Collection
- `census_data_collector_simple.py` - Main data collection script
- `census_data_collector.py` - Alternative comprehensive collector

### Analysis
- `analyze_demographics.py` - Statistical analysis and reporting
- `create_map_visualization.py` - Interactive map generation

### Visualizations
- `dfw_demographic_dashboard.html` - Main interactive dashboard
- `dfw_demographic_map.html` - Detailed demographic map
- `dfw_population_timeline.html` - Population growth timeline
- `serve_maps.py` - Local web server for viewing maps

### Data Files
- `dfw_major_cities_demographics_*.csv` - Raw collected data
- `dfw_demographics_cleaned.csv` - Processed and cleaned data

## Key Findings

### Population Growth (2009-2022)
- **Overall metro growth**: 19.8% (924,180 people added)
- **Fastest growing cities**:
  1. Frisco: 130.4% growth (+114,363 people)
  2. McKinney: 72.7% growth (+82,554 people)
  3. Mansfield: 71.5% growth (+30,722 people)

### Demographic Trends
- **Increasing diversity** across all major cities
- **Asian population growth** particularly in Plano (14.9% → 22.7%)
- **Hispanic population** remains stable in Dallas (~42%)
- **White population** declining in most urban centers
- **Suburban growth** outpacing urban core growth

### Interactive Features
- **Layer Toggle**: Switch between 2009/2022 demographics and growth patterns
- **Detailed Popups**: Click any city for comprehensive demographic breakdowns
- **Timeline View**: See population changes across multiple years
- **Growth Visualization**: Color-coded cities by growth rate with legend

## Technical Details

### Census API Integration
- Automated data collection with error handling and rate limiting
- Support for Census API keys (recommended for large datasets)
- Comprehensive variable mapping for demographic categories

### Visualization Technology
- **Folium** for interactive Leaflet.js maps
- **Pandas** for data processing and analysis
- **HTML/CSS/JavaScript** for dashboard interface
- **Responsive design** for desktop and mobile viewing

## Requirements
- Python 3.7+
- Internet connection for Census API access (data collection)
- Modern web browser for viewing visualizations

## Optional: Census API Key
For faster data collection, get a free API key at: https://api.census.gov/data/key_signup.html

## Usage Examples

### View Specific City Trends
```python
# Load and filter data
df = pd.read_csv('dfw_demographics_cleaned.csv')
dallas_data = df[df['city'] == 'Dallas city']
print(dallas_data[['year', 'total_population', 'hispanic_pct']])
```

### Custom Analysis
```python
# Calculate diversity index
df['diversity_index'] = 1 - (
    (df['white_pct']/100)**2 + 
    (df['black_pct']/100)**2 + 
    (df['asian_pct']/100)**2 + 
    (df['hispanic_pct']/100)**2
)
```

## Contributing
Feel free to extend the analysis, add new visualizations, or include additional demographic variables. The modular design makes it easy to customize for other metropolitan areas or time periods.
