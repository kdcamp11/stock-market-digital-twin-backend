"""
Example: Run a backtest simulation using the EMA bounce strategy on historical AAPL data.
"""
import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from twin_state_query_example import load_data
from simulation.simulator import StrategySimulator
from simulation.strategies import ema_bounce_strategy
from simulation.config_examples import example_ema_bounce

if __name__ == "__main__":
    symbol = 'AAPL'
    df = load_data(symbol, db_path="/Users/keithcamp/Stock Market Digital Twin/data_ingestion/stocks.db")
    if df is None:
        print(f"No data found for {symbol}.")
        exit(1)
    # Enrich DataFrame with required indicators
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from indicators import add_ema, add_rsi
    df = add_ema(df, [example_ema_bounce['params']['ema_length']])
    df = add_rsi(df, 14)
    # Make sure indicators exist for the strategy
    required_cols = [f'EMA_{example_ema_bounce["params"]["ema_length"]}', 'RSI']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"Missing columns for strategy: {missing}")
        exit(1)
    sim = StrategySimulator(df, ema_bounce_strategy, example_ema_bounce['params'])
    results = sim.run()
    print("Performance Report:")
    for k, v in results['performance'].items():
        print(f"{k}: {v}")
    print("\nTrade Log:")
    for trade in results['trade_log']:
        print(trade)
