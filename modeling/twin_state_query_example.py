"""
Example: Query data from SQLite and model twin state for all symbols
"""
import pandas as pd
import sqlite3
from modeling.twin_state import TwinState

def get_symbols(db_path):
    conn = sqlite3.connect(db_path)
    symbols = pd.read_sql_query("SELECT DISTINCT Symbol FROM stock_prices", conn)['Symbol'].tolist()
    conn.close()
    return symbols

def load_data(symbol, db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        f"SELECT Date, Open, High, Low, Close, Volume FROM stock_prices WHERE Symbol = ? ORDER BY Date ASC",
        conn, params=(symbol,)
    )
    conn.close()
    if df.empty:
        return None
    df['Date'] = pd.to_datetime(df['Date'])
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    df = df.set_index('Date')
    return df

import os

if __name__ == "__main__":
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data_ingestion/stocks.db"))
    symbols = get_symbols(db_path)
    print(f"Found symbols: {symbols}")
    for symbol in symbols:
        df = load_data(symbol, db_path)
        print(f"\n--- Twin state for {symbol} ---")
        twin = TwinState(df)
        state = twin.get_state()
        for k, v in state.items():
            print(f"{k}: {v}")
