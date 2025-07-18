"""
Example alert rule functions for use in alert config.
"""
def macd_bullish_crossover(state):
    return state.get('MACD_Cross', False)
def macd_confidence(state):
    return 0.8 if state.get('MACD_Cross', False) else 0.0
def macd_summary(state):
    return f"MACD bullish crossover detected. MACD: {state.get('MACD_12_26_9')}, Signal: {state.get('MACDs_12_26_9')}"
def rsi_oversold(state):
    return state.get('RSI', 100) < 30
def rsi_confidence(state):
    rsi = state.get('RSI', 100)
    if rsi < 20:
        return 1.0
    elif rsi < 30:
        return 0.8
    else:
        return 0.0
def rsi_summary(state):
    return f"RSI oversold: {state.get('RSI')}"
