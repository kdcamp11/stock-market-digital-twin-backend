"""
User-configurable alert rules and preferences.
"""
import yaml

def load_alert_config(path):
    with open(path) as f:
        return yaml.safe_load(f)

def get_alert_conditions(rules):
    # Example: return list of rule dicts with 'name', 'condition', 'confidence', 'summary', etc.
    # In real use, these would be more modular and user-defined.
    return rules
