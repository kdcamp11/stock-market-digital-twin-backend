"""
REST API for agentic AI stock decision-making
"""
from fastapi import FastAPI, Query
from pydantic import BaseModel
from modeling.agent import StockAgent
from modeling.twin_state import TwinState
from modeling.twin_state_query_example import load_data
import yfinance as yf
import sqlite3

app = FastAPI()

# --- Start alert monitoring as a background thread ---
import threading
import time

def run_alert_monitor_periodically():
    from alerts.monitor import AlertMonitor
    monitor = AlertMonitor(config_path="alert_config.yaml")
    while True:
        monitor.check_all_symbols()
        time.sleep(600)  # Run every 10 minutes

@app.on_event("startup")
def start_alert_monitor():
    t = threading.Thread(target=run_alert_monitor_periodically, daemon=True)
    t.start()


# --- CORS middleware for Netlify frontend ---
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://stock-market-digital-twin.netlify.app"],  # More secure, or use ["*"] for dev
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
                    df.columns = [c.replace(' ', '_') for c in df.columns]
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
    symbol = req.symbol.upper()
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
    # Check if symbol already exists
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (symbol,))
    if cursor.fetchone():
        conn.close()
        return {"status": "exists", "message": f"{symbol} already in database."}
    # Fetch data from Yahoo Finance
    df = yf.download(symbol, period="max")
    if df is None or df.empty:
        conn.close()
        return {"status": "error", "message": f"No data found for {symbol} on Yahoo Finance."}
    # Save to SQLite
    df.reset_index(inplace=True)
    df.columns = [c.replace(' ', '_') for c in df.columns]
    try:
        df.to_sql(symbol, conn, if_exists="replace", index=False)
        conn.close()
        return {"status": "success", "message": f"{symbol} added to database.", "rows": len(df)}
    except Exception as e:
        conn.close()
        return {"status": "error", "message": str(e)}
