"""
Performance reporting for strategy simulation.
"""
def generate_report(trades, equity_curve, initial_cash):
    n_trades = len([t for t in trades if t['type'] == 'sell'])
    wins = [t for t in trades if t['type'] == 'sell' and t['pnl'] > 0]
    losses = [t for t in trades if t['type'] == 'sell' and t['pnl'] <= 0]
    total_return = (equity_curve[-1] - initial_cash) / initial_cash if equity_curve else 0
    win_rate = len(wins) / n_trades if n_trades > 0 else 0
    max_drawdown = 0
    peak = initial_cash
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak
        if dd > max_drawdown:
            max_drawdown = dd
    return {
        'total_return': total_return,
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'n_trades': n_trades
    }
