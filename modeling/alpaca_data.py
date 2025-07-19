"""
Alpaca Market Data API Integration
Complete replacement for Yahoo Finance data
"""
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3

try:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import (
        StockBarsRequest, StockLatestQuoteRequest, StockLatestTradeRequest,
        StockQuotesRequest, StockTradesRequest
    )
    from alpaca.data.timeframe import TimeFrame
    from alpaca.data.live import StockDataStream
except ImportError:
    print("alpaca-py not installed. Please install with: pip install alpaca-py")
    StockHistoricalDataClient = None

class AlpacaDataProvider:
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.environ.get('ALPACA_API_KEY')
        self.api_secret = api_secret or os.environ.get('ALPACA_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API credentials not found. Set ALPACA_API_KEY and ALPACA_API_SECRET environment variables.")
        
        if StockHistoricalDataClient is None:
            raise ImportError("alpaca-py not installed. Please install with: pip install alpaca-py")
            
        # Initialize the client with proper configuration
        try:
            self.client = StockHistoricalDataClient(self.api_key, self.api_secret)
            print(f"✅ Alpaca client initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Alpaca client: {e}")
            raise
        
    def get_historical_bars(self, 
                           symbol: str, 
                           start_date: str = None, 
                           end_date: str = None,
                           timeframe: str = "1Day") -> pd.DataFrame:
        """
        Get historical bar data from Alpaca
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date in YYYY-MM-DD format (default: 2 years ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            timeframe: Bar timeframe ('1Day', '1Hour', '1Min', etc.)
        
        Returns:
            DataFrame with OHLCV data
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        # Map timeframe string to Alpaca TimeFrame
        timeframe_map = {
            "1Min": TimeFrame.Minute,
            "5Min": TimeFrame(5, "Minute"),
            "15Min": TimeFrame(15, "Minute"),
            "1Hour": TimeFrame.Hour,
            "1Day": TimeFrame.Day,
            "1Week": TimeFrame.Week,
            "1Month": TimeFrame.Month
        }
        
        tf = timeframe_map.get(timeframe, TimeFrame.Day)
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=datetime.strptime(start_date, '%Y-%m-%d'),
            end=datetime.strptime(end_date, '%Y-%m-%d')
        )
        
        bars = self.client.get_stock_bars(request)
        
        if symbol not in bars:
            return pd.DataFrame()
            
        # Convert to DataFrame
        data = []
        for bar in bars[symbol]:
            data.append({
                'Date': bar.timestamp.date(),
                'Open': float(bar.open),
                'High': float(bar.high),
                'Low': float(bar.low),
                'Close': float(bar.close),
                'Volume': int(bar.volume)
            })
            
        df = pd.DataFrame(data)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').reset_index(drop=True)
            
        return df
    
    def get_latest_quote(self, symbol: str) -> Dict:
        """Get the latest quote for a symbol"""
        request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quotes = self.client.get_stock_latest_quote(request)
        
        if symbol not in quotes:
            return None
            
        quote = quotes[symbol]
        return {
            'symbol': symbol,
            'ask_price': float(quote.ask_price) if quote.ask_price else None,
            'bid_price': float(quote.bid_price) if quote.bid_price else None,
            'ask_size': int(quote.ask_size) if quote.ask_size else None,
            'bid_size': int(quote.bid_size) if quote.bid_size else None,
            'timestamp': quote.timestamp
        }
    
    def get_latest_trade(self, symbol: str) -> Dict:
        """Get the latest trade for a symbol"""
        request = StockLatestTradeRequest(symbol_or_symbols=symbol)
        trades = self.client.get_stock_latest_trade(request)
        
        if symbol not in trades:
            return None
            
        trade = trades[symbol]
        return {
            'symbol': symbol,
            'price': float(trade.price),
            'size': int(trade.size),
            'timestamp': trade.timestamp
        }
    
    def update_database_with_alpaca_data(self, 
                                       db_path: str, 
                                       symbols: List[str] = None,
                                       start_date: str = None) -> Dict:
        """
        Update SQLite database with fresh Alpaca data
        
        Args:
            db_path: Path to SQLite database
            symbols: List of symbols to update (if None, updates all existing symbols)
            start_date: Start date for historical data (default: 2 years ago)
        
        Returns:
            Dict with update results
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing symbols if none provided
        if symbols is None:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
            symbols = [row[0] for row in cursor.fetchall()]
        
        results = {
            'updated': [],
            'failed': [],
            'total_rows': 0
        }
        
        for symbol in symbols:
            try:
                print(f"Updating {symbol} with Alpaca data...")
                
                # Get historical data from Alpaca
                df = self.get_historical_bars(symbol, start_date=start_date)
                
                if df.empty:
                    results['failed'].append(f"{symbol}: No data available")
                    continue
                
                # Ensure Date column is string for SQLite compatibility
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                
                # Replace existing data
                df.to_sql(symbol, conn, if_exists='replace', index=False)
                
                results['updated'].append(f"{symbol}: {len(df)} rows")
                results['total_rows'] += len(df)
                
            except Exception as e:
                results['failed'].append(f"{symbol}: {str(e)}")
                continue
        
        conn.close()
        return results
    
    def add_new_symbol_to_database(self, 
                                 db_path: str, 
                                 symbol: str,
                                 start_date: str = None) -> Dict:
        """
        Add a new symbol to the database with Alpaca data
        
        Args:
            db_path: Path to SQLite database
            symbol: Symbol to add
            start_date: Start date for historical data
        
        Returns:
            Dict with operation result
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if symbol already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (symbol,))
        if cursor.fetchone():
            conn.close()
            return {"status": "exists", "message": f"{symbol} already in database."}
        
        try:
            # Get historical data from Alpaca
            df = self.get_historical_bars(symbol, start_date=start_date)
            
            if df.empty:
                conn.close()
                return {"status": "error", "message": f"No data found for {symbol} on Alpaca."}
            
            # Ensure Date column is string for SQLite compatibility
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
            
            # Save to database
            df.to_sql(symbol, conn, if_exists='replace', index=False)
            conn.close()
            
            return {
                "status": "success", 
                "message": f"{symbol} added to database with Alpaca data.", 
                "rows": len(df)
            }
            
        except Exception as e:
            conn.close()
            return {"status": "error", "message": str(e)}

class AlpacaStreamingData:
    """
    Alpaca real-time streaming data handler
    """
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.environ.get('ALPACA_API_KEY')
        self.api_secret = api_secret or os.environ.get('ALPACA_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca API credentials not found.")
        
        try:
            self.stream = StockDataStream(self.api_key, self.api_secret)
        except Exception as e:
            print(f"Could not initialize Alpaca streaming: {e}")
            self.stream = None
    
    def setup_quote_handler(self, callback_func):
        """Setup handler for real-time quotes"""
        if self.stream:
            @self.stream.on_quote
            async def quote_handler(quote):
                await callback_func(quote)
    
    def setup_trade_handler(self, callback_func):
        """Setup handler for real-time trades"""
        if self.stream:
            @self.stream.on_trade
            async def trade_handler(trade):
                await callback_func(trade)
    
    def subscribe_to_symbols(self, symbols: List[str]):
        """Subscribe to real-time data for symbols"""
        if self.stream:
            self.stream.subscribe_quotes(*symbols)
            self.stream.subscribe_trades(*symbols)
    
    async def start_streaming(self):
        """Start the streaming connection"""
        if self.stream:
            await self.stream._run_forever()

# Convenience functions for backward compatibility
def get_alpaca_data_provider():
    """Get an instance of AlpacaDataProvider"""
    try:
        return AlpacaDataProvider()
    except Exception as e:
        print(f"Could not initialize Alpaca data provider: {e}")
        return None

def update_all_tickers_with_alpaca(db_path: str):
    """Update all tickers in database with fresh Alpaca data"""
    provider = get_alpaca_data_provider()
    if provider:
        return provider.update_database_with_alpaca_data(db_path)
    return {"error": "Could not initialize Alpaca provider"}
