"""
Example script to query and display stored stock data from the local database.
"""
from storage import StockDataStorage

# Initialize the storage object
storage = StockDataStorage('stocks.db')

# Query for a specific symbol and date range
symbol = 'AAPL'
start_date = '2022-01-01'
end_date = '2022-12-31'

df = storage.query_data(symbol=symbol, start_date=start_date, end_date=end_date)

print(f"Showing {symbol} data from {start_date} to {end_date}:")
print(df.head())

# Query for all symbols in a date range
all_df = storage.query_data(start_date=start_date, end_date=end_date)
print("\nAll symbols in date range:")
print(all_df.head())

storage.close()
