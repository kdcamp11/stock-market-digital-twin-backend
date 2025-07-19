import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { buildApiUrl } from '../api';
import useLivePrices from '../hooks/useLivePrices';
import SymbolSearch from './SymbolSearch';

const DashboardPanel = () => {
  const [twinStates, setTwinStates] = useState([]);
  const [selectedSymbols, setSelectedSymbols] = useState([]);
  const { prices, connectionStatus, errors, reconnect } = useLivePrices(selectedSymbols);

  useEffect(() => {
    const fetchTwinStates = async () => {
      try {
        const response = await axios.get(buildApiUrl('/api/twin/latest'));
        setTwinStates(response.data);
        // Auto-select first few symbols for live streaming
        const symbols = response.data.slice(0, 3).map(state => state.symbol);
        setSelectedSymbols(symbols);
      } catch (err) {
        console.error('Error fetching twin states:', err);
      }
    };
    
    fetchTwinStates();
    // Refresh twin states every 30 seconds
    const interval = setInterval(fetchTwinStates, 30000);
    return () => clearInterval(interval);
  }, []);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return '#28a745';
      case 'connecting': return '#ffc107';
      case 'error': return '#dc3545';
      case 'disconnected': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const formatPrice = (price) => {
    if (price === null || price === undefined) return '—';
    return typeof price === 'number' ? price.toFixed(2) : price;
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <h2>Live Dashboard</h2>
        
        {/* Connection Status */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          marginBottom: '15px',
          padding: '8px 12px',
          backgroundColor: '#f8f9fa',
          borderRadius: '4px',
          fontSize: '14px'
        }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: getConnectionStatusColor(),
            marginRight: '8px'
          }}></div>
          <span>Real-time data: {connectionStatus}</span>
          {connectionStatus === 'error' && (
            <button 
              onClick={reconnect}
              style={{
                marginLeft: '10px',
                padding: '4px 8px',
                fontSize: '12px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              Reconnect
            </button>
          )}
        </div>

        {/* Symbol Search */}
        <div style={{ marginBottom: '20px', position: 'relative' }}>
          <h3>Select Symbols for Live Streaming</h3>
          <SymbolSearch 
            onSymbolsChange={setSelectedSymbols}
            initialSymbols={selectedSymbols}
          />
        </div>
      </div>

      <h2>Latest Twin States</h2>
      {twinStates.map(state => {
        const livePrice = prices[state.symbol];
        const hasError = errors[state.symbol];
        const isSelected = selectedSymbols.includes(state.symbol);
        
        return (
          <div key={state.symbol} style={{ 
            marginBottom: '20px', 
            padding: '15px', 
            border: isSelected ? '2px solid #007bff' : '1px solid #ccc',
            borderRadius: '8px',
            backgroundColor: isSelected ? '#f8f9ff' : 'white'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h3 style={{ margin: 0 }}>{state.symbol}</h3>
              {isSelected && (
                <span style={{
                  fontSize: '12px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  padding: '2px 6px',
                  borderRadius: '10px'
                }}>
                  LIVE
                </span>
              )}
            </div>
            
            {/* Price Information */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '10px' }}>
              <div>
                <strong>Historical Price:</strong> ${formatPrice(state.close)}
                <div style={{ fontSize: '12px', color: '#666' }}>Updated: {state.timestamp}</div>
              </div>
              
              {isSelected && (
                <div>
                  <strong>Live Price:</strong> 
                  {hasError ? (
                    <span style={{ color: '#dc3545', fontSize: '12px' }}> Error: {hasError}</span>
                  ) : livePrice ? (
                    <span>
                      <span style={{ color: '#28a745', fontWeight: 'bold' }}> ${formatPrice(livePrice.price)}</span>
                      <div style={{ fontSize: '12px', color: '#666' }}>Updated: {formatTimestamp(livePrice.timestamp)}</div>
                    </span>
                  ) : (
                    <span style={{ color: '#6c757d' }}> Loading...</span>
                  )}
                </div>
              )}
            </div>

            {/* Signals */}
            {state.signals && state.signals.length > 0 && (
              <div style={{ marginBottom: '10px' }}>
                <strong>Signals:</strong>
                <div style={{ marginTop: '5px' }}>
                  {state.signals.map((signal, idx) => (
                    <span key={idx} style={{ 
                      backgroundColor: signal === 'TTM Squeeze' ? 'orange' : signal === 'RSI Oversold' ? 'red' : 'gray',
                      color: 'white',
                      padding: '4px 8px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      marginRight: '6px',
                      display: 'inline-block'
                    }}>
                      {signal}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default DashboardPanel;
