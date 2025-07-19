import os
import sqlite3
import yfinance as yf
from modeling.twin_state_query_example import get_symbols

def update_all_tickers(db_path):
    symbols = get_symbols(db_path)
    for symbol in symbols:
        print(f"Updating {symbol}...")
        df = yf.download(symbol, period="max")
        if df is not None and not df.empty:
            df.reset_index(inplace=True)
            df.columns = [c.replace(' ', '_') for c in df.columns]
            conn = sqlite3.connect(db_path)
            try:
                df.to_sql(symbol, conn, if_exists="replace", index=False)
                print(f"Updated {symbol} with {len(df)} rows.")
            except Exception as e:
                print(f"Error updating {symbol}: {e}")
            conn.close()
        else:
            print(f"No data found for {symbol}.")
    print("All tickers updated.")

if __name__ == "__main__":
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "stocks.db"))
    update_all_tickers(db_path)
