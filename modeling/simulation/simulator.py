"""
Core simulation engine for strategy backtesting.
"""
import pandas as pd
from .report import generate_report

class StrategySimulator:
    def __init__(self, df, strategy, params=None, initial_cash=10000):
        self.df = df.copy()
        self.strategy = strategy
        self.params = params or {}
        self.initial_cash = initial_cash
        self.trades = []
        self.equity_curve = []

    def run(self):
        position = 0
        entry_price = 0
        cash = self.initial_cash
        equity = self.initial_cash
        for i, row in self.df.iterrows():
            signal = self.strategy(row, self.params)
            if position == 0 and signal == 'buy':
                position = 1
                entry_price = row['Close']
                self.trades.append({'type': 'buy', 'date': i, 'price': entry_price})
            elif position == 1 and signal == 'sell':
                position = 0
                exit_price = row['Close']
                pnl = exit_price - entry_price
                cash += pnl
                self.trades.append({'type': 'sell', 'date': i, 'price': exit_price, 'pnl': pnl})
            equity = cash + (row['Close'] - entry_price if position == 1 else 0)
            self.equity_curve.append(equity)
        report = generate_report(self.trades, self.equity_curve, self.initial_cash)
        return {'performance': report, 'trade_log': self.trades, 'equity_curve': self.equity_curve}
