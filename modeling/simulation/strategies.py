"""
Modular strategy logic for entry/exit signals.
"""
def ema_bounce_strategy(row, params):
    ema_length = params.get('ema_length', 20)
    rsi_thresh = params.get('rsi_thresh', 30)
    # Assumes row has 'Close', f'EMA_{ema_length}', and 'RSI'
    if row['Close'] > row[f'EMA_{ema_length}'] and row['RSI'] < rsi_thresh:
        return 'buy'
    elif row['Close'] < row[f'EMA_{ema_length}'] and row['RSI'] > 70:
        return 'sell'
    else:
        return 'hold'
