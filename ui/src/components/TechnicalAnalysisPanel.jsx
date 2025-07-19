import React, { useState, useEffect } from 'react';
import { buildApiUrl } from '../api';

const TechnicalAnalysisPanel = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [timeframe, setTimeframe] = useState('1Day');
  const [period, setPeriod] = useState('6M');
  const [loading, setLoading] = useState(false);
  const [technicalData, setTechnicalData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [backtestData, setBacktestData] = useState(null);
  const [optionsData, setOptionsData] = useState(null);
  const [activeTab, setActiveTab] = useState('technical');

  const fetchTechnicalAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch(buildApiUrl(`/api/technical/${symbol}?timeframe=${timeframe}`));
      const data = await response.json();
      if (data.status === 'success') {
        setTechnicalData(data.analysis);
      }
    } catch (error) {
      console.error('Error fetching technical analysis:', error);
    }
    setLoading(false);
  };

  const fetchChartData = async () => {
    setLoading(true);
    try {
      const response = await fetch(buildApiUrl(`/api/chart/${symbol}?timeframe=${timeframe}&period=${period}`));
      const data = await response.json();
      if (data.status === 'success') {
        setChartData(data.chart_data);
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
    }
    setLoading(false);
  };

  const fetchBacktestData = async () => {
    setLoading(true);
    try {
      const response = await fetch(buildApiUrl(`/api/backtest/${symbol}?timeframe=${timeframe}`));
      const data = await response.json();
      if (data.status === 'success') {
        setBacktestData(data.backtest);
      }
    } catch (error) {
      console.error('Error fetching backtest data:', error);
    }
    setLoading(false);
  };

  const fetchOptionsData = async () => {
    setLoading(true);
    try {
      const [chainResponse, analysisResponse, strategiesResponse] = await Promise.all([
        fetch(buildApiUrl(`/api/options/${symbol}`)),
        fetch(buildApiUrl(`/api/options/analysis/${symbol}`)),
        fetch(buildApiUrl(`/api/options/strategies/${symbol}?outlook=BULLISH`))
      ]);

      const chainData = await chainResponse.json();
      const analysisData = await analysisResponse.json();
      const strategiesData = await strategiesResponse.json();

      setOptionsData({
        chain: chainData.status === 'success' ? chainData.options_chain : null,
        analysis: analysisData.status === 'success' ? analysisData.options_analysis : null,
        strategies: strategiesData.status === 'success' ? strategiesData.strategies : null
      });
    } catch (error) {
      console.error('Error fetching options data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (activeTab === 'technical') {
      fetchTechnicalAnalysis();
    } else if (activeTab === 'chart') {
      fetchChartData();
    } else if (activeTab === 'backtest') {
      fetchBacktestData();
    } else if (activeTab === 'options') {
      fetchOptionsData();
    }
  }, [symbol, timeframe, period, activeTab]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercent = (value) => {
    const color = value >= 0 ? '#28a745' : '#dc3545';
    const sign = value >= 0 ? '+' : '';
    return (
      <span style={{ color, fontWeight: 'bold' }}>
        {sign}{value.toFixed(2)}%
      </span>
    );
  };

  const getSignalColor = (signal) => {
    switch (signal) {
      case 'BUY': return '#28a745';
      case 'SELL': return '#dc3545';
      default: return '#ffc107';
    }
  };

  return (
    <div>
      <h2>Advanced Technical Analysis</h2>

      {/* Controls */}
      <div style={{ 
        marginBottom: '20px', 
        padding: '15px', 
        backgroundColor: '#f8f9fa', 
        borderRadius: '8px',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '15px'
      }}>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Symbol:</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            placeholder="Enter symbol"
          />
        </div>
        
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Timeframe:</label>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
          >
            <option value="1Min">1 Minute</option>
            <option value="5Min">5 Minutes</option>
            <option value="15Min">15 Minutes</option>
            <option value="1Hour">1 Hour</option>
            <option value="1Day">1 Day</option>
            <option value="1Week">1 Week</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Period:</label>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
          >
            <option value="1M">1 Month</option>
            <option value="3M">3 Months</option>
            <option value="6M">6 Months</option>
            <option value="1Y">1 Year</option>
            <option value="2Y">2 Years</option>
            <option value="5Y">5 Years</option>
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ marginBottom: '20px' }}>
        {['technical', 'chart', 'backtest', 'options'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '10px 20px',
              marginRight: '10px',
              backgroundColor: activeTab === tab ? '#007bff' : '#e9ecef',
              color: activeTab === tab ? 'white' : '#495057',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              textTransform: 'capitalize'
            }}
          >
            {tab === 'technical' ? 'Technical Analysis' : 
             tab === 'chart' ? 'Chart & Indicators' :
             tab === 'backtest' ? 'Backtest Results' : 'Options Analysis'}
          </button>
        ))}
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ fontSize: '18px', color: '#666' }}>Loading {activeTab} data...</div>
        </div>
      )}

      {/* Technical Analysis Tab */}
      {activeTab === 'technical' && technicalData && !loading && (
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: 'white' }}>
          <h3>Current Technical Analysis for {symbol}</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginBottom: '20px' }}>
            <div>
              <h4>Signal Summary</h4>
              <div style={{ 
                padding: '15px', 
                backgroundColor: getSignalColor(technicalData.signal), 
                color: 'white', 
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{technicalData.signal}</div>
                <div>Strength: {technicalData.signal_strength}</div>
                <div>Price: {formatCurrency(technicalData.close_price)}</div>
              </div>
            </div>

            <div>
              <h4>Key Indicators</h4>
              <div style={{ fontSize: '14px' }}>
                <div><strong>RSI:</strong> {technicalData.indicators.RSI?.toFixed(2) || 'N/A'}</div>
                <div><strong>MACD:</strong> {technicalData.indicators.MACD?.toFixed(4) || 'N/A'}</div>
                <div><strong>BB Position:</strong> {technicalData.indicators.BB_Position?.toFixed(2) || 'N/A'}</div>
                <div><strong>VWAP:</strong> {formatCurrency(technicalData.indicators.VWAP || 0)}</div>
                <div><strong>ATR %:</strong> {technicalData.indicators.ATR_Percent?.toFixed(2) || 'N/A'}%</div>
                <div><strong>TTM Squeeze:</strong> {technicalData.indicators.TTM_Squeeze ? 'Yes' : 'No'}</div>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <h4>Buy Signals</h4>
              <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                {technicalData.buy_signals && technicalData.buy_signals.length > 0 ? (
                  technicalData.buy_signals.map((signal, idx) => (
                    <div key={idx} style={{ 
                      padding: '5px 10px', 
                      margin: '5px 0', 
                      backgroundColor: '#d4edda', 
                      borderRadius: '4px',
                      fontSize: '14px'
                    }}>
                      {signal}
                    </div>
                  ))
                ) : (
                  <div style={{ color: '#666', fontStyle: 'italic' }}>No buy signals</div>
                )}
              </div>
            </div>

            <div>
              <h4>Sell Signals</h4>
              <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                {technicalData.sell_signals && technicalData.sell_signals.length > 0 ? (
                  technicalData.sell_signals.map((signal, idx) => (
                    <div key={idx} style={{ 
                      padding: '5px 10px', 
                      margin: '5px 0', 
                      backgroundColor: '#f8d7da', 
                      borderRadius: '4px',
                      fontSize: '14px'
                    }}>
                      {signal}
                    </div>
                  ))
                ) : (
                  <div style={{ color: '#666', fontStyle: 'italic' }}>No sell signals</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chart Tab */}
      {activeTab === 'chart' && chartData && !loading && (
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: 'white' }}>
          <h3>Chart Data for {symbol} ({timeframe}, {period})</h3>
          <div style={{ marginBottom: '20px' }}>
            <div><strong>Data Points:</strong> {chartData.ohlcv?.length || 0}</div>
            <div><strong>Buy Signals:</strong> {chartData.signals?.buy?.length || 0}</div>
            <div><strong>Sell Signals:</strong> {chartData.signals?.sell?.length || 0}</div>
          </div>
          
          {/* Simple price chart visualization */}
          <div style={{ height: '300px', border: '1px solid #eee', borderRadius: '4px', padding: '10px', backgroundColor: '#f9f9f9' }}>
            <div style={{ textAlign: 'center', paddingTop: '130px', color: '#666' }}>
              📈 Chart visualization would be implemented here using a charting library like Chart.js or D3.js
              <br />
              <small>Data includes OHLCV, indicators (SMA, Bollinger Bands, RSI, MACD, VWAP), and buy/sell signals</small>
            </div>
          </div>
        </div>
      )}

      {/* Backtest Tab */}
      {activeTab === 'backtest' && backtestData && !loading && (
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: 'white' }}>
          <h3>Backtest Results for {symbol}</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
            <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div style={{ fontSize: '12px', color: '#666' }}>Initial Capital</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{formatCurrency(backtestData.initial_capital)}</div>
            </div>
            <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div style={{ fontSize: '12px', color: '#666' }}>Final Value</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{formatCurrency(backtestData.final_value)}</div>
            </div>
            <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Return</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{formatPercent(backtestData.total_return)}</div>
            </div>
            <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Trades</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{backtestData.total_trades}</div>
            </div>
          </div>

          {backtestData.trades && backtestData.trades.length > 0 && (
            <div>
              <h4>Recent Trades</h4>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#e9ecef' }}>
                      <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Date</th>
                      <th style={{ padding: '8px', textAlign: 'left', border: '1px solid #ddd' }}>Action</th>
                      <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Price</th>
                      <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Shares</th>
                      <th style={{ padding: '8px', textAlign: 'right', border: '1px solid #ddd' }}>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {backtestData.trades.slice(-10).map((trade, idx) => (
                      <tr key={idx}>
                        <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                          {new Date(trade.date).toLocaleDateString()}
                        </td>
                        <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                          <span style={{
                            padding: '2px 6px',
                            borderRadius: '10px',
                            fontSize: '12px',
                            backgroundColor: trade.action === 'BUY' ? '#d4edda' : '#f8d7da',
                            color: trade.action === 'BUY' ? '#155724' : '#721c24'
                          }}>
                            {trade.action}
                          </span>
                        </td>
                        <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>
                          {formatCurrency(trade.price)}
                        </td>
                        <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>
                          {trade.shares}
                        </td>
                        <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'right' }}>
                          {formatCurrency(trade.cost || trade.proceeds)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Options Tab */}
      {activeTab === 'options' && optionsData && !loading && (
        <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', backgroundColor: 'white' }}>
          <h3>Options Analysis for {symbol}</h3>
          
          {optionsData.analysis && (
            <div style={{ marginBottom: '20px' }}>
              <h4>Options Metrics</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
                <div>
                  <strong>Put/Call Ratio:</strong> {optionsData.analysis.put_call_ratio?.toFixed(2) || 'N/A'}
                </div>
                <div>
                  <strong>Max Pain:</strong> {formatCurrency(optionsData.analysis.max_pain || 0)}
                </div>
                <div>
                  <strong>Implied Volatility:</strong> {(optionsData.analysis.implied_volatility_avg * 100)?.toFixed(1) || 'N/A'}%
                </div>
                <div>
                  <strong>Options Sentiment:</strong> 
                  <span style={{ 
                    marginLeft: '5px',
                    padding: '2px 6px',
                    borderRadius: '10px',
                    fontSize: '12px',
                    backgroundColor: 
                      optionsData.analysis.options_sentiment === 'BULLISH' ? '#d4edda' :
                      optionsData.analysis.options_sentiment === 'BEARISH' ? '#f8d7da' : '#fff3cd',
                    color:
                      optionsData.analysis.options_sentiment === 'BULLISH' ? '#155724' :
                      optionsData.analysis.options_sentiment === 'BEARISH' ? '#721c24' : '#856404'
                  }}>
                    {optionsData.analysis.options_sentiment}
                  </span>
                </div>
              </div>
            </div>
          )}

          {optionsData.strategies && (
            <div>
              <h4>Suggested Options Strategies</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '15px' }}>
                {optionsData.strategies.map((strategy, idx) => (
                  <div key={idx} style={{ 
                    padding: '15px', 
                    border: '1px solid #ddd', 
                    borderRadius: '8px',
                    backgroundColor: '#f8f9fa'
                  }}>
                    <h5 style={{ margin: '0 0 10px 0', color: '#007bff' }}>{strategy.name}</h5>
                    <div style={{ fontSize: '14px', marginBottom: '10px' }}>{strategy.description}</div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      <div><strong>Max Profit:</strong> {strategy.max_profit}</div>
                      <div><strong>Max Loss:</strong> {strategy.max_loss}</div>
                      <div><strong>Breakeven:</strong> {strategy.breakeven}</div>
                      <div><strong>Complexity:</strong> {strategy.complexity}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TechnicalAnalysisPanel;
