"""
Test the TwinState modeling layer on ingested data.
"""
import pandas as pd
import sqlite3
from twin_state import TwinState

def load_data(symbol, db_path='/Users/keithcamp/Stock Market Digital Twin/data_ingestion/stocks.db'):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        f"SELECT Date, Open, High, Low, Close, Volume FROM stock_prices WHERE Symbol = ? ORDER BY Date ASC",
        conn, params=(symbol,)
    )
    conn.close()
    # Ensure correct dtypes
    df['Date'] = pd.to_datetime(df['Date'])
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    return df

if __name__ == "__main__":
    symbol = 'AAPL'
    df = load_data(symbol)
    print(f"Loaded {len(df)} rows for {symbol}")
    df = df.set_index('Date')  # Set Date as index for indicator compatibility
    twin = TwinState(df)
    state = twin.get_state()
    print(f"Twin state for {symbol}:")
    for k, v in state.items():
        print(f"{k}: {v}")
