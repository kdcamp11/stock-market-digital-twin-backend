import React, { useState, useEffect } from 'react';
import { buildApiUrl } from '../api';

const SymbolSearch = ({ onSymbolsChange, initialSymbols = [] }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSymbols, setSelectedSymbols] = useState(initialSymbols);
  const [availableSymbols, setAvailableSymbols] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load available symbols from database
  useEffect(() => {
    const loadSymbols = async () => {
      try {
        const response = await fetch(buildApiUrl('/api/twin/latest'));
        const data = await response.json();
        const symbols = data.map(item => item.symbol).sort();
        setAvailableSymbols(symbols);
      } catch (error) {
        console.error('Failed to load symbols:', error);
      }
    };
    loadSymbols();
  }, []);

  // Filter symbols based on search term
  const filteredSymbols = availableSymbols.filter(symbol =>
    symbol.toLowerCase().includes(searchTerm.toLowerCase()) &&
    !selectedSymbols.includes(symbol)
  );

  const addSymbol = async (symbol) => {
    const upperSymbol = symbol.toUpperCase();
    
    // If symbol is not in database, try to add it
    if (!availableSymbols.includes(upperSymbol)) {
      setIsLoading(true);
      try {
        const response = await fetch(`${apiUrl}/api/add_ticker`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol: upperSymbol })
        });
        const result = await response.json();
        
        if (result.status === 'success' || result.status === 'exists') {
          setAvailableSymbols(prev => [...prev, upperSymbol].sort());
        } else {
          alert(`Failed to add ${upperSymbol}: ${result.message}`);
          setIsLoading(false);
          return;
        }
      } catch (error) {
        alert(`Error adding ${upperSymbol}: ${error.message}`);
        setIsLoading(false);
        return;
      }
      setIsLoading(false);
    }

    const newSymbols = [...selectedSymbols, upperSymbol];
    setSelectedSymbols(newSymbols);
    onSymbolsChange(newSymbols);
    setSearchTerm('');
  };

  const removeSymbol = (symbol) => {
    const newSymbols = selectedSymbols.filter(s => s !== symbol);
    setSelectedSymbols(newSymbols);
    onSymbolsChange(newSymbols);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && searchTerm.trim()) {
      addSymbol(searchTerm.trim());
    }
  };

  return (
    <div className="symbol-search">
      <div className="search-input-container">
        <input
          type="text"
          placeholder="Search or add ticker symbol (e.g., AAPL, TSLA)..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px'
          }}
        />
        {isLoading && <div style={{ marginTop: '4px', fontSize: '12px', color: '#666' }}>Adding symbol...</div>}
      </div>

      {/* Dropdown for filtered symbols */}
      {searchTerm && filteredSymbols.length > 0 && (
        <div style={{
          position: 'absolute',
          zIndex: 1000,
          backgroundColor: 'white',
          border: '1px solid #ddd',
          borderRadius: '4px',
          maxHeight: '200px',
          overflowY: 'auto',
          width: '100%',
          marginTop: '2px'
        }}>
          {filteredSymbols.slice(0, 10).map(symbol => (
            <div
              key={symbol}
              onClick={() => addSymbol(symbol)}
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                borderBottom: '1px solid #eee'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f5f5f5'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
            >
              {symbol}
            </div>
          ))}
        </div>
      )}

      {/* Selected symbols */}
      <div style={{ marginTop: '12px' }}>
        {selectedSymbols.map(symbol => (
          <span
            key={symbol}
            style={{
              display: 'inline-block',
              backgroundColor: '#007bff',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '12px',
              fontSize: '12px',
              marginRight: '6px',
              marginBottom: '6px',
              cursor: 'pointer'
            }}
            onClick={() => removeSymbol(symbol)}
            title="Click to remove"
          >
            {symbol} ×
          </span>
        ))}
      </div>
    </div>
  );
};

export default SymbolSearch;
