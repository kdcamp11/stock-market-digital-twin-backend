"""
Modular notification channels for alerts.
"""
def send_alert(alert, channels):
    # Example: print to console, but can extend to email, Slack, Discord, etc.
    for chan in channels:
        if chan == 'console':
            print(f"[ALERT] {alert['timestamp']} | {alert['symbol']} | {alert['rule']} | {alert['summary']} | Confidence: {alert['confidence']}")
        # Add more channel integrations here (email, Slack, Discord)
