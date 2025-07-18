"""
Simulated trade execution when signal is strong.
"""
def simulate_trade(alert):
    print(f"[SIM TRADE] Would execute trade for {alert['symbol']} on {alert['rule']} (confidence: {alert['confidence']})")
    # Extend to log simulated trades
