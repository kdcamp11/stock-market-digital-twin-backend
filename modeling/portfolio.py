"""
Portfolio simulation and management for Stock Market Digital Twin
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class Portfolio:
    def __init__(self, initial_cash: float = 100000.0):
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.positions = {}  # {symbol: {'shares': int, 'avg_cost': float, 'last_price': float}}
        self.transactions = []  # List of all buy/sell transactions
        self.performance_history = []  # Daily portfolio value snapshots
        
    def buy(self, symbol: str, shares: int, price: float, timestamp: datetime = None):
        """Buy shares of a stock"""
        if timestamp is None:
            timestamp = datetime.now()
            
        cost = shares * price
        if cost > self.cash:
            raise ValueError(f"Insufficient cash. Need ${cost:.2f}, have ${self.cash:.2f}")
            
        self.cash -= cost
        
        if symbol in self.positions:
            # Update average cost
            current_shares = self.positions[symbol]['shares']
            current_cost = self.positions[symbol]['avg_cost'] * current_shares
            new_avg_cost = (current_cost + cost) / (current_shares + shares)
            
            self.positions[symbol]['shares'] += shares
            self.positions[symbol]['avg_cost'] = new_avg_cost
        else:
            self.positions[symbol] = {
                'shares': shares,
                'avg_cost': price,
                'last_price': price
            }
            
        self.transactions.append({
            'timestamp': timestamp,
            'action': 'buy',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'total': cost
        })
        
    def sell(self, symbol: str, shares: int, price: float, timestamp: datetime = None):
        """Sell shares of a stock"""
        if timestamp is None:
            timestamp = datetime.now()
            
        if symbol not in self.positions:
            raise ValueError(f"No position in {symbol}")
            
        if shares > self.positions[symbol]['shares']:
            raise ValueError(f"Cannot sell {shares} shares, only own {self.positions[symbol]['shares']}")
            
        proceeds = shares * price
        self.cash += proceeds
        
        self.positions[symbol]['shares'] -= shares
        if self.positions[symbol]['shares'] == 0:
            del self.positions[symbol]
            
        self.transactions.append({
            'timestamp': timestamp,
            'action': 'sell',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'total': proceeds
        })
        
    def update_prices(self, prices: Dict[str, float]):
        """Update last known prices for all positions"""
        for symbol in self.positions:
            if symbol in prices:
                self.positions[symbol]['last_price'] = prices[symbol]
                
    def get_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        stock_value = sum(
            pos['shares'] * pos['last_price'] 
            for pos in self.positions.values()
        )
        return self.cash + stock_value
        
    def get_total_return(self) -> float:
        """Calculate total return percentage"""
        current_value = self.get_portfolio_value()
        return ((current_value - self.initial_cash) / self.initial_cash) * 100
        
    def get_positions_summary(self) -> List[Dict]:
        """Get summary of all positions"""
        summary = []
        for symbol, pos in self.positions.items():
            current_value = pos['shares'] * pos['last_price']
            cost_basis = pos['shares'] * pos['avg_cost']
            pnl = current_value - cost_basis
            pnl_pct = (pnl / cost_basis) * 100 if cost_basis > 0 else 0
            
            summary.append({
                'symbol': symbol,
                'shares': pos['shares'],
                'avg_cost': pos['avg_cost'],
                'last_price': pos['last_price'],
                'current_value': current_value,
                'cost_basis': cost_basis,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
        return summary
        
    def to_dict(self) -> Dict:
        """Serialize portfolio to dictionary"""
        return {
            'cash': self.cash,
            'initial_cash': self.initial_cash,
            'positions': self.positions,
            'transactions': [
                {**tx, 'timestamp': tx['timestamp'].isoformat()} 
                for tx in self.transactions
            ],
            'portfolio_value': self.get_portfolio_value(),
            'total_return': self.get_total_return()
        }
        
    @classmethod
    def from_dict(cls, data: Dict):
        """Deserialize portfolio from dictionary"""
        portfolio = cls(data['initial_cash'])
        portfolio.cash = data['cash']
        portfolio.positions = data['positions']
        portfolio.transactions = [
            {**tx, 'timestamp': datetime.fromisoformat(tx['timestamp'])}
            for tx in data['transactions']
        ]
        return portfolio

class PortfolioSimulator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def simulate_strategy(self, 
                         symbols: List[str], 
                         start_date: str, 
                         end_date: str,
                         strategy_func,
                         initial_cash: float = 100000.0) -> Portfolio:
        """
        Simulate a trading strategy over historical data
        
        Args:
            symbols: List of stock symbols to trade
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            strategy_func: Function that takes (symbol, data) and returns buy/sell signals
            initial_cash: Starting cash amount
        """
        portfolio = Portfolio(initial_cash)
        
        # Get historical data for all symbols
        conn = sqlite3.connect(self.db_path)
        
        for symbol in symbols:
            try:
                query = f"""
                SELECT Date, Open, High, Low, Close, Volume 
                FROM {symbol} 
                WHERE Date BETWEEN ? AND ? 
                ORDER BY Date
                """
                df = pd.read_sql_query(query, conn, params=[start_date, end_date])
                df['Date'] = pd.to_datetime(df['Date'])
                
                if df.empty:
                    continue
                    
                # Apply strategy to each day
                for idx, row in df.iterrows():
                    signal = strategy_func(symbol, row, df.iloc[:idx+1])
                    
                    if signal == 'buy' and portfolio.cash >= row['Close'] * 100:  # Buy 100 shares
                        try:
                            portfolio.buy(symbol, 100, row['Close'], row['Date'])
                        except ValueError:
                            pass  # Not enough cash
                            
                    elif signal == 'sell' and symbol in portfolio.positions:
                        shares_to_sell = min(100, portfolio.positions[symbol]['shares'])
                        if shares_to_sell > 0:
                            portfolio.sell(symbol, shares_to_sell, row['Close'], row['Date'])
                            
                    # Update portfolio value tracking
                    current_prices = {s: row['Close'] if s == symbol else 
                                    portfolio.positions.get(s, {}).get('last_price', 0) 
                                    for s in portfolio.positions.keys()}
                    portfolio.update_prices(current_prices)
                    
            except Exception as e:
                print(f"Error simulating {symbol}: {e}")
                continue
                
        conn.close()
        return portfolio
        
    def backtest_agent_decisions(self, 
                                start_date: str, 
                                end_date: str,
                                initial_cash: float = 100000.0) -> Portfolio:
        """
        Backtest the agent's decision-making over historical data
        """
        from modeling.agent import StockAgent
        
        portfolio = Portfolio(initial_cash)
        agent = StockAgent(self.db_path)
        
        # Get all available symbols
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        symbols = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        
        # Simulate day by day
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end_date_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            
            for symbol in symbols[:5]:  # Limit to first 5 symbols for demo
                try:
                    # Get agent decision for this symbol on this date
                    decision_result = agent.decide(f"Should I buy {symbol}?")
                    
                    if isinstance(decision_result, dict):
                        decision = decision_result.get('decision', 'wait')
                        confidence = decision_result.get('confidence', 0)
                        
                        # Get price for this date
                        query = f"SELECT Close FROM {symbol} WHERE Date = ?"
                        cursor.execute(query, (date_str,))
                        result = cursor.fetchone()
                        
                        if result:
                            price = result[0]
                            
                            # Execute trades based on agent decision and confidence
                            if decision == 'buy' and confidence > 0.6:
                                shares = min(100, int(portfolio.cash / price))
                                if shares > 0:
                                    try:
                                        portfolio.buy(symbol, shares, price, current_date)
                                    except ValueError:
                                        pass
                                        
                            elif decision == 'sell' and symbol in portfolio.positions:
                                shares = min(50, portfolio.positions[symbol]['shares'])
                                if shares > 0:
                                    portfolio.sell(symbol, shares, price, current_date)
                                    
                except Exception as e:
                    continue
                    
            current_date += timedelta(days=1)
            
        conn.close()
        return portfolio

# Simple strategy examples
def simple_rsi_strategy(symbol: str, current_data: pd.Series, historical_data: pd.DataFrame):
    """Simple RSI-based strategy"""
    if len(historical_data) < 14:
        return 'wait'
        
    # Calculate simple RSI
    closes = historical_data['Close'].values
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
            
    if len(gains) < 14:
        return 'wait'
        
    avg_gain = sum(gains[-14:]) / 14
    avg_loss = sum(losses[-14:]) / 14
    
    if avg_loss == 0:
        return 'wait'
        
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    if rsi < 30:
        return 'buy'
    elif rsi > 70:
        return 'sell'
    else:
        return 'wait'
