"""
Advanced Technical Indicators for Stock Market Digital Twin
Includes MACD, Bollinger Bands, VWAP, TTM Squeeze, Stochastic RSI, ATR, Fibonacci zones
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import pandas_ta as ta

class TechnicalIndicators:
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV DataFrame
        Expected columns: Date, Open, High, Low, Close, Volume
        """
        self.df = df.copy()
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df = self.df.sort_values('Date').reset_index(drop=True)
        
    def calculate_all_indicators(self) -> pd.DataFrame:
        """Calculate all technical indicators and return enhanced DataFrame"""
        df = self.df.copy()
        
        # Basic indicators
        df = self._add_moving_averages(df)
        df = self._add_rsi(df)
        
        # Advanced indicators
        df = self._add_macd(df)
        df = self._add_bollinger_bands(df)
        df = self._add_vwap(df)
        df = self._add_stochastic_rsi(df)
        df = self._add_atr(df)
        df = self._add_ttm_squeeze(df)
        df = self._add_fibonacci_levels(df)
        
        # Signal generation
        df = self._generate_signals(df)
        
        return df
    
    def _add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add various moving averages"""
        df['SMA_20'] = ta.sma(df['Close'], length=20)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        df['EMA_12'] = ta.ema(df['Close'], length=12)
        df['EMA_26'] = ta.ema(df['Close'], length=26)
        df['EMA_50'] = ta.ema(df['Close'], length=50)
        return df
    
    def _add_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add RSI indicator"""
        df['RSI'] = ta.rsi(df['Close'], length=14)
        return df
    
    def _add_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add MACD indicator"""
        macd_data = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        df['MACD'] = macd_data['MACD_12_26_9']
        df['MACD_Signal'] = macd_data['MACDs_12_26_9']
        df['MACD_Histogram'] = macd_data['MACDh_12_26_9']
        
        # MACD signals
        df['MACD_Bullish'] = (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
        df['MACD_Bearish'] = (df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
        
        return df
    
    def _add_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Bollinger Bands"""
        bb_data = ta.bbands(df['Close'], length=20, std=2)
        df['BB_Upper'] = bb_data['BBU_20_2.0']
        df['BB_Middle'] = bb_data['BBM_20_2.0']
        df['BB_Lower'] = bb_data['BBL_20_2.0']
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # Bollinger Band signals
        df['BB_Squeeze'] = df['BB_Width'] < df['BB_Width'].rolling(20).mean()
        df['BB_Breakout_Upper'] = df['Close'] > df['BB_Upper']
        df['BB_Breakout_Lower'] = df['Close'] < df['BB_Lower']
        
        return df
    
    def _add_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Volume Weighted Average Price"""
        df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
        
        # VWAP signals
        df['Above_VWAP'] = df['Close'] > df['VWAP']
        df['VWAP_Cross_Up'] = (df['Close'] > df['VWAP']) & (df['Close'].shift(1) <= df['VWAP'].shift(1))
        df['VWAP_Cross_Down'] = (df['Close'] < df['VWAP']) & (df['Close'].shift(1) >= df['VWAP'].shift(1))
        
        return df
    
    def _add_stochastic_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Stochastic RSI"""
        stoch_rsi = ta.stochrsi(df['Close'], length=14, rsi_length=14, k=3, d=3)
        df['StochRSI_K'] = stoch_rsi['STOCHRSIk_14_14_3_3']
        df['StochRSI_D'] = stoch_rsi['STOCHRSId_14_14_3_3']
        
        # Stochastic RSI signals
        df['StochRSI_Oversold'] = (df['StochRSI_K'] < 20) & (df['StochRSI_D'] < 20)
        df['StochRSI_Overbought'] = (df['StochRSI_K'] > 80) & (df['StochRSI_D'] > 80)
        df['StochRSI_Bullish_Cross'] = (df['StochRSI_K'] > df['StochRSI_D']) & (df['StochRSI_K'].shift(1) <= df['StochRSI_D'].shift(1))
        df['StochRSI_Bearish_Cross'] = (df['StochRSI_K'] < df['StochRSI_D']) & (df['StochRSI_K'].shift(1) >= df['StochRSI_D'].shift(1))
        
        return df
    
    def _add_atr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Average True Range"""
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        df['ATR_Percent'] = (df['ATR'] / df['Close']) * 100
        
        # Volatility signals
        df['High_Volatility'] = df['ATR_Percent'] > df['ATR_Percent'].rolling(50).quantile(0.8)
        df['Low_Volatility'] = df['ATR_Percent'] < df['ATR_Percent'].rolling(50).quantile(0.2)
        
        return df
    
    def _add_ttm_squeeze(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add TTM Squeeze indicator"""
        # Keltner Channels
        kc_data = ta.kc(df['High'], df['Low'], df['Close'], length=20, scalar=1.5)
        df['KC_Upper'] = kc_data['KCUe_20_1.5']
        df['KC_Lower'] = kc_data['KCLe_20_1.5']
        
        # TTM Squeeze occurs when Bollinger Bands are inside Keltner Channels
        df['TTM_Squeeze'] = (df['BB_Upper'] < df['KC_Upper']) & (df['BB_Lower'] > df['KC_Lower'])
        df['TTM_Squeeze_Release'] = (~df['TTM_Squeeze']) & (df['TTM_Squeeze'].shift(1))
        
        # Momentum oscillator for TTM Squeeze
        df['TTM_Momentum'] = ta.linreg(df['Close'] - ((df['High'] + df['Low']) / 2 + df['EMA_12']) / 2, length=20)
        df['TTM_Momentum_Up'] = df['TTM_Momentum'] > 0
        df['TTM_Momentum_Down'] = df['TTM_Momentum'] < 0
        
        return df
    
    def _add_fibonacci_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Fibonacci retracement levels"""
        # Calculate over rolling 50-day periods
        window = 50
        
        df['Fib_High'] = df['High'].rolling(window).max()
        df['Fib_Low'] = df['Low'].rolling(window).min()
        df['Fib_Range'] = df['Fib_High'] - df['Fib_Low']
        
        # Fibonacci levels
        fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        for level in fib_levels:
            df[f'Fib_{int(level*1000)}'] = df['Fib_High'] - (df['Fib_Range'] * level)
        
        # Fibonacci signals
        df['Near_Fib_Support'] = False
        df['Near_Fib_Resistance'] = False
        
        for level in fib_levels:
            fib_col = f'Fib_{int(level*1000)}'
            tolerance = df['ATR'] * 0.5  # Use ATR for dynamic tolerance
            
            # Near support (price close to fib level from above)
            near_support = (df['Close'] <= df[fib_col] + tolerance) & (df['Close'] >= df[fib_col] - tolerance) & (df['Close'] < df['Close'].shift(1))
            df['Near_Fib_Support'] |= near_support
            
            # Near resistance (price close to fib level from below)
            near_resistance = (df['Close'] <= df[fib_col] + tolerance) & (df['Close'] >= df[fib_col] - tolerance) & (df['Close'] > df['Close'].shift(1))
            df['Near_Fib_Resistance'] |= near_resistance
        
        return df
    
    def _generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate comprehensive buy/sell signals"""
        # Initialize signal columns
        df['Signal_Strength'] = 0
        df['Buy_Signals'] = []
        df['Sell_Signals'] = []
        
        # Bullish signals
        bullish_conditions = [
            ('MACD_Bullish', 'MACD Bullish Cross'),
            ('RSI < 30', 'RSI Oversold'),
            ('BB_Breakout_Lower', 'BB Oversold'),
            ('VWAP_Cross_Up', 'VWAP Breakout'),
            ('StochRSI_Bullish_Cross & StochRSI_Oversold', 'StochRSI Bullish'),
            ('TTM_Squeeze_Release & TTM_Momentum_Up', 'TTM Squeeze Release Up'),
            ('Near_Fib_Support', 'Fibonacci Support'),
            ('Close > SMA_20 & SMA_20 > SMA_50', 'Moving Average Bullish')
        ]
        
        # Bearish signals
        bearish_conditions = [
            ('MACD_Bearish', 'MACD Bearish Cross'),
            ('RSI > 70', 'RSI Overbought'),
            ('BB_Breakout_Upper', 'BB Overbought'),
            ('VWAP_Cross_Down', 'VWAP Breakdown'),
            ('StochRSI_Bearish_Cross & StochRSI_Overbought', 'StochRSI Bearish'),
            ('TTM_Squeeze_Release & TTM_Momentum_Down', 'TTM Squeeze Release Down'),
            ('Near_Fib_Resistance', 'Fibonacci Resistance'),
            ('Close < SMA_20 & SMA_20 < SMA_50', 'Moving Average Bearish')
        ]
        
        # Evaluate conditions and assign signals
        for i in range(len(df)):
            buy_signals = []
            sell_signals = []
            signal_strength = 0
            
            # Check bullish conditions
            for condition, name in bullish_conditions:
                try:
                    if eval(condition.replace('RSI', f'df.iloc[{i}]["RSI"]')
                           .replace('Close', f'df.iloc[{i}]["Close"]')
                           .replace('SMA_20', f'df.iloc[{i}]["SMA_20"]')
                           .replace('SMA_50', f'df.iloc[{i}]["SMA_50"]')
                           .replace('MACD_Bullish', f'df.iloc[{i}]["MACD_Bullish"]')
                           .replace('BB_Breakout_Lower', f'df.iloc[{i}]["BB_Breakout_Lower"]')
                           .replace('VWAP_Cross_Up', f'df.iloc[{i}]["VWAP_Cross_Up"]')
                           .replace('StochRSI_Bullish_Cross', f'df.iloc[{i}]["StochRSI_Bullish_Cross"]')
                           .replace('StochRSI_Oversold', f'df.iloc[{i}]["StochRSI_Oversold"]')
                           .replace('TTM_Squeeze_Release', f'df.iloc[{i}]["TTM_Squeeze_Release"]')
                           .replace('TTM_Momentum_Up', f'df.iloc[{i}]["TTM_Momentum_Up"]')
                           .replace('Near_Fib_Support', f'df.iloc[{i}]["Near_Fib_Support"]')):
                        buy_signals.append(name)
                        signal_strength += 1
                except:
                    continue
            
            # Check bearish conditions
            for condition, name in bearish_conditions:
                try:
                    if eval(condition.replace('RSI', f'df.iloc[{i}]["RSI"]')
                           .replace('Close', f'df.iloc[{i}]["Close"]')
                           .replace('SMA_20', f'df.iloc[{i}]["SMA_20"]')
                           .replace('SMA_50', f'df.iloc[{i}]["SMA_50"]')
                           .replace('MACD_Bearish', f'df.iloc[{i}]["MACD_Bearish"]')
                           .replace('BB_Breakout_Upper', f'df.iloc[{i}]["BB_Breakout_Upper"]')
                           .replace('VWAP_Cross_Down', f'df.iloc[{i}]["VWAP_Cross_Down"]')
                           .replace('StochRSI_Bearish_Cross', f'df.iloc[{i}]["StochRSI_Bearish_Cross"]')
                           .replace('StochRSI_Overbought', f'df.iloc[{i}]["StochRSI_Overbought"]')
                           .replace('TTM_Squeeze_Release', f'df.iloc[{i}]["TTM_Squeeze_Release"]')
                           .replace('TTM_Momentum_Down', f'df.iloc[{i}]["TTM_Momentum_Down"]')
                           .replace('Near_Fib_Resistance', f'df.iloc[{i}]["Near_Fib_Resistance"]')):
                        sell_signals.append(name)
                        signal_strength -= 1
                except:
                    continue
            
            df.at[i, 'Buy_Signals'] = buy_signals
            df.at[i, 'Sell_Signals'] = sell_signals
            df.at[i, 'Signal_Strength'] = signal_strength
        
        # Generate final signals
        df['Final_Signal'] = 'HOLD'
        df.loc[df['Signal_Strength'] >= 3, 'Final_Signal'] = 'BUY'
        df.loc[df['Signal_Strength'] <= -3, 'Final_Signal'] = 'SELL'
        
        return df
    
    def get_current_signals(self) -> Dict:
        """Get current signals for the latest data point"""
        df_with_indicators = self.calculate_all_indicators()
        if df_with_indicators.empty:
            return {}
        
        latest = df_with_indicators.iloc[-1]
        
        return {
            'date': latest['Date'].strftime('%Y-%m-%d'),
            'close_price': latest['Close'],
            'signal': latest['Final_Signal'],
            'signal_strength': latest['Signal_Strength'],
            'buy_signals': latest['Buy_Signals'],
            'sell_signals': latest['Sell_Signals'],
            'indicators': {
                'RSI': latest['RSI'],
                'MACD': latest['MACD'],
                'MACD_Signal': latest['MACD_Signal'],
                'BB_Position': latest['BB_Position'],
                'VWAP': latest['VWAP'],
                'ATR_Percent': latest['ATR_Percent'],
                'TTM_Squeeze': latest['TTM_Squeeze'],
                'StochRSI_K': latest['StochRSI_K'],
                'StochRSI_D': latest['StochRSI_D']
            }
        }
    
    def get_backtest_data(self, initial_capital: float = 100000) -> Dict:
        """Generate backtest results with buy/sell signals"""
        df_with_indicators = self.calculate_all_indicators()
        
        # Simulate trading based on signals
        capital = initial_capital
        shares = 0
        trades = []
        portfolio_values = []
        
        for i, row in df_with_indicators.iterrows():
            date = row['Date']
            price = row['Close']
            signal = row['Final_Signal']
            
            # Execute trades
            if signal == 'BUY' and capital > price:
                shares_to_buy = int(capital * 0.95 / price)  # Use 95% of capital
                if shares_to_buy > 0:
                    cost = shares_to_buy * price
                    capital -= cost
                    shares += shares_to_buy
                    trades.append({
                        'date': date,
                        'action': 'BUY',
                        'price': price,
                        'shares': shares_to_buy,
                        'cost': cost
                    })
            
            elif signal == 'SELL' and shares > 0:
                proceeds = shares * price
                capital += proceeds
                trades.append({
                    'date': date,
                    'action': 'SELL',
                    'price': price,
                    'shares': shares,
                    'proceeds': proceeds
                })
                shares = 0
            
            # Calculate portfolio value
            portfolio_value = capital + (shares * price)
            portfolio_values.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'capital': capital,
                'shares': shares,
                'price': price
            })
        
        # Calculate performance metrics
        final_value = portfolio_values[-1]['portfolio_value'] if portfolio_values else initial_capital
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        return {
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'total_trades': len(trades),
            'trades': trades,
            'portfolio_values': portfolio_values,
            'indicators_data': df_with_indicators.to_dict('records')
        }
