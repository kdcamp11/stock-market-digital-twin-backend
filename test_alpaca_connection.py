#!/usr/bin/env python3
"""
Test Alpaca API Connection
Simple script to test if Alpaca API credentials are working correctly
"""

import os
import sys

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")

# Load .env file
load_env_file()

def test_alpaca_connection():
    """Test basic Alpaca API connection"""
    print("🧪 Testing Alpaca API Connection")
    print("=" * 40)
    
    # Check credentials
    api_key = os.getenv('ALPACA_API_KEY')
    api_secret = os.getenv('ALPACA_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Alpaca API credentials not found!")
        print("Please check your .env file")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...")
    print(f"✅ API Secret found: {api_secret[:8]}...")
    
    try:
        # Test with alpaca-py library
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        from datetime import datetime, timedelta
        
        print("✅ alpaca-py library imported successfully")
        
        # Initialize client
        client = StockHistoricalDataClient(api_key, api_secret)
        print("✅ Alpaca client initialized")
        
        # Test with a simple request for recent data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)  # Just 5 days of data
        
        print(f"📅 Testing data request for AAPL from {start_date.date()} to {end_date.date()}")
        
        request_params = StockBarsRequest(
            symbol_or_symbols=["AAPL"],
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )
        
        # Make the API call
        bars = client.get_stock_bars(request_params)
        
        if bars and bars.df is not None and not bars.df.empty:
            print("✅ Successfully retrieved data from Alpaca!")
            print(f"📊 Retrieved {len(bars.df)} bars for AAPL")
            print("\n📈 Sample data:")
            print(bars.df.head())
            return True
        else:
            print("⚠️  API call succeeded but no data returned")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install alpaca-py: pip install alpaca-py")
        return False
        
    except Exception as e:
        print(f"❌ Error testing Alpaca connection: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Check if it's a 403 error specifically
        if "403" in str(e) or "Forbidden" in str(e):
            print("\n🔍 403 Forbidden Error Troubleshooting:")
            print("1. Check if your API keys are for paper trading or live trading")
            print("2. Verify your API keys have market data permissions")
            print("3. Check if your Alpaca account has data subscription")
            print("4. Try using paper trading endpoints if using paper keys")
            
        return False

def test_alternative_approach():
    """Test alternative approach using requests library"""
    print("\n🔄 Testing alternative approach with requests...")
    
    try:
        import requests
        import base64
        
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_API_SECRET')
        
        # Try the basic account info endpoint first
        headers = {
            'APCA-API-KEY-ID': api_key,
            'APCA-API-SECRET-KEY': api_secret
        }
        
        # Test with paper trading URL first
        base_url = "https://paper-api.alpaca.markets"
        
        print(f"🌐 Testing connection to {base_url}")
        
        response = requests.get(f"{base_url}/v2/account", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Successfully connected to Alpaca paper trading API!")
            account_info = response.json()
            print(f"📊 Account status: {account_info.get('status', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed to connect: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            # Try live trading URL
            base_url = "https://api.alpaca.markets"
            print(f"🌐 Testing connection to {base_url}")
            
            response = requests.get(f"{base_url}/v2/account", headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ Successfully connected to Alpaca live trading API!")
                return True
            else:
                print(f"❌ Failed to connect to live API: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error with alternative approach: {e}")
        return False

if __name__ == "__main__":
    print("🏦 Alpaca API Connection Test")
    print("=" * 50)
    
    success = test_alpaca_connection()
    
    if not success:
        print("\n" + "=" * 50)
        test_alternative_approach()
    
    print("\n🎯 Recommendations:")
    if success:
        print("✅ Your Alpaca API is working! You can proceed with data ingestion.")
    else:
        print("❌ API connection failed. Please:")
        print("1. Verify your API keys are correct")
        print("2. Check if you need paper trading vs live trading endpoints")
        print("3. Ensure your account has market data permissions")
        print("4. Contact Alpaca support if issues persist")
