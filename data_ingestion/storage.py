"""
Handles local SQLite storage for stock data.
"""
import sqlite3
import pandas as pd

class StockDataStorage:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        query = """
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
        """
        self.conn.execute(query)
        self.conn.commit()

    def save_data(self, df, symbol):
        import numpy as np
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join([str(i) for i in col if i]) for col in df.columns.values]
        else:
            df.columns = [str(col) for col in df.columns]

        # yfinance typically returns index as DatetimeIndex; reset and rename as needed
        if 'Date' not in df.columns and 'Datetime' not in df.columns:
            if df.index.name in ['Date', 'Datetime']:
                df = df.reset_index()
            else:
                df = df.reset_index(drop=True)
                df['Date'] = None

        # Robust column mapping
        col_map = {
            'Date': 'Date',
            'Datetime': 'Date',
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Adj Close': 'Adj_Close',
            'Adj_Close': 'Adj_Close',
            'Volume': 'Volume',
        }
        df = df.rename(columns=col_map)

        # Only use columns that exist in df
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Adj_Close', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan
        df['Symbol'] = symbol

        # Convert numeric columns to float (except Symbol and Date)
        for col in ['Open', 'High', 'Low', 'Close', 'Adj_Close', 'Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Reorder columns to match schema
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Adj_Close', 'Volume', 'Symbol']]
        df.to_sql('stock_prices', self.conn, if_exists='append', index=False)

    def close(self):
        self.conn.close()

    def query_data(self, symbol=None, start_date=None, end_date=None):
        """
        Retrieve stock data for a symbol and date range.
        Args:
            symbol (str): Stock symbol (optional)
            start_date (str): Start date 'YYYY-MM-DD' (optional)
            end_date (str): End date 'YYYY-MM-DD' (optional)
        Returns:
            pd.DataFrame: Query results
        """
        query = "SELECT * FROM stock_prices WHERE 1=1"
        params = []
        if symbol:
            query += " AND Symbol = ?"
            params.append(symbol)
        if start_date:
            query += " AND Date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND Date <= ?"
            params.append(end_date)
        return pd.read_sql_query(query, self.conn, params=params)

# Example usage:
# storage = StockDataStorage('stocks.db')
# df = storage.query_data(symbol='AAPL', start_date='2022-01-01', end_date='2022-12-31')
# print(df.head())
# storage.close()
