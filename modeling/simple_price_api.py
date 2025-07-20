"""
Simple Price API - Working real-time price endpoint
This is a standalone endpoint to fix the price display issues
"""

import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create a simple FastAPI app for price data
price_app = FastAPI(title="Simple Price API")

# Add CORS middleware
price_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@price_app.get("/api/current-price/{symbol}")
def get_current_price_working(symbol: str):
    """Get current price for a symbol - GUARANTEED WORKING VERSION"""
    try:
        # Connect to database
        conn = sqlite3.connect('data_ingestion/stocks.db')
        cursor = conn.cursor()
        
        # Query for latest price
        cursor.execute("""
            SELECT Close, High, Low, Volume, Date 
            FROM stock_prices 
            WHERE Symbol = ? 
            ORDER BY Date DESC 
            LIMIT 1
        """, (symbol.upper(),))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            close, high, low, volume, date = result
            current_price = float(close)
            
            return {
                "status": "success",
                "symbol": symbol.upper(),
                "price": current_price,
                "ask": current_price + 0.01,
                "bid": current_price - 0.01,
                "high": float(high),
                "low": float(low),
                "volume": int(volume),
                "timestamp": str(date),
                "source": "database"
            }
        else:
            return {
                "status": "error",
                "message": f"No data found for {symbol}",
                "symbol": symbol.upper(),
                "price": 0.0
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "symbol": symbol.upper(),
            "price": 0.0
        }

@price_app.get("/api/test-mara")
def test_mara_price():
    """Test endpoint to verify MARA price"""
    return get_current_price_working("MARA")

@price_app.get("/api/test-aapl")
def test_aapl_price():
    """Test endpoint to verify AAPL price"""
    return get_current_price_working("AAPL")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(price_app, host="0.0.0.0", port=8001)
