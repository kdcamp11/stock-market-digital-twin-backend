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

    def build_state(self):
        latest = self.df.iloc[-1]
        state = {
            'Above_EMA_9': latest['Close'] > latest['EMA_9'],
            'Above_EMA_20': latest['Close'] > latest['EMA_20'],
            'Above_EMA_50': latest['Close'] > latest['EMA_50'],
            'Above_SMA_20': latest['Close'] > latest['SMA_20'],
            'Above_VWAP': latest['Close'] > latest['VWAP'],
            'MACD_Cross': latest['MACD_12_26_9'] > latest['MACDs_12_26_9'],
            'RSI': latest['RSI'],
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
        if latest['Golden_Cross']:
            signals.append('Golden Cross')
        if latest['MACD_12_26_9'] > latest['MACDs_12_26_9']:
            signals.append('MACD Bullish')
        if latest['RSI'] < 30:
            signals.append('RSI Oversold')
        if latest['RSI'] > 70:
            signals.append('RSI Overbought')
        if latest.get('Squeeze_On', False):
            signals.append('TTM Squeeze')
        return signals

    def confirm_direction(self, latest):
        confirmations = 0
        if latest['Close'] > latest['EMA_9']:
            confirmations += 1
        if latest['Close'] > latest['VWAP']:
            confirmations += 1
        if latest['MACD_12_26_9'] > latest['MACDs_12_26_9']:
            confirmations += 1
        if latest['Golden_Cross']:
            confirmations += 1
        return confirmations >= 3

    def get_state(self):
        return self.state
