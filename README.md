# DFW Demographic Evolution

This project collects and analyzes demographic data for cities in the Dallas-Fort Worth metropolitan area over the past 20 years using U.S. Census Bureau data, with interactive web-based visualizations.

![UI screenshot](blog/screenshot.jpg)

## Features

- **Data Collection**: Automated Census API data collection for cities in specified counties
- **Analysis**: Population growth, demographic composition, and ancestry trend analysis
- **Interactive Maps**: Web-based visualizations showing demographic changes over time
- **Dashboard**: Comprehensive HTML dashboard with multiple visualization layers

## Data Sources
- U.S. Census Bureau American Community Survey (ACS) 5-Year Estimates
- Years covered: 2009-2022
- Geographic coverage: 11 North Texas counties

## Counties Included
- Dallas County
- Tarrant County (Fort Worth)
- Collin County
- Denton County
- Grayson County (Sherman)
- Rockwall County
- Ellis County
- Johnson County
- Kaufman County
- Parker County
- Wise County

## Data Displayed
- **Population**: Total population by city over time
- **Racial Makeup**: Shows population percent identifying as: White, Black, Asian, Hispanic/Latino, Other


## Quick Start

1. **Setup Environment**:
   ```bash
   cd dfw_demographic_evolution
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **View Existing Visualizations**:
   ```bash
   python serve_maps.py
   ```

3. **Collect New Data** (optional - clean data already included):
   ```bash
   python collect_data.py
   ```

4. **Generate Visualizations**:
   ```bash
   python create_visualization.py
   ```

5. **View Interactive Maps**:
   ```bash
   python serve_maps.py
   ```
   This will start a local web server and open the dashboard in your browser.

## Files Overview

### Core Scripts
- `collect_data.py` - Main data collection script with resume capability
- `create_visualization.py` - Interactive map and dashboard generation
- `serve_maps.py` - Local web server for viewing visualizations

### Utilities
- `setup_api_key.py` - Census API key configuration helper

### Generated Visualizations
- `north_texas_cities_dashboard.html` - Main interactive dashboard
- `north_texas_cities_map.html` - Interactive demographic map

### Configuration
- **`counties.json`** - County configuration file defining target counties

### Data Files
- `north_texas_county_demographics.csv` - Complete demographic dataset for all DFW cities

## Configuration File

The project uses a JSON configuration file (`counties.json`) to define which counties to include in data collection:

```json
{
  "north_texas_counties": {
    "Dallas": "113",
    "Tarrant": "439", 
    "Collin": "085",
    "Denton": "121",
    "Grayson": "181",
    "Rockwall": "397",
    "Ellis": "139",
    "Johnson": "251",
    "Kaufman": "257",
    "Parker": "367",
    "Wise": "497"
  }
}
```

### Configuration Structure
- **County Names**: Human-readable county names (e.g., "Dallas", "Tarrant")
- **FIPS Codes**: Census Bureau county FIPS codes for API queries
- **Automatic Discovery**: The collector queries all incorporated places within each county

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

For faster and more reliable data collection, get a free API key at: https://api.census.gov/data/key_signup.html

### Setting up the API Key

**Option 1: Environment Variable (Recommended)**
```bash
export CENSUS_API_KEY="your_api_key_here"
```

**Option 2: Interactive Prompt**
The collector will prompt you for the API key if not found in the environment.

### Benefits of Using an API Key
- 5x faster data collection
- Reduced timeout errors  
- Higher success rate for large datasets
- No rate limiting delays

### Licensing
This project is open-source, licensed under the MIT license. Data files are public works from the U.S. census.

### AI disclosure
The project was built by Amazon Q Developer CLI running Anthropic Claude 4 Sonnet.
