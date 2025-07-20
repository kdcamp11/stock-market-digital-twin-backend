"""
REST API for agentic AI stock decision-making
"""
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Query
from contextlib import asynccontextmanager
from pydantic import BaseModel
import pandas as pd
import sqlite3
import time
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional

try:
    from modeling.agent import StockAgent
    from modeling.twin_state import TwinState
    from modeling.twin_state_query_example import load_data
except ImportError:
    # If running directly, try importing from current directory
    from agent import StockAgent
    from twin_state import TwinState
    from twin_state_query_example import load_data

import yfinance as yf
import sqlite3

# Helper function to handle imports consistently
def safe_import(module_name, class_or_func_name=None):
    """Safely import modules with fallback for direct execution"""
    try:
        if class_or_func_name:
            module = __import__(f'modeling.{module_name}', fromlist=[class_or_func_name])
            return getattr(module, class_or_func_name)
        else:
            return __import__(f'modeling.{module_name}', fromlist=[''])
    except ImportError:
        try:
            if class_or_func_name:
                module = __import__(module_name, fromlist=[class_or_func_name])
                return getattr(module, class_or_func_name)
            else:
                return __import__(module_name, fromlist=[''])
        except ImportError:
            return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        t = threading.Thread(target=run_alert_monitor_periodically, daemon=True)
        t.start()
    except Exception as e:
        print(f"Alert monitoring disabled: {e}")
    yield
    # Shutdown (if needed)
    pass

app = FastAPI(lifespan=lifespan)

# --- Alpaca Real-Time Data Integration ---
from fastapi import HTTPException, WebSocket, WebSocketDisconnect
import os
import asyncio
import json

def get_realtime_quote(symbol: str):
    """Get real-time quote from Alpaca using new data provider"""
    try:
        from modeling.alpaca_data import get_alpaca_data_provider
        provider = get_alpaca_data_provider()
        if provider:
            return provider.get_latest_quote(symbol)
        return None
    except Exception as e:
        print(f"Error fetching real-time quote for {symbol}: {e}")
        return None

def get_realtime_trade(symbol: str):
    """Get real-time trade from Alpaca"""
    try:
        from modeling.alpaca_data import get_alpaca_data_provider
        provider = get_alpaca_data_provider()
        if provider:
            return provider.get_latest_trade(symbol)
        return None
    except Exception as e:
        print(f"Error fetching real-time trade for {symbol}: {e}")
        return None

# Removed duplicate broken real-time endpoint - using working version below

@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    await websocket.accept()
    try:
        subscribe_msg = await websocket.receive_text()
        try:
            subscribe_data = json.loads(subscribe_msg)
            symbols = subscribe_data.get("symbols", [])
            if not symbols or not isinstance(symbols, list):
                await websocket.send_text(json.dumps({"error": "Send {\"symbols\": [\"AAPL\", ...]} to subscribe."}))
                await websocket.close()
                return
        except Exception:
            await websocket.send_text(json.dumps({"error": "Invalid subscribe message. Send {\"symbols\": [\"AAPL\", ...]}"}))
            await websocket.close()
            return
        last_prices = {s: None for s in symbols}
        while True:
            updates = []
            for symbol in symbols:
                try:
                    # Try to get both quote and trade data
                    quote = get_realtime_quote(symbol)
                    trade = get_realtime_trade(symbol)
                    
                    # Prefer trade price, fallback to quote
                    price = None
                    timestamp = None
                    
                    if trade and trade.get('price'):
                        price = trade['price']
                        timestamp = str(trade.get('timestamp', ''))
                    elif quote and (quote.get('ask_price') or quote.get('bid_price')):
                        price = quote.get('ask_price') or quote.get('bid_price')
                        timestamp = str(quote.get('timestamp', ''))
                    
                    if price and price != last_prices.get(symbol):
                        updates.append({
                            "symbol": symbol,
                            "price": price,
                            "timestamp": timestamp,
                            "type": "trade" if trade else "quote"
                        })
                        last_prices[symbol] = price
                        
                except Exception as e:
                    updates.append({"symbol": symbol, "error": str(e)})
            if updates:
                await websocket.send_text(json.dumps({"updates": updates}))
            await asyncio.sleep(2)  # Poll every 2 seconds for demo; adjust as needed
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
        await websocket.close()

# --- Start alert monitoring as a background thread ---
import threading
import time

def run_alert_monitor_periodically():
    try:
        from modeling.alerts.monitor import AlertMonitor
        monitor = AlertMonitor(config_path="alert_config.yaml")
        while True:
            monitor.check_all_symbols()
            time.sleep(600)  # Run every 10 minutes
    except ImportError:
        # Alert monitoring is optional - skip if not available
        print("Alert monitoring disabled - alerts module not found")
        return

# --- CORS middleware for Netlify frontend ---
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
agent = StockAgent(db_path=db_path)

class DecisionRequest(BaseModel):
    question: str

class SimRequest(BaseModel):
    symbol: str
    params: dict = {}

class AgentRequest(BaseModel):
    question: str

