"""
REST API for agentic AI stock decision-making
"""
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Query
from pydantic import BaseModel

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

app = FastAPI()

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

@app.get("/api/realtime/{symbol}")
def realtime_price(symbol: str):
    try:
        quote = get_realtime_quote(symbol.upper())
        if quote is None:
            raise Exception("Failed to fetch real-time quote")
        return {
            "symbol": symbol.upper(),
            "ask": getattr(quote, 'ask_price', None),
            "bid": getattr(quote, 'bid_price', None),
            "timestamp": str(getattr(quote, 'timestamp', ''))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.on_event("startup")
def start_alert_monitor():
    t = threading.Thread(target=run_alert_monitor_periodically, daemon=True)
    t.start()


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
def get_technical_analysis(symbol: str, timeframe: str = "1Day"):
    """Get comprehensive technical analysis for a symbol"""
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
        
        # Calculate technical indicators
        tech_indicators = TechnicalIndicators(df)
        signals = tech_indicators.get_current_signals()
        
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "analysis": signals
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
def get_chart_data(symbol: str, timeframe: str = "1Day", period: str = "6M"):
    """Get chart data with technical indicators for visualization"""
    try:
        from modeling.technical_indicators import TechnicalIndicators
        from modeling.alpaca_data import get_alpaca_data_provider
        from datetime import datetime, timedelta
        
        provider = get_alpaca_data_provider()
        if not provider:
            return {"status": "error", "message": "Data provider not available"}
        
        # Calculate start date based on period
        end_date = datetime.now()
        period_map = {
            "1M": 30, "3M": 90, "6M": 180, 
            "1Y": 365, "2Y": 730, "5Y": 1825
        }
        days_back = period_map.get(period, 180)
        start_date = end_date - timedelta(days=days_back)
        
        # Get historical data
        df = provider.get_historical_bars(
            symbol.upper(), 
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            timeframe=timeframe
        )
        
        if df.empty:
            return {"status": "error", "message": f"No data found for {symbol}"}
        
        # Calculate all indicators
        tech_indicators = TechnicalIndicators(df)
        df_with_indicators = tech_indicators.calculate_all_indicators()
        
        # Prepare chart data
        chart_data = {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "period": period,
            "ohlcv": df_with_indicators[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_dict('records'),
            "indicators": {
                "sma_20": df_with_indicators[['Date', 'SMA_20']].dropna().to_dict('records'),
                "sma_50": df_with_indicators[['Date', 'SMA_50']].dropna().to_dict('records'),
                "bollinger_bands": df_with_indicators[['Date', 'BB_Upper', 'BB_Middle', 'BB_Lower']].dropna().to_dict('records'),
                "rsi": df_with_indicators[['Date', 'RSI']].dropna().to_dict('records'),
                "macd": df_with_indicators[['Date', 'MACD', 'MACD_Signal', 'MACD_Histogram']].dropna().to_dict('records'),
                "vwap": df_with_indicators[['Date', 'VWAP']].dropna().to_dict('records')
            },
            "signals": {
                "buy": df_with_indicators[df_with_indicators['Final_Signal'] == 'BUY'][['Date', 'Close', 'Buy_Signals']].to_dict('records'),
                "sell": df_with_indicators[df_with_indicators['Final_Signal'] == 'SELL'][['Date', 'Close', 'Sell_Signals']].to_dict('records')
            }
        }
        
        return {
            "status": "success",
            "chart_data": chart_data
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Options Data Endpoints ---
@app.get("/api/options/{symbol}")
def get_options_chain(symbol: str, expiration: str = None):
    """Get options chain for a symbol"""
    try:
        from modeling.options_data import get_options_provider
        
        provider = get_options_provider()
        if not provider:
            return {"status": "error", "message": "Options provider not available"}
        
        chain = provider.get_options_chain(symbol.upper(), expiration)
        
        return {
            "status": "success",
            "options_chain": chain
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/options/analysis/{symbol}")
def get_options_analysis(symbol: str):
    """Get comprehensive options analysis"""
    try:
        from modeling.options_data import get_options_provider
        
        provider = get_options_provider()
        if not provider:
            return {"status": "error", "message": "Options provider not available"}
        
        analysis = provider.get_options_analysis(symbol.upper())
        
        return {
            "status": "success",
            "options_analysis": analysis
        }
        
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

# --- Missing Frontend Endpoints ---
@app.get("/api/twin/latest")
def get_latest_twin_states():
    """Get latest twin states for all symbols"""
    try:
        # Get symbols from database
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol")
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not symbols:
            return {"status": "success", "data": []}
        
        # Get latest data for each symbol
        twin_states = []
        for symbol in symbols[:10]:  # Limit to first 10 for performance
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT symbol, date, open, high, low, close, volume 
                    FROM stock_prices 
                    WHERE symbol = ? 
                    ORDER BY date DESC 
                    LIMIT 1
                """, (symbol,))
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    twin_states.append({
                        "symbol": row[0],
                        "date": row[1],
                        "open": row[2],
                        "high": row[3],
                        "low": row[4],
                        "close": row[5],
                        "volume": row[6]
                    })
            except Exception:
                continue
        
        return {"status": "success", "data": twin_states}
        
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
