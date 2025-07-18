"""
Alert logging and deduplication.
"""
import json
import os

class AlertLogger:
    def __init__(self, log_file='alerts.log'):
        self.log_file = log_file
        self.logged = set()
        if os.path.exists(log_file):
            with open(log_file) as f:
                for line in f:
                    try:
                        rec = json.loads(line.strip())
                        self.logged.add(rec['alert_id'])
                    except Exception:
                        continue
    def is_duplicate(self, alert_id):
        return alert_id in self.logged
    def log_alert(self, alert_id, alert):
        self.logged.add(alert_id)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps({'alert_id': alert_id, **alert}) + '\n')
