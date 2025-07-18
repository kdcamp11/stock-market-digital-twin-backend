"""
Pattern and event detection (crossovers, squeezes, bounces, etc.)
"""
import pandas as pd

def detect_golden_cross(df, fast='EMA_50', slow='EMA_200'):
    cross = (df[fast] > df[slow]) & (df[fast].shift(1) <= df[slow].shift(1))
    df['Golden_Cross'] = cross
    return df

def detect_support_resistance(df, window=20):
    df['Support'] = df['Low'].rolling(window, min_periods=1).min()
    df['Resistance'] = df['High'].rolling(window, min_periods=1).max()
    return df

def detect_trend(df, ema_length=20):
    # Simple trend: price above EMA is uptrend, below is downtrend
    df['Trend'] = 'Consolidating'
    df.loc[df['Close'] > df[f'EMA_{ema_length}'], 'Trend'] = 'Trending Up'
    df.loc[df['Close'] < df[f'EMA_{ema_length}'], 'Trend'] = 'Trending Down'
    return df
