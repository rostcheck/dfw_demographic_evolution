#!/usr/bin/env python3
"""
Simple web server to serve the North Texas demographic visualizations
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

def start_server(port=8000):
    """Start a simple HTTP server to serve the visualization files"""
    
    # Change to the project directory
    os.chdir(Path(__file__).parent)
    
    # Check which dashboard files exist
    dashboard_files = []
    if Path('north_texas_cities_dashboard.html').exists():
        dashboard_files.append(('north_texas_cities_dashboard.html', 'North Texas Cities Dashboard (Latest)'))
    if Path('north_texas_expanded_dashboard.html').exists():
        dashboard_files.append(('north_texas_expanded_dashboard.html', 'Expanded Dashboard'))
    if Path('dfw_demographic_dashboard.html').exists():
        dashboard_files.append(('dfw_demographic_dashboard.html', 'Original Dashboard (32 cities)'))
    
    # Determine the best dashboard to use
    primary_dashboard = dashboard_files[0][0] if dashboard_files else 'index.html'
    
    # Create server
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"🌐 Starting web server at http://localhost:{port}")
            print(f"📊 Primary Dashboard: http://localhost:{port}/{primary_dashboard}")
            
            if len(dashboard_files) > 1:
                print(f"🗂️  All available dashboards:")
                for filename, description in dashboard_files:
                    print(f"   • {description}: http://localhost:{port}/{filename}")
            
            print(f"🗺️  Direct map files:")
            if Path('north_texas_cities_map.html').exists():
                print(f"   • North Texas Cities Map: http://localhost:{port}/north_texas_cities_map.html")
            if Path('dfw_demographic_map.html').exists():
                print(f"   • Original Map: http://localhost:{port}/dfw_demographic_map.html")
            
            print(f"\n💡 Press Ctrl+C to stop the server")
            
            # Try to open the primary dashboard in the default browser
            try:
                webbrowser.open(f'http://localhost:{port}/{primary_dashboard}')
                print(f"🚀 Opening {primary_dashboard} in your default browser...")
            except:
                print(f"⚠️  Could not auto-open browser. Please manually navigate to the URL above.")
            
            print(f"\n🔄 Server running... (serving files from {os.getcwd()})")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped.")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Trying port {port + 1}...")
            start_server(port + 1)
        else:
            print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    start_server()