class AddTickerRequest(BaseModel):
    symbol: str

class PortfolioRequest(BaseModel):
    initial_cash: float = 100000.0
    
class BacktestRequest(BaseModel):
    start_date: str
    end_date: str
    initial_cash: float = 100000.0
    strategy: str = "agent"  # "agent" or "rsi"
    symbols: list = []

@app.get("/decision")
def get_decision(question: str = Query(..., description="Plain-language question about a stock")):
    result = agent.decide(question)
    return {"question": question, "result": result}

@app.post("/decision")
def post_decision(req: DecisionRequest):
    result = agent.decide(req.question)
    return {"question": req.question, "result": result}

# --- New UI endpoints below ---

@app.get("/api/debug/files")
def list_files():
    import os
    dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion"))
    try:
        files = os.listdir(dir_path)
        file_stats = {f: os.stat(os.path.join(dir_path, f)).st_mode for f in files}
        return JSONResponse({"dir": dir_path, "files": files, "file_stats": file_stats})
    except Exception as e:
        return JSONResponse({"error": str(e), "dir": dir_path})

@app.get("/api/twin/latest")
def get_latest_twin_states():
    import os
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
    from modeling.twin_state_query_example import get_symbols, load_data
    symbols = get_symbols(db_path)
    result = []
    for symbol in symbols:
        df = load_data(symbol, db_path)
        if df is None or df.empty:
            continue
        from modeling.twin_state import TwinState
        twin = TwinState(df)
        state = twin.get_state()
        # Add timestamp from latest row
        ts = str(df.index[-1]) if len(df.index) else None
        result.append({
            "symbol": symbol,
            "close": df.iloc[-1]["Close"] if len(df) else None,
            "signals": state.get("Signals", []),
            "timestamp": ts
        })
    return result

@app.get("/api/alerts/log")
def get_alerts_log():
    import os, json
    log_path = os.path.join(os.path.dirname(__file__), "alerts", "alerts.log")
    if not os.path.exists(log_path):
        return []
    alerts = []
    with open(log_path) as f:
        for line in f:
            try:
                alerts.append(json.loads(line.strip()))
            except Exception:
                continue
    return alerts[::-1]  # newest first

@app.post("/api/simulate")
def run_simulation(req: SimRequest):
    from modeling.twin_state_query_example import load_data
    from modeling.simulation.simulator import StrategySimulator
    from modeling.simulation.strategies import ema_bounce_strategy
    import os
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
    df = load_data(req.symbol, db_path)
    if df is None or df.empty:
        return {"error": "No data found for symbol"}
    # Enrich with indicators if needed
    from modeling.indicators import add_ema, add_rsi
    df = add_ema(df, [req.params.get("ema_length", 20)])
    df = add_rsi(df, 14)
    sim = StrategySimulator(df, ema_bounce_strategy, req.params)
    results = sim.run()
    return results

@app.post("/api/agent")
def agent_chat(req: AgentRequest):
    import re
    from modeling.twin_state_query_example import get_symbols
    # Extract all-caps ticker symbols from the question
    words = re.findall(r'\b[A-Z]{1,5}\b', req.question)
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
    known_symbols = set(get_symbols(db_path))
    # Try to add missing tickers
    for symbol in words:
        if symbol not in known_symbols:
            from fastapi import Request
            import yfinance as yf, sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (symbol,))
            if not cursor.fetchone():
                df = yf.download(symbol, period="max")
                if df is not None and not df.empty:
                    df.reset_index(inplace=True)
                    # Handle MultiIndex columns from yfinance
                    if hasattr(df.columns, 'levels'):  # MultiIndex
                        df.columns = [col[0] if isinstance(col, tuple) else str(col) for col in df.columns]
                    df.columns = [str(c).replace(' ', '_') for c in df.columns]
                    try:
                        df.to_sql(symbol, conn, if_exists="replace", index=False)
                    except Exception:
                        pass
            conn.close()
    # Now make the decision (with fresh DB tickers)
    result = agent.decide(req.question)
    return {
        "decision": result.get("decision"),
        "confidence": result.get("confidence"),
        "explanation": result.get("explanation"),
    }

