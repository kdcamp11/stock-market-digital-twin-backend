"""
Core monitoring/alert logic for digital twin signals.
"""
import time
from .channels import send_alert
from .log import AlertLogger
from .simulate import simulate_trade
from .config import load_alert_config, get_alert_conditions
from . import rules
from twin_state_query_example import load_data
from twin_state import TwinState

class AlertMonitor:
    def __init__(self, config_path='alert_config.yaml'):
        self.config = load_alert_config(config_path)
        self.logger = AlertLogger(self.config.get('alert_log', 'alerts.log'))
        self.interval = self.config.get('check_interval', 300)  # default: 5 min

    def run(self):
        while True:
            self.check_all_symbols()
            time.sleep(self.interval)

    def check_all_symbols(self):
        # Map of rule names to functions from rules.py
        rule_func_map = {name: getattr(rules, name) for name in dir(rules) if not name.startswith('_')}
        for symbol, rule_list in self.config['symbols'].items():
            df = load_data(symbol, self.config['db_path'])
            if df is None or df.empty:
                continue
            twin = TwinState(df)
            state = twin.get_state()
            # Get latest date from DataFrame
            latest_row = df.iloc[-1]
            if 'Date' in df.columns:
                latest_date = str(latest_row['Date'])
            elif df.index.name and df.index.name.lower().startswith('date'):
                latest_date = str(df.index[-1])
            else:
                latest_date = time.strftime('%Y-%m-%d')
            for rule in get_alert_conditions(rule_list):
                cond_fn = rule_func_map.get(rule['condition'])
                conf_fn = rule_func_map.get(rule['confidence'])
                sum_fn = rule_func_map.get(rule['summary'])
                if cond_fn and cond_fn(state):
                    alert_id = f"{symbol}:{rule['name']}:{latest_date}"
                    if not self.logger.is_duplicate(alert_id):
                        alert = {
                            'symbol': symbol,
                            'rule': rule['name'],
                            'confidence': conf_fn(state) if conf_fn else 1.0,
                            'summary': sum_fn(state) if sum_fn else '',
                            'timestamp': latest_date,
                        }
                        send_alert(alert, self.config['channels'])
                        self.logger.log_alert(alert_id, alert)
                        if rule.get('simulate_trade') and alert['confidence'] >= rule.get('min_confidence', 0.7):
                            simulate_trade(alert)
