#!/usr/bin/env python3
"""
Fresh Data Ingestion Script for Stock Market Digital Twin
Fetches current market data from Alpaca and updates the local database
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

def setup_database():
    """Ensure database has the correct schema"""
    db_path = os.path.join(os.path.dirname(__file__), "data_ingestion", "stocks.db")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist (matching existing schema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            Date TEXT,
            Open REAL,
            High REAL,
            Low REAL,
            Close REAL,
            Adj_Close REAL,
            Volume INTEGER,
            Symbol TEXT,
            PRIMARY KEY (Date, Symbol)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database setup complete: {db_path}")
    return db_path

def ingest_alpaca_data(symbols=None, days_back=30):
    """Ingest fresh data from Alpaca API"""
    if symbols is None:
        symbols = ['AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN', 'META', 'NVDA', 'SPY', 'QQQ']
    
    print(f"🚀 Starting fresh data ingestion for {len(symbols)} symbols...")
    
    try:
        # Use direct alpaca-py library like in the successful test
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_API_SECRET')
        
        if not api_key or not api_secret:
            print("❌ Alpaca API credentials not available. Please set ALPACA_API_KEY and ALPACA_API_SECRET environment variables.")
            return False
        
        # Initialize client directly (same as successful test)
        client = StockHistoricalDataClient(api_key, api_secret)
        print("✅ Alpaca client initialized successfully")
        
        db_path = setup_database()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"📅 Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        success_count = 0
        for symbol in symbols:
            try:
                print(f"📈 Fetching {symbol}...")
                
                # Get historical bars from Alpaca (same pattern as successful test)
                request_params = StockBarsRequest(
                    symbol_or_symbols=[symbol],
                    timeframe=TimeFrame.Day,
                    start=start_date,
                    end=end_date
                )
                
                bars = client.get_stock_bars(request_params)
                df = bars.df if bars and bars.df is not None else pd.DataFrame()
                
                if df.empty:
                    print(f"⚠️  No data found for {symbol}")
                    continue
                
                # Prepare data for database insertion
                # Reset index to get timestamp as a column
                df = df.reset_index()
                
                # Handle multi-index columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(0)  # Remove symbol level
                
                # Rename columns to match database schema
                column_mapping = {
                    'timestamp': 'Date',
                    'open': 'Open',
                    'high': 'High', 
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }
                df = df.rename(columns=column_mapping)
                
                # Add required columns
                df['Symbol'] = symbol
                df['Adj_Close'] = df['Close']  # Alpaca doesn't provide adjusted close, use close
                
                # Format date properly
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    print(f"⚠️  Warning: No Date column found for {symbol}. Columns: {list(df.columns)}")
                    continue
                
                # Insert into database
                conn = sqlite3.connect(db_path)
                
                # Delete existing data for this symbol in the date range
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM stock_prices 
                    WHERE Symbol = ? AND Date >= ? AND Date <= ?
                """, (symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                
                # Insert new data
                df[['Date', 'Open', 'High', 'Low', 'Close', 'Adj_Close', 'Volume', 'Symbol']].to_sql(
                    'stock_prices', conn, if_exists='append', index=False
                )
                
                conn.commit()
                conn.close()
                
                print(f"✅ {symbol}: {len(df)} records inserted")
                success_count += 1
                
            except Exception as e:
                print(f"❌ Error fetching {symbol}: {e}")
                continue
        
        print(f"\n🎉 Data ingestion complete! Successfully updated {success_count}/{len(symbols)} symbols")
        
        # Show sample of latest data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Symbol, Date, Close 
            FROM stock_prices 
            ORDER BY Date DESC, Symbol 
            LIMIT 10
        """)
        
        print("\n📊 Latest data sample:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: ${row[2]:.2f} on {row[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error during data ingestion: {e}")
        return False

def main():
    """Main function"""
    print("🏦 Stock Market Digital Twin - Fresh Data Ingestion")
    print("=" * 50)
    
    # Check for environment variables
    if not os.getenv('ALPACA_API_KEY') or not os.getenv('ALPACA_API_SECRET'):
        print("⚠️  Alpaca API credentials not found in environment variables.")
        print("   Please set ALPACA_API_KEY and ALPACA_API_SECRET")
        print("   You can copy them from your Render deployment environment.")
        print()
        print("   Example:")
        print("   export ALPACA_API_KEY='your_key_here'")
        print("   export ALPACA_API_SECRET='your_secret_here'")
        print()
        return
    
    # Run data ingestion
    success = ingest_alpaca_data()
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Restart your backend server to use the fresh data")
        print("2. Refresh your frontend to see current 2025 prices")
        print("3. Test the Technical Analysis tab with fresh data")
    else:
        print("\n❌ Data ingestion failed. Please check your Alpaca credentials and try again.")

if __name__ == "__main__":
    main()
