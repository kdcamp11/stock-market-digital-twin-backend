"""
All indicator calculations (EMA, SMA, VWAP, MACD, RSI, TTM Squeeze, etc.)
"""
import pandas as pd
import pandas_ta as ta

# EMA, SMA, MACD, RSI

def add_ema(df, lengths=[9, 20, 50]):
    for length in lengths:
        df[f'EMA_{length}'] = ta.ema(df['Close'], length)
    return df

def add_sma(df, length=20):
    df[f'SMA_{length}'] = ta.sma(df['Close'], length)
    return df

def add_vwap(df):
    df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
    return df

def add_macd(df):
    macd = ta.macd(df['Close'])
    df = pd.concat([df, macd], axis=1)
    return df

def add_rsi(df, length=14):
    df['RSI'] = ta.rsi(df['Close'], length)
    return df

def add_ttm_squeeze(df):
    # TTM Squeeze: Use Bollinger Bands and Keltner Channels
    bb = ta.bbands(df['Close'])
    kc = ta.kc(df['High'], df['Low'], df['Close'])
    df = pd.concat([df, bb, kc], axis=1)
    # Squeeze is on when lower BB > lower KC and upper BB < upper KC
    df['Squeeze_On'] = (df['BBL_5_2.0'] > df['KCLe_20_2']) & (df['BBU_5_2.0'] < df['KCUe_20_2'])
    df['Squeeze_Off'] = (df['BBL_5_2.0'] < df['KCLe_20_2']) & (df['BBU_5_2.0'] > df['KCUe_20_2'])
    return df