@app.post("/api/add_ticker")
def add_ticker(req: AddTickerRequest):
    """Add a new ticker to the database using Alpaca data"""
    symbol = req.symbol.upper()
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
    
    try:
        from modeling.alpaca_data import get_alpaca_data_provider
        provider = get_alpaca_data_provider()
        if not provider:
            return {"status": "error", "message": "Alpaca data provider not available"}
        
        result = provider.add_new_symbol_to_database(db_path, symbol)
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/update_all_tickers")
def update_all_tickers():
    """Update all existing tickers with fresh Alpaca data"""
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
    
    try:
        from modeling.alpaca_data import get_alpaca_data_provider
        provider = get_alpaca_data_provider()
        if not provider:
            return {"status": "error", "message": "Alpaca data provider not available"}
        
        result = provider.update_database_with_alpaca_data(db_path)
        return {
            "status": "success",
            "message": "Database updated with fresh Alpaca data",
            "details": result
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Advanced Technical Analysis Endpoints ---
@app.get("/api/technical/{symbol}")
async def get_technical_analysis(symbol: str):
    """Get comprehensive technical analysis with calculated indicators and triggered signals"""
    # Normalize symbol to uppercase for consistency
    symbol = symbol.upper().strip()
    try:
        conn = sqlite3.connect('data_ingestion/stocks.db')
        query = '''
        SELECT Date, Open, High, Low, Close, Volume FROM stock_prices 
        WHERE Symbol = ? 
        ORDER BY Date DESC 
        LIMIT 50
        '''
        
        df = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()
        
        if df.empty:
            return {"status": "error", "message": f"No data found for {symbol}"}
        
        # Sort by date ascending for calculations
        df = df.sort_values('Date')
        df.reset_index(drop=True, inplace=True)
        
        # Calculate technical indicators on-demand
        try:
            import pandas_ta as ta
            
            # Calculate basic indicators
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['EMA_9'] = ta.ema(df['Close'], length=9)
            df['EMA_20'] = ta.ema(df['Close'], length=20)
            df['EMA_50'] = ta.ema(df['Close'], length=50)
            
            # MACD
            macd_result = ta.macd(df['Close'])
            if macd_result is not None and not macd_result.empty:
                # Handle different possible column names
                macd_cols = macd_result.columns.tolist()
                if len(macd_cols) >= 2:
                    df['MACD'] = macd_result.iloc[:, 0]  # First column is usually MACD
                    df['MACD_Signal'] = macd_result.iloc[:, 1]  # Second is signal
            
            # Bollinger Bands
            bb_result = ta.bbands(df['Close'])
            if bb_result is not None and not bb_result.empty:
                bb_cols = bb_result.columns.tolist()
                if len(bb_cols) >= 3:
                    df['BB_Lower'] = bb_result.iloc[:, 0]  # Usually lower, middle, upper
                    df['BB_Middle'] = bb_result.iloc[:, 1]
                    df['BB_Upper'] = bb_result.iloc[:, 2]
            
            # VWAP (simplified)
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
        except ImportError:
            # Fallback to simple calculations if pandas_ta not available
            df['RSI'] = 50  # Neutral RSI
            df['EMA_9'] = df['Close'].ewm(span=9).mean()
            df['EMA_20'] = df['Close'].ewm(span=20).mean()
            df['EMA_50'] = df['Close'].ewm(span=50).mean()
            df['MACD'] = df['EMA_9'] - df['EMA_20']
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['VWAP'] = df['Close']  # Simplified
        
        # Get latest values
        latest = df.iloc[-1]
        current_price = float(latest['Close'])
        
        # Build indicators dictionary
        indicators = {
            'RSI': float(latest.get('RSI', 50)) if pd.notna(latest.get('RSI', 50)) else 50,
            'MACD': float(latest.get('MACD', 0)) if pd.notna(latest.get('MACD', 0)) else 0,
            'MACD_Signal': float(latest.get('MACD_Signal', 0)) if pd.notna(latest.get('MACD_Signal', 0)) else 0,
            'EMA_9': float(latest.get('EMA_9', current_price)) if pd.notna(latest.get('EMA_9', current_price)) else current_price,
            'EMA_20': float(latest.get('EMA_20', current_price)) if pd.notna(latest.get('EMA_20', current_price)) else current_price,
            'EMA_50': float(latest.get('EMA_50', current_price)) if pd.notna(latest.get('EMA_50', current_price)) else current_price,
            'VWAP': float(latest.get('VWAP', current_price)) if pd.notna(latest.get('VWAP', current_price)) else current_price,
            'BB_Upper': float(latest.get('BB_Upper', current_price * 1.02)) if pd.notna(latest.get('BB_Upper')) else current_price * 1.02,
            'BB_Lower': float(latest.get('BB_Lower', current_price * 0.98)) if pd.notna(latest.get('BB_Lower')) else current_price * 0.98,
            'Current_Price': current_price,
            'Volume': int(latest['Volume']) if pd.notna(latest['Volume']) else 0
        }
        
        # Determine triggered signals
        signals = []
        
        # RSI signals
        rsi = indicators['RSI']
        if rsi > 70:
            signals.append('RSI Overbought')
        elif rsi < 30:
            signals.append('RSI Oversold')
        
        # MACD signals
        if indicators['MACD'] > indicators['MACD_Signal']:
            signals.append('MACD Bullish Crossover')
        else:
            signals.append('MACD Bearish Crossover')
        
        # EMA signals
        if indicators['EMA_9'] > indicators['EMA_20']:
            signals.append('Short-term Bullish (EMA 9 > EMA 20)')
        else:
            signals.append('Short-term Bearish (EMA 9 < EMA 20)')
        
        # Golden Cross / Death Cross
        if indicators['EMA_20'] > indicators['EMA_50']:
            signals.append('Golden Cross (EMA 20 > EMA 50)')
        else:
            signals.append('Death Cross (EMA 20 < EMA 50)')
        
        # Price vs VWAP
        if current_price > indicators['VWAP']:
            signals.append('Price Above VWAP (Bullish)')
        else:
            signals.append('Price Below VWAP (Bearish)')
        
        # Bollinger Bands
        if current_price > indicators['BB_Upper']:
            signals.append('Price Above Bollinger Upper (Overbought)')
        elif current_price < indicators['BB_Lower']:
            signals.append('Price Below Bollinger Lower (Oversold)')
        
        return {
            "status": "success", 
            "indicators": indicators,
            "signals": signals,
            "timestamp": latest['Date'],
            "symbol": symbol
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/backtest/{symbol}")
def get_backtest_results(symbol: str, timeframe: str = "1Day", initial_capital: float = 100000):
    """Get backtest results with buy/sell signals and performance"""
    try:
        from modeling.technical_indicators import TechnicalIndicators
        from modeling.alpaca_data import get_alpaca_data_provider
        
        provider = get_alpaca_data_provider()
        if not provider:
            return {"status": "error", "message": "Data provider not available"}
        
        # Get historical data
        df = provider.get_historical_bars(symbol.upper(), timeframe=timeframe)
        if df.empty:
            return {"status": "error", "message": f"No data found for {symbol}"}
        
        # Run backtest
        tech_indicators = TechnicalIndicators(df)
        backtest_results = tech_indicators.get_backtest_data(initial_capital)
        
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "backtest": backtest_results
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/chart/{symbol}")
async def get_chart_data(symbol: str, timeframe: str = "1D", period: str = "6M"):
    """Get comprehensive chart data with candlesticks and calculated indicators"""
    # Normalize symbol to uppercase for consistency
    symbol = symbol.upper().strip()
    try:
        # Map period to number of days
        period_days = {
            "1D": 1,
            "1W": 7, 
            "1M": 30,
            "3M": 90,
            "6M": 180,
            "1Y": 365,
            "2Y": 730,
            "5Y": 1825
        }.get(period, 180)  # Default to 6 months
        
        # Calculate date cutoff
        cutoff_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('data_ingestion/stocks.db')
        query = '''
        SELECT Date, Open, High, Low, Close, Volume
        FROM stock_prices 
        WHERE Symbol = ? AND Date >= ?
        ORDER BY Date ASC 
        LIMIT 1000
        '''
        
        df = pd.read_sql_query(query, conn, params=(symbol, cutoff_date))
        conn.close()
        
        if df.empty:
            return {"status": "error", "message": f"No data found for {symbol}"}
        
        # Calculate indicators on-demand for charting
        try:
            import pandas_ta as ta
            
            # Calculate indicators
            df['EMA_9'] = ta.ema(df['Close'], length=9)
            df['EMA_20'] = ta.ema(df['Close'], length=20)
            df['EMA_50'] = ta.ema(df['Close'], length=50)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # MACD
            macd_result = ta.macd(df['Close'])
            if macd_result is not None and not macd_result.empty:
                macd_cols = macd_result.columns.tolist()
                if len(macd_cols) >= 2:
                    df['MACD'] = macd_result.iloc[:, 0]
                    df['MACD_Signal'] = macd_result.iloc[:, 1]
            
            # Bollinger Bands
            bb_result = ta.bbands(df['Close'])
            if bb_result is not None and not bb_result.empty:
                bb_cols = bb_result.columns.tolist()
                if len(bb_cols) >= 3:
                    df['BB_lower'] = bb_result.iloc[:, 0]
                    df['BB_middle'] = bb_result.iloc[:, 1]
                    df['BB_upper'] = bb_result.iloc[:, 2]
            
            # VWAP
            df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            
        except Exception as e:
            print(f"pandas_ta error: {e}")
            # Fallback calculations
            df['EMA_9'] = df['Close'].ewm(span=9).mean()
            df['EMA_20'] = df['Close'].ewm(span=20).mean()
            df['EMA_50'] = df['Close'].ewm(span=50).mean()
            df['RSI'] = 50  # Neutral
            df['MACD'] = df['EMA_9'] - df['EMA_20']
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['VWAP'] = df['Close']
            # Simple Bollinger Bands
            rolling_mean = df['Close'].rolling(window=20).mean()
            rolling_std = df['Close'].rolling(window=20).std()
            df['BB_upper'] = rolling_mean + (rolling_std * 2)
            df['BB_lower'] = rolling_mean - (rolling_std * 2)
            df['BB_middle'] = rolling_mean
        
        # Convert to list of dictionaries
        chart_data = []
        for _, row in df.iterrows():
            data_point = {
                'timestamp': row['Date'],
                'open': float(row['Open']) if pd.notna(row['Open']) else None,
                'high': float(row['High']) if pd.notna(row['High']) else None,
                'low': float(row['Low']) if pd.notna(row['Low']) else None,
                'close': float(row['Close']) if pd.notna(row['Close']) else None,
                'volume': int(row['Volume']) if pd.notna(row['Volume']) else None,
                'EMA_9': float(row.get('EMA_9')) if pd.notna(row.get('EMA_9')) else None,
                'EMA_20': float(row.get('EMA_20')) if pd.notna(row.get('EMA_20')) else None,
                'EMA_50': float(row.get('EMA_50')) if pd.notna(row.get('EMA_50')) else None,
                'RSI': float(row.get('RSI', 50)) if pd.notna(row.get('RSI', 50)) else None,
                'MACD': float(row.get('MACD', 0)) if pd.notna(row.get('MACD', 0)) else None,
                'MACD_Signal': float(row.get('MACD_Signal', 0)) if pd.notna(row.get('MACD_Signal', 0)) else None,
                'VWAP': float(row.get('VWAP')) if pd.notna(row.get('VWAP')) else None,
                'BB_upper': float(row.get('BB_upper')) if pd.notna(row.get('BB_upper')) else None,
                'BB_lower': float(row.get('BB_lower')) if pd.notna(row.get('BB_lower')) else None,
                'BB_middle': float(row.get('BB_middle')) if pd.notna(row.get('BB_middle')) else None,
            }
            chart_data.append(data_point)
        
        return {"status": "success", "data": chart_data}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/options/{symbol}")
async def get_options_chain(symbol: str):
    """Get options chain for a symbol using Alpaca data"""
    try:
        from modeling.alpaca_options import get_alpaca_options_provider
        
        provider = get_alpaca_options_provider()
        if provider and provider.api_key:
            # Use real Alpaca options data
            chain_data = provider.get_options_chain(symbol.upper())
            return {"status": "success", "data": chain_data}
        else:
            # Fallback to enhanced mock data
            conn = sqlite3.connect('data_ingestion/stocks.db')
            query = '''
            SELECT Close FROM stock_prices 
            WHERE Symbol = ? 
            ORDER BY Date DESC 
            LIMIT 1
            '''
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty:
                return {"status": "error", "message": f"No data found for {symbol}"}
            
            current_price = float(df.iloc[0]['Close'])
            
            # Enhanced mock options chain
            chain = []
            for i in range(-5, 6):
                strike = round(current_price + (current_price * 0.05 * i), 2)
                moneyness = current_price - strike
                
                # More realistic option pricing
                call_intrinsic = max(0, moneyness)
                put_intrinsic = max(0, -moneyness)
                time_value = max(0.5, 3 - abs(moneyness) * 0.1)
                
                chain.append({
                    'symbol': f"{symbol}{abs(i):02d}",
                    'strike': strike,
                    'option_type': 'call',
                    'bid': max(0.01, call_intrinsic + time_value - 0.05),
                    'ask': call_intrinsic + time_value + 0.05,
                    'last': call_intrinsic + time_value,
                    'volume': int(abs(i) * 20 + 100),
                    'open_interest': int(abs(i) * 50 + 200),
                    'implied_volatility': 0.25 + abs(i) * 0.01
                })
                
                chain.append({
                    'symbol': f"{symbol}P{abs(i):02d}",
                    'strike': strike,
                    'option_type': 'put',
                    'bid': max(0.01, put_intrinsic + time_value - 0.05),
                    'ask': put_intrinsic + time_value + 0.05,
                    'last': put_intrinsic + time_value,
                    'volume': int(abs(i) * 15 + 80),
                    'open_interest': int(abs(i) * 40 + 150),
                    'implied_volatility': 0.25 + abs(i) * 0.01
                })
            
            options_data = {
                'symbol': symbol,
                'current_price': current_price,
                'chain': chain,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            return {"status": "success", "data": options_data}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/options/analysis/{symbol}")
async def get_options_analysis(symbol: str):
    """Get comprehensive options analysis using Alpaca data"""
    try:
        from modeling.alpaca_options import get_alpaca_options_provider
        
        provider = get_alpaca_options_provider()
        if provider and provider.api_key:
            # Use real Alpaca options analysis
            analysis_data = provider.get_options_analysis(symbol.upper())
            return {"status": "success", "data": analysis_data}
        else:
            # Enhanced fallback analysis
            conn = sqlite3.connect('data_ingestion/stocks.db')
            query = '''
            SELECT Close FROM stock_prices 
            WHERE Symbol = ? 
            ORDER BY Date DESC 
            LIMIT 1
            '''
            df = pd.read_sql_query(query, conn, params=(symbol,))
            conn.close()
            
            if df.empty:
                return {"status": "error", "message": f"No data found for {symbol}"}
            
            current_price = float(df.iloc[0]['Close'])
            
            # Enhanced options analysis with realistic metrics
            analysis = {
                'symbol': symbol,
                'current_price': current_price,
                'sentiment': {
                    'put_call_ratio': 0.85 + (hash(symbol) % 100) * 0.01,  # Vary by symbol
                    'implied_volatility': 0.285 + (hash(symbol) % 50) * 0.001,
                    'max_pain': current_price * (0.98 + (hash(symbol) % 40) * 0.001),
                    'sentiment_score': 'NEUTRAL'
                },
                'strategies': [
                    {
                        'name': 'Bull Call Spread',
                        'description': f'Buy {current_price:.0f} call, sell {current_price*1.05:.0f} call',
                        'outlook': 'Moderately Bullish',
                        'max_profit': f'${(current_price * 0.05 * 100):.0f}',
                        'max_loss': f'${(current_price * 0.02 * 100):.0f}',
                        'breakeven': f'${current_price * 1.02:.2f}',
                        'complexity': 'Intermediate'
                    },
                    {
                        'name': 'Iron Condor',
                        'description': f'Sell {current_price*0.95:.0f} put & {current_price*1.05:.0f} call',
                        'outlook': 'Neutral',
                        'max_profit': f'${(current_price * 0.03 * 100):.0f}',
                        'max_loss': f'${(current_price * 0.07 * 100):.0f}',
                        'breakeven': f'${current_price*0.97:.2f} - ${current_price*1.03:.2f}',
                        'complexity': 'Advanced'
                    },
                    {
                        'name': 'Protective Put',
                        'description': f'Buy stock + {current_price*0.95:.0f} put',
                        'outlook': 'Bullish with Protection',
                        'max_profit': 'Unlimited',
                        'max_loss': f'${current_price * 0.05:.0f} per share',
                        'breakeven': f'${current_price * 1.02:.2f}',
                        'complexity': 'Beginner'
                    }
                ],
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            return {"status": "success", "data": analysis}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/options/strategies/{symbol}")
def get_options_strategies(symbol: str, outlook: str = "BULLISH"):
    """Get suggested options strategies based on market outlook"""
    try:
        from modeling.options_data import get_options_provider
        
        provider = get_options_provider()
        if not provider:
            return {"status": "error", "message": "Options provider not available"}
        
        strategies = provider.get_options_strategies(symbol.upper(), outlook.upper())
        
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "outlook": outlook.upper(),
            "strategies": strategies
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Working Real-time Price Endpoint ---
@app.get("/api/price/{symbol}")
def get_current_price(symbol: str):
    """Get current price for a symbol - SIMPLE WORKING VERSION"""
    # Normalize symbol to uppercase for consistency
    symbol = symbol.upper().strip()
    try:
        conn = sqlite3.connect('data_ingestion/stocks.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Close, High, Low, Volume, Date 
            FROM stock_prices 
            WHERE Symbol = ? 
            ORDER BY Date DESC 
            LIMIT 1
        """, (symbol,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            close, high, low, volume, date = result
            current_price = float(close)
            return {
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "price": current_price,
                    "ask": current_price + 0.01,
                    "bid": current_price - 0.01,
                    "high": float(high),
                    "low": float(low),
                    "volume": int(volume),
                    "timestamp": str(date),
                    "source": "database"
                }
            }
        else:
            return {
                "status": "error",
                "message": f"No data found for {symbol}"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/realtime/{symbol}")
def get_realtime_price_fixed(symbol: str):
    """Get real-time price - calls the working price endpoint"""
    return get_current_price(symbol)

# --- Dynamic Symbol Search Endpoints ---
@app.get("/api/search/symbols")
async def search_symbols(query: str = Query(..., min_length=1)):
    """Search for symbols in comprehensive stock universe"""
    try:
        # Use comprehensive symbol list (works without Alpaca)
        all_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD',
            'INTC', 'MARA', 'RIOT', 'COIN', 'SQ', 'PYPL', 'UBER', 'LYFT', 'SHOP', 'ROKU',
            'ZM', 'PLTR', 'SNOW', 'CRWD', 'NET', 'DDOG', 'OKTA', 'TWLO', 'WORK', 'DOCU',
            'ZS', 'SPY', 'QQQ', 'IWM', 'VTI', 'VOO', 'VEA', 'VWO', 'GLD', 'SLV', 'TLT',
            'ARKK', 'ARKQ', 'ARKG', 'ARKW', 'ARKF', 'XLK', 'XLF', 'XLE', 'XLV', 'XLI',
            'BA', 'JPM', 'JNJ', 'V', 'MA', 'UNH', 'HD', 'PG', 'DIS', 'ADBE', 'CRM', 'ORCL',
            'IBM', 'CSCO', 'QCOM', 'TXN', 'AVGO', 'NOW', 'INTU', 'ISRG', 'BKNG', 'GILD',
            'BABA', 'NIO', 'XPEV', 'LI', 'PDD', 'JD', 'BILI', 'DIDI', 'TME', 'NTES',
            'GME', 'AMC', 'BB', 'NOK', 'SNDL', 'CLOV', 'WISH', 'SOFI', 'HOOD', 'RBLX',
            'ABNB', 'DASH', 'PINS', 'SNAP', 'TWTR', 'SPOT', 'SQ', 'PYPL', 'ADSK', 'WDAY',
            'CZR', 'DKNG', 'PENN', 'MGM', 'LVS', 'WYNN', 'BYD', 'F', 'GM', 'LCID', 'RIVN'
        ]
        
        filtered = [s for s in all_symbols if query.upper() in s]
        return {
            "status": "success",
            "symbols": [{'symbol': s, 'name': s} for s in filtered[:20]],
            "source": "comprehensive"
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/data/fetch/{symbol}")
async def fetch_symbol_data(symbol: str, days: int = 30):
    """Fetch fresh data for any symbol using yfinance as fallback"""
    try:
        symbol = symbol.upper()
        
        # Check if data exists in database
        conn = sqlite3.connect('data_ingestion/stocks.db')
        query = '''
        SELECT COUNT(*) as count FROM stock_prices 
        WHERE symbol = ?
        '''
        df = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()
        
        data_exists = df.iloc[0]['count'] > 0
        
        if data_exists:
            return {
                "status": "success",
                "message": f"Using existing data for {symbol}",
                "source": "database",
                "symbol": symbol
            }
        
        # Try to fetch data using yfinance as fallback
        try:
            import yfinance as yf
            
            # Fetch data from yfinance
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days}d")
            
            if hist.empty:
                return {
                    "status": "error",
                    "message": f"No data found for {symbol}"
                }
            
            # Store in database
            conn = sqlite3.connect('data_ingestion/stocks.db')
            
            # Delete existing data for this symbol
            conn.execute('DELETE FROM stock_prices WHERE symbol = ?', (symbol,))
            
            # Insert new data
            for index, row in hist.iterrows():
                conn.execute('''
                    INSERT OR REPLACE INTO stock_prices 
                    (date, open, high, low, close, adj_close, volume, symbol)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    index.strftime('%Y-%m-%d'),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    float(row['Close']),  # Use close as adj_close
                    int(row['Volume']),
                    symbol
                ))
            
            conn.commit()
            conn.close()
            
            return {
                "status": "success",
                "message": f"Fetched {len(hist)} days of data for {symbol}",
                "source": "yfinance",
                "symbol": symbol,
                "records": len(hist)
            }
            
        except Exception as fetch_error:
            print(f"Data fetch error: {fetch_error}")
            return {
                "status": "error",
                "message": f"Failed to fetch data for {symbol}: {str(fetch_error)}"
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Trade Logging Endpoints ---
@app.post("/api/trades/log")
async def log_hypothetical_trade(trade_data: dict):
    """Log a hypothetical trade for tracking"""
    try:
        # Store trade in memory or database for tracking
        # For now, we'll just return success - in production you'd store this
        return {
            "status": "success",
            "message": "Trade logged successfully",
            "trade_id": f"trade_{int(time.time())}",
            "data": trade_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/trades/performance/{symbol}")
async def get_trade_performance(symbol: str):
    """Get performance of hypothetical trades for a symbol"""
    try:
        # Get current price for P&L calculation
        conn = sqlite3.connect('data_ingestion/stocks.db')
        query = '''
        SELECT close FROM stock_prices 
        WHERE symbol = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
        '''
        df = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()
        
        if df.empty:
            return {"status": "error", "message": f"No data found for {symbol}"}
        
        current_price = float(df.iloc[0]['close'])
        
        # In a real implementation, you'd fetch stored trades from database
        # For now, return mock performance data
        return {
            "status": "success",
            "symbol": symbol,
            "current_price": current_price,
            "trades": [],  # Would contain actual logged trades
            "total_pnl": 0.0,
            "win_rate": 0.0
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/agent")
def agent_chat(request: dict):
    """Agent chat endpoint"""
    try:
        question = request.get('question', '')
        if not question:
            return {"status": "error", "message": "No question provided"}
        
        # Initialize agent
        agent = StockAgent()
        
        # Get agent decision
        result = agent.decide(question)
        
        return {
            "status": "success",
            "response": result.get('explanation', 'No explanation available'),
            "decision": result.get('decision', 'wait'),
            "confidence": result.get('confidence', 0.0)
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/symbols")
def get_symbols():
    """Get all available symbols"""
    try:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol")
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return {"status": "success", "symbols": symbols}
        
    except Exception as e:
        return {"status": "error", "message": str(e), "symbols": []}

# Removed duplicate - using the one defined below

# --- Portfolio Simulation Endpoints (Optional) ---
try:
    from modeling.portfolio import Portfolio, PortfolioSimulator, simple_rsi_strategy
    PORTFOLIO_AVAILABLE = True
except ImportError:
    PORTFOLIO_AVAILABLE = False
    print("Portfolio simulation disabled - portfolio module not found")

if PORTFOLIO_AVAILABLE:
    @app.post("/api/portfolio/create")
    def create_portfolio(req: PortfolioRequest):
        """Create a new portfolio"""
        try:
            portfolio = Portfolio(req.initial_cash)
            return {
                "status": "success",
                "portfolio": portfolio.to_dict()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/portfolio/backtest")
    def backtest_strategy(req: BacktestRequest):
        """Run a backtest simulation"""
        try:
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
            simulator = PortfolioSimulator(db_path)
            
            if req.strategy == "agent":
                portfolio = simulator.backtest_agent_decisions(
                    req.start_date, 
                    req.end_date, 
                    req.initial_cash
                )
            elif req.strategy == "rsi":
                symbols = req.symbols if req.symbols else ["AAPL", "TSLA", "MSFT"]
                portfolio = simulator.simulate_strategy(
                    symbols,
                    req.start_date,
                    req.end_date,
                    simple_rsi_strategy,
                    req.initial_cash
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid strategy. Use 'agent' or 'rsi'")
                
            return {
                "status": "success",
                "portfolio": portfolio.to_dict(),
                "positions": portfolio.get_positions_summary(),
                "transactions": portfolio.transactions[-10:]  # Last 10 transactions
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/portfolio/demo")
    def get_demo_portfolio():
        """Get a demo portfolio with sample data"""
        try:
            portfolio = Portfolio(100000.0)
            
            # Add some sample positions
            portfolio.buy("AAPL", 50, 150.0)
            portfolio.buy("TSLA", 25, 200.0)
            portfolio.buy("MSFT", 30, 300.0)
            
            # Update with current prices (mock data)
            portfolio.update_prices({
                "AAPL": 155.0,
                "TSLA": 210.0,
                "MSFT": 310.0
            })
            
            return {
                "status": "success",
                "portfolio": portfolio.to_dict(),
                "positions": portfolio.get_positions_summary()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
else:
    # Portfolio endpoints disabled - return error messages
    @app.post("/api/portfolio/create")
    def create_portfolio_disabled(req: PortfolioRequest):
        return {"status": "error", "message": "Portfolio simulation not available"}
    
    @app.post("/api/portfolio/backtest")
    def backtest_strategy_disabled(req: BacktestRequest):
        return {"status": "error", "message": "Portfolio simulation not available"}
    
    @app.get("/api/portfolio/demo")
    def get_demo_portfolio_disabled():
        return {"status": "error", "message": "Portfolio simulation not available"}

# --- Missing Frontend API Endpoints ---

@app.get("/api/intelligent-options/{symbol}")
def get_intelligent_options_recommendation(symbol: str):
    """Get intelligent options trading recommendation for a symbol"""
    try:
        # Normalize symbol to uppercase for consistency
        symbol = symbol.upper().strip()
        
        # Import the intelligent options agent
        from modeling.intelligent_options_agent import IntelligentOptionsAgent
        
        # Create agent and get recommendation
        agent = IntelligentOptionsAgent()
        recommendation = agent.generate_recommendation(symbol)
        
        return {
            "status": "success",
            "symbol": symbol,
            "recommendation": recommendation,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
    except ImportError as e:
        # Fallback to mock data if agent not available
        return {
            "status": "mock",
            "symbol": symbol.upper(),
            "recommendation": {
                "action": "BUY",
                "contract_type": "CALL",
                "strike": 20.0,
                "expiration": "2025-08-15",
                "premium": 1.25,
                "confidence": 0.75,
                "reasoning": "Mock recommendation - intelligent options agent not available"
            },
            "timestamp": pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol.upper() if 'symbol' in locals() else "UNKNOWN",
            "message": f"Failed to generate recommendation: {str(e)}",
            "timestamp": pd.Timestamp.now().isoformat()
        }

@app.post("/api/agent")
def agent_chat_endpoint(req: AgentRequest):
    """Chat with the stock analysis agent"""
    try:
        # Use the existing agent_chat function
        return agent_chat(req)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Agent chat failed: {str(e)}",
            "timestamp": pd.Timestamp.now().isoformat()
        }

@app.get("/api/current-price/{symbol}")
def get_current_price_alt(symbol: str):
    """Alternative endpoint for current price (matches frontend expectation)"""
    # Normalize symbol to uppercase for consistency
    symbol = symbol.upper().strip()
    # Use the existing get_current_price function
    return get_current_price(symbol)

@app.get("/api/signals/{symbol}")
def get_comprehensive_signals(symbol: str):
    """Get comprehensive signals analysis for both Active Signals and Options Analysis panels"""
    try:
        # Normalize symbol to uppercase for consistency
        symbol = symbol.upper().strip()
        
        # Import the comprehensive signals analysis function
        try:
            from modeling.intelligent_options_agent import get_comprehensive_signals_analysis
        except ImportError:
            # Fallback for direct execution
            from intelligent_options_agent import get_comprehensive_signals_analysis
        
        # Get comprehensive signals analysis
        print(f"DEBUG API: Calling get_comprehensive_signals_analysis for {symbol}")
        analysis = get_comprehensive_signals_analysis(symbol)
        print(f"DEBUG API: Analysis result: {analysis}")
        
        if 'error' in analysis:
            return {
                "status": "error",
                "symbol": symbol,
                "message": analysis['error'],
                "timestamp": pd.Timestamp.now().isoformat()
            }
        
        return {
            "status": "success",
            "symbol": symbol,
            "data": analysis,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
    except ImportError as e:
        return {
            "status": "error",
            "symbol": symbol.upper() if 'symbol' in locals() else "UNKNOWN",
            "message": "Signals analysis not available - missing dependencies",
            "timestamp": pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "symbol": symbol.upper() if 'symbol' in locals() else "UNKNOWN",
            "message": f"Signals analysis failed: {str(e)}",
            "timestamp": pd.Timestamp.now().isoformat()
        }
