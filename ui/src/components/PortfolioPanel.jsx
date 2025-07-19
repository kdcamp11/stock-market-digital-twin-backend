import React, { useState, useEffect } from 'react';
import { apiUrl } from '../api';

const PortfolioPanel = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [backtestResults, setBacktestResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [backtestParams, setBacktestParams] = useState({
    start_date: '2023-01-01',
    end_date: '2023-12-31',
    initial_cash: 100000,
    strategy: 'agent',
    symbols: ['AAPL', 'TSLA', 'MSFT']
  });

  useEffect(() => {
    loadDemoPortfolio();
  }, []);

  const loadDemoPortfolio = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/portfolio/demo`);
      const data = await response.json();
      if (data.status === 'success') {
        setPortfolio(data);
      }
    } catch (error) {
      console.error('Error loading demo portfolio:', error);
    }
  };

  const runBacktest = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/portfolio/backtest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(backtestParams)
      });
      const data = await response.json();
      if (data.status === 'success') {
        setBacktestResults(data);
      } else {
        alert(`Backtest failed: ${data.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error running backtest:', error);
      alert('Error running backtest');
    }
    setLoading(false);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatPercent = (percent) => {
    const color = percent >= 0 ? '#28a745' : '#dc3545';
    const sign = percent >= 0 ? '+' : '';
    return (
      <span style={{ color, fontWeight: 'bold' }}>
        {sign}{percent.toFixed(2)}%
      </span>
    );
  };

  return (
    <div>
      <h2>Portfolio Management</h2>

      {/* Demo Portfolio Section */}
      <div style={{ marginBottom: '30px' }}>
        <h3>Demo Portfolio</h3>
        {portfolio ? (
          <div style={{
            padding: '20px',
            border: '1px solid #ddd',
            borderRadius: '8px',
            backgroundColor: '#f8f9fa'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
              <div>
                <strong>Portfolio Value:</strong><br />
                {formatCurrency(portfolio.portfolio.portfolio_value)}
              </div>
              <div>
                <strong>Cash:</strong><br />
                {formatCurrency(portfolio.portfolio.cash)}
              </div>
              <div>
                <strong>Total Return:</strong><br />
                {formatPercent(portfolio.portfolio.total_return)}
              </div>
            </div>

            <h4>Positions</h4>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#e9ecef' }}>
                    <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Symbol</th>
                    <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Shares</th>
                    <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Avg Cost</th>
                    <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Last Price</th>
                    <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Value</th>
                    <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>P&L</th>
                    <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.positions.map(pos => (
                    <tr key={pos.symbol}>
                      <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>{pos.symbol}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>{pos.shares}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>{formatCurrency(pos.avg_cost)}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>{formatCurrency(pos.last_price)}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>{formatCurrency(pos.current_value)}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>
                        <span style={{ color: pos.pnl >= 0 ? '#28a745' : '#dc3545' }}>
                          {formatCurrency(pos.pnl)}
                        </span>
                      </td>
                      <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>
                        {formatPercent(pos.pnl_pct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div>Loading demo portfolio...</div>
        )}
      </div>

      {/* Backtest Section */}
      <div style={{ marginBottom: '30px' }}>
        <h3>Strategy Backtesting</h3>
        <div style={{
          padding: '20px',
          border: '1px solid #ddd',
          borderRadius: '8px',
          backgroundColor: '#fff'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Start Date:</label>
              <input
                type="date"
                value={backtestParams.start_date}
                onChange={(e) => setBacktestParams(prev => ({ ...prev, start_date: e.target.value }))}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>End Date:</label>
              <input
                type="date"
                value={backtestParams.end_date}
                onChange={(e) => setBacktestParams(prev => ({ ...prev, end_date: e.target.value }))}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Initial Cash:</label>
              <input
                type="number"
                value={backtestParams.initial_cash}
                onChange={(e) => setBacktestParams(prev => ({ ...prev, initial_cash: parseInt(e.target.value) }))}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Strategy:</label>
              <select
                value={backtestParams.strategy}
                onChange={(e) => setBacktestParams(prev => ({ ...prev, strategy: e.target.value }))}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              >
                <option value="agent">AI Agent Decisions</option>
                <option value="rsi">RSI Strategy</option>
              </select>
            </div>
          </div>

          <button
            onClick={runBacktest}
            disabled={loading}
            style={{
              padding: '12px 24px',
              backgroundColor: loading ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            {loading ? 'Running Backtest...' : 'Run Backtest'}
          </button>
        </div>

        {/* Backtest Results */}
        {backtestResults && (
          <div style={{
            marginTop: '20px',
            padding: '20px',
            border: '1px solid #ddd',
            borderRadius: '8px',
            backgroundColor: '#f8f9fa'
          }}>
            <h4>Backtest Results</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
              <div>
                <strong>Final Portfolio Value:</strong><br />
                {formatCurrency(backtestResults.portfolio.portfolio_value)}
              </div>
              <div>
                <strong>Total Return:</strong><br />
                {formatPercent(backtestResults.portfolio.total_return)}
              </div>
              <div>
                <strong>Final Cash:</strong><br />
                {formatCurrency(backtestResults.portfolio.cash)}
              </div>
              <div>
                <strong>Total Transactions:</strong><br />
                {backtestResults.portfolio.transactions.length}
              </div>
            </div>

            {backtestResults.positions && backtestResults.positions.length > 0 && (
              <>
                <h5>Final Positions</h5>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#e9ecef' }}>
                        <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Symbol</th>
                        <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Shares</th>
                        <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>P&L</th>
                        <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>P&L %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {backtestResults.positions.map(pos => (
                        <tr key={pos.symbol}>
                          <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>{pos.symbol}</td>
                          <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>{pos.shares}</td>
                          <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>
                            <span style={{ color: pos.pnl >= 0 ? '#28a745' : '#dc3545' }}>
                              {formatCurrency(pos.pnl)}
                            </span>
                          </td>
                          <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>
                            {formatPercent(pos.pnl_pct)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}

            {backtestResults.transactions && backtestResults.transactions.length > 0 && (
              <>
                <h5>Recent Transactions</h5>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#e9ecef' }}>
                        <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Date</th>
                        <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Action</th>
                        <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Symbol</th>
                        <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Shares</th>
                        <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Price</th>
                        <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {backtestResults.transactions.map((tx, idx) => (
                        <tr key={idx}>
                          <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                            {new Date(tx.timestamp).toLocaleDateString()}
                          </td>
                          <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                            <span style={{
                              padding: '2px 6px',
                              borderRadius: '10px',
                              fontSize: '12px',
                              backgroundColor: tx.action === 'buy' ? '#d4edda' : '#f8d7da',
                              color: tx.action === 'buy' ? '#155724' : '#721c24'
                            }}>
                              {tx.action.toUpperCase()}
                            </span>
                          </td>
                          <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold' }}>{tx.symbol}</td>
                          <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>{tx.shares}</td>
                          <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>{formatCurrency(tx.price)}</td>
                          <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>{formatCurrency(tx.total)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PortfolioPanel;
