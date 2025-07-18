"""
Example: Run AlertMonitor once to show alert triggering for AAPL and TSLA using sample rules.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from alerts.monitor import AlertMonitor

if __name__ == "__main__":
    monitor = AlertMonitor(config_path="alert_config.yaml")
    # Run check once instead of infinite loop for demonstration
    monitor.check_all_symbols()
    print("\nAlert check complete. See alerts.log for any triggered alerts.")
