#!/usr/bin/env python3
"""
Helper script to set up Census API key environment variable
"""

import os

def setup_api_key():
    """Help user set up the Census API key"""
    print("🔑 CENSUS API KEY SETUP")
    print("=" * 30)
    
    # Check if already set
    existing_key = os.getenv('CENSUS_API_KEY')
    if existing_key:
        print(f"✅ CENSUS_API_KEY is already set!")
        print(f"   Key: {existing_key[:8]}...{existing_key[-4:]} (masked)")
        
        change = input("\nDo you want to change it? (y/n): ").lower().strip()
        if change != 'y':
            print("👍 Keeping existing API key")
            return
    
    print("\n📝 To set up your Census API key:")
    print("1. Get a free API key at: https://api.census.gov/data/key_signup.html")
    print("2. Enter it below")
    print("3. The key will be saved for this session")
    
    api_key = input("\nEnter your Census API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return
    
    # Set for current session
    os.environ['CENSUS_API_KEY'] = api_key
    print(f"✅ API key set for this session!")
    
    # Show how to set permanently
    print(f"\n💡 To set permanently, add this to your shell profile:")
    print(f"   export CENSUS_API_KEY='{api_key}'")
    print(f"\n   For bash: echo 'export CENSUS_API_KEY=\"{api_key}\"' >> ~/.bashrc")
    print(f"   For zsh:  echo 'export CENSUS_API_KEY=\"{api_key}\"' >> ~/.zshrc")
    
    # Test the key
    print(f"\n🧪 Testing API key...")
    try:
        import requests
        test_url = "https://api.census.gov/data/2022/acs/acs5"
        params = {
            'get': 'NAME,B01003_001E',
            'for': 'place:19000',  # Dallas
            'in': 'state:48',
            'key': api_key
        }
        
        response = requests.get(test_url, params=params, timeout=10)
        if response.status_code == 200:
            print("✅ API key is valid and working!")
        else:
            print(f"⚠️ API key test failed: {response.status_code}")
            print("   The key might still work, but there was an issue with the test")
    except Exception as e:
        print(f"⚠️ Could not test API key: {e}")
        print("   The key might still work")
    
    print(f"\n🚀 Ready to run: python incremental_collector.py")

if __name__ == "__main__":
    setup_api_key()
