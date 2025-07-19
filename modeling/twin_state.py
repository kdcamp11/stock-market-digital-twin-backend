"""
TwinState object and logic
"""
import pandas as pd
from modeling.indicators import add_ema, add_sma, add_vwap, add_macd, add_rsi, add_ttm_squeeze
from modeling.patterns import detect_golden_cross, detect_support_resistance, detect_trend

class TwinState:
    def __init__(self, df):
        self.df = df.copy()
        self.calculate_indicators()
        self.detect_patterns()
        self.state = self.build_state()

    def calculate_indicators(self):
        self.df = add_ema(self.df, [9, 20, 50])
        self.df = add_sma(self.df, 20)
        self.df = add_vwap(self.df)
        self.df = add_macd(self.df)
        self.df = add_rsi(self.df)
        self.df = add_ttm_squeeze(self.df)

    def detect_patterns(self):
        self.df = detect_golden_cross(self.df, 'EMA_50', 'EMA_20')
        self.df = detect_support_resistance(self.df)
        self.df = detect_trend(self.df, 20)

    def safe_compare(self, val1, val2, default=False):
        """Safely compare two values, handling None cases"""
        try:
            if val1 is None or val2 is None:
                return default
            return val1 > val2
        except (TypeError, ValueError):
            return default
    
    def safe_get(self, series, key, default=0):
        """Safely get value from series, handling None and missing keys"""
        try:
            val = series.get(key, default)
            return val if val is not None else default
        except (KeyError, AttributeError):
            return default

    def build_state(self):
        latest = self.df.iloc[-1]
        state = {
            'Above_EMA_9': self.safe_compare(latest['Close'], self.safe_get(latest, 'EMA_9')),
            'Above_EMA_20': self.safe_compare(latest['Close'], self.safe_get(latest, 'EMA_20')),
            'Above_EMA_50': self.safe_compare(latest['Close'], self.safe_get(latest, 'EMA_50')),
            'Above_SMA_20': self.safe_compare(latest['Close'], self.safe_get(latest, 'SMA_20')),
            'Above_VWAP': self.safe_compare(latest['Close'], self.safe_get(latest, 'VWAP')),
            'MACD_Cross': self.safe_compare(self.safe_get(latest, 'MACD_12_26_9'), self.safe_get(latest, 'MACDs_12_26_9')),
            'RSI': self.safe_get(latest, 'RSI', 50),
            'Squeeze_On': latest.get('Squeeze_On', False),
            'Golden_Cross': latest.get('Golden_Cross', False),
            'Trend': latest['Trend'],
            'Support': latest['Support'],
            'Resistance': latest['Resistance'],
            'Signals': self.get_signals(latest),
            'Confirmation': self.confirm_direction(latest)
        }
        return state

    def get_signals(self, latest):
        signals = []
        if latest.get('Golden_Cross', False):
            signals.append('Golden Cross')
        if self.safe_compare(self.safe_get(latest, 'MACD_12_26_9'), self.safe_get(latest, 'MACDs_12_26_9')):
            signals.append('MACD Bullish')
        rsi = self.safe_get(latest, 'RSI', 50)
        if rsi < 30:
            signals.append('RSI Oversold')
        if rsi > 70:
            signals.append('RSI Overbought')
        if latest.get('Squeeze_On', False):
            signals.append('TTM Squeeze')
        return signals

    def confirm_direction(self, latest):
        confirmations = 0
        if self.safe_compare(latest['Close'], self.safe_get(latest, 'EMA_9')):
            confirmations += 1
        if self.safe_compare(latest['Close'], self.safe_get(latest, 'VWAP')):
            confirmations += 1
        if self.safe_compare(self.safe_get(latest, 'MACD_12_26_9'), self.safe_get(latest, 'MACDs_12_26_9')):
            confirmations += 1
        if latest.get('Golden_Cross', False):
            confirmations += 1
        return confirmations >= 3

    def get_state(self):
        return self.state
