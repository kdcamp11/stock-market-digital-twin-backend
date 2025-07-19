#!/usr/bin/env python3
"""
Standalone runner for the Stock Market Digital Twin API
This file handles the import issues and runs the API server
"""

import sys
import os
import uvicorn

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set environment variables if needed
os.environ.setdefault('PYTHONPATH', current_dir)

if __name__ == "__main__":
    # Import and run the FastAPI app
    try:
        from modeling.api import app
        print("✅ Successfully imported FastAPI app from modeling.api")
        
        print("🚀 Starting Stock Market Digital Twin API server...")
        print("📊 Available endpoints:")
        print("  - GET  /api/decision - Agent decision making")
        print("  - GET  /api/realtime/{symbol} - Real-time quotes")
        print("  - POST /api/add_ticker - Add new ticker")
        print("  - POST /api/update_all_tickers - Update all tickers")
        print("  - GET  /api/technical/{symbol} - Technical analysis")
        print("  - GET  /api/backtest/{symbol} - Backtest results")
        print("  - GET  /api/chart/{symbol} - Chart data with indicators")
        print("  - GET  /api/options/{symbol} - Options chain")
        print("  - GET  /api/options/analysis/{symbol} - Options analysis")
        print("  - GET  /api/options/strategies/{symbol} - Options strategies")
        print("  - WebSocket /ws/realtime - Live price streaming")
        print()
        print("🌐 Server will be available at: http://localhost:8000")
        print("📖 API docs available at: http://localhost:8000/docs")
        print()
        
        # Run the server
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            reload=False,  # Disable reload to avoid import issues
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you have all required dependencies installed:")
        print("   pip install fastapi uvicorn pandas alpaca-py pandas-ta")
        print("2. Set your Alpaca API credentials:")
        print("   export ALPACA_API_KEY='your_api_key'")
        print("   export ALPACA_API_SECRET='your_api_secret'")
        print("3. Make sure the database file exists:")
        print("   Check: data_ingestion/stocks.db")
        sys.exit(1)
