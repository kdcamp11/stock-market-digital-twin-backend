"""
Agentic AI layer: interprets plain-language goals/questions, reasons over twin state, and outputs a decision.
"""
import re
from modeling.twin_state import TwinState
from modeling.twin_state_query_example import load_data

class StockAgent:
    def __init__(self, db_path):
        """StockAgent requires explicit db_path for SQLite database."""
        self.db_path = db_path

    def parse_goal(self, goal):
        # Reload known symbols from DB every time
        self.known_symbols = set(get_symbols(self.db_path))
        # Extract likely stock symbols (all caps, 1-5 letters, not common English words)
        words = re.findall(r'\b[A-Z]{1,5}\b', goal)
        symbols = [w for w in words if w in self.known_symbols]
        action = None
        if 'buy' in goal.lower():
            action = 'buy'
        elif 'sell' in goal.lower():
            action = 'sell'
        return symbols, action

    def get_twin_state(self, symbol):
        df = load_data(symbol, self.db_path)
        if df is None or df.empty:
            return None
        twin = TwinState(df)
        return twin.get_state()

    def decide(self, goal):
        symbols, _ = self.parse_goal(goal)
        if not symbols:
            return {'decision': 'wait', 'confidence': 0.0, 'explanation': 'No symbol found in request.'}
        results = {}
        for symbol in symbols:
            state = self.get_twin_state(symbol)
            if state is None:
                results[symbol] = {
                    'decision': 'wait',
                    'confidence': 0.0,
                    'explanation': f'No data found for {symbol}.'
                }
                continue
            decision, confidence, explanation = self.reason(state)
            results[symbol] = {
                'decision': decision,
                'confidence': confidence,
                'explanation': explanation
            }
        return results if len(results) > 1 else list(results.values())[0]

    def reason(self, state):
        # Modular: add more rules easily
        bullish = []
        bearish = []
        neutral = []
        explain = []

        # Example: bullish signals
        if state['Above_EMA_9'] and state['Above_EMA_20'] and state['Above_VWAP']:
            bullish.append('Price above EMAs and VWAP')
        if state['MACD_Cross']:
            bullish.append('MACD bullish crossover')
        if state['Golden_Cross']:
            bullish.append('Golden cross event')
        if state['RSI'] < 35:
            bullish.append('RSI oversold')
        if 'EMA bounce' in state.get('Signals', []):
            bullish.append('EMA bounce')
        if state.get('Squeeze_On', False):
            bullish.append('TTM Squeeze (potential breakout)')

        # Bearish signals
        if not state['Above_EMA_9'] and not state['Above_EMA_20'] and not state['Above_VWAP']:
            bearish.append('Price below EMAs and VWAP')
        if not state['MACD_Cross']:
            bearish.append('MACD bearish or no cross')
        if state['RSI'] > 70:
            bearish.append('RSI overbought')
        if state['Trend'] == 'Trending Down':
            bearish.append('Downtrend')
        if state.get('Squeeze_On', False):
            bearish.append('TTM Squeeze (potential breakdown)')

        # Confidence: fraction of signals that align
        n_bull = len(bullish)
        n_bear = len(bearish)
        n_total = n_bull + n_bear
        confidence = 0.0
        if n_total > 0:
            confidence = max(n_bull, n_bear) / n_total

        # Decision logic
        if n_bull >= 3 and n_bull > n_bear:
            decision = 'buy'
            explain = bullish
        elif n_bear >= 3 and n_bear > n_bull:
            decision = 'sell'
            explain = bearish
        elif n_total == 0 or abs(n_bull - n_bear) < 2:
            decision = 'wait'
            explain = ['Signals are mixed or unclear. No strong recommendation.']
        else:
            decision = 'wait'
            explain = ['No clear alignment of signals.']

        return decision, round(confidence, 2), '; '.join(explain)
