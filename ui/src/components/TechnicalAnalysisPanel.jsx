import React, { useState, useEffect } from 'react';
import { buildApiUrl } from '../api';
import LiveChart from './LiveChart';

const TechnicalAnalysisPanel = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [loading, setLoading] = useState(false);
  const [technicalData, setTechnicalData] = useState(null);
  const [activeTab, setActiveTab] = useState('technical');

  const fetchTechnicalAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch(buildApiUrl(`/api/technical/${symbol}`));
      const data = await response.json();
      if (data.status === 'success') {
        // Backend returns { indicators, signals, timestamp, symbol }
        setTechnicalData({
          indicators: data.indicators,
          signals: data.signals,
          timestamp: data.timestamp,
          symbol: data.symbol
        });
      }
    } catch (error) {
      console.error('Error fetching technical analysis:', error);
    }
    setLoading(false);
  };





  useEffect(() => {
    if (activeTab === 'technical') {
      fetchTechnicalAnalysis();
    }
  }, [symbol, activeTab]);

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
        

      </div>

      {/* Tabs */}
      <div style={{ marginBottom: '20px' }}>

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
          
          <div style={{ marginBottom: '20px' }}>
            <div>
              <h4>Current Price & Status</h4>
              <div style={{ 
                padding: '15px', 
                backgroundColor: '#007bff', 
                color: 'white', 
                borderRadius: '8px',
                textAlign: 'center',
                maxWidth: '300px'
              }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{formatCurrency(technicalData.indicators?.Current_Price || 0)}</div>
                <div>Volume: {technicalData.indicators?.Volume?.toLocaleString() || 'N/A'}</div>
                <div>Updated: {new Date(technicalData.timestamp).toLocaleString()}</div>
              </div>
            </div>
          </div>

          <div>
            <h4>Active Signals ({technicalData.signals?.length || 0})</h4>
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              {technicalData.signals && technicalData.signals.length > 0 ? (
                technicalData.signals.map((signal, idx) => {
                  const isPositive = signal.includes('Bullish') || signal.includes('Golden') || signal.includes('Above');
                  return (
                    <div key={idx} style={{ 
                      padding: '8px 12px', 
                      margin: '5px 0', 
                      backgroundColor: isPositive ? '#d4edda' : '#f8d7da',
                      borderLeft: `4px solid ${isPositive ? '#28a745' : '#dc3545'}`,
                      borderRadius: '4px',
                      fontSize: '14px'
                    }}>
                      {signal}
                    </div>
                  );
                })
              ) : (
                <div style={{ color: '#666', fontStyle: 'italic' }}>No active signals</div>
              )}
            </div>
          </div>
        </div>
      )}


    </div>
  );
};

export default TechnicalAnalysisPanel;
