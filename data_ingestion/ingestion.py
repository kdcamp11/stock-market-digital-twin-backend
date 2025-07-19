"""
Main ingestion logic for stock market data.
"""
import yaml
import pandas as pd
import yfinance as yf
from storage import StockDataStorage

def load_config(path='config.yaml'):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def fetch_stock_data(symbol, start, end, interval):
    df = yf.download(symbol, start=start, end=end, interval=interval, group_by='ticker')
    df = df.reset_index()  # Ensure 'Date' is a column
    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join([str(i) for i in col if i]) for col in df.columns.values]
    else:
        df.columns = [str(col) for col in df.columns]
    # Map columns like 'AAPL_Open' to 'Open', etc.
    prefix = f'{symbol}_'
    col_map = {f'{symbol}_Open': 'Open',
               f'{symbol}_High': 'High',
               f'{symbol}_Low': 'Low',
               f'{symbol}_Close': 'Close',
               f'{symbol}_Adj Close': 'Adj_Close',
               f'{symbol}_Volume': 'Volume'}
    # Build the new DataFrame
    data = {
        'Date': df['Date'],
        'Open': df.get(f'{symbol}_Open', None),
        'High': df.get(f'{symbol}_High', None),
        'Low': df.get(f'{symbol}_Low', None),
        'Close': df.get(f'{symbol}_Close', None),
        'Adj_Close': df.get(f'{symbol}_Adj Close', df.get(f'{symbol}_Close', None)),
        'Volume': df.get(f'{symbol}_Volume', None),
        'Symbol': symbol
    }
    result_df = pd.DataFrame(data)
    return result_df

def main():
    config = load_config()
    storage = StockDataStorage('stocks.db')
    for symbol in config['symbols']:
        df = fetch_stock_data(symbol, config['start_date'], config['end_date'], config['interval'])
        storage.save_data(df, symbol)

if __name__ == '__main__':
    main()
