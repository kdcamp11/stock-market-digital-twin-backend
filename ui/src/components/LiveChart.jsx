import React, { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

// Custom Candlestick Bar Component
const CandlestickBar = (props) => {
  const { payload, x, y, width, height } = props;
  if (!payload) return null;
  
  const { open, high, low, close } = payload;
  const isGreen = close >= open;
  const color = isGreen ? '#22c55e' : '#ef4444';
  const bodyHeight = Math.abs(close - open);
  const bodyY = Math.min(close, open);
  
  // Scale values to chart coordinates
  const scale = height / (high - low);
  const wickX = x + width / 2;
  const bodyWidth = Math.max(width * 0.6, 2);
  const bodyX = x + (width - bodyWidth) / 2;
  
  return (
    <g>
      {/* High-Low Wick */}
      <line
        x1={wickX}
        y1={y}
        x2={wickX}
        y2={y + height}
        stroke={color}
        strokeWidth={1}
      />
      {/* Open-Close Body */}
      <rect
        x={bodyX}
        y={y + (high - Math.max(open, close)) * scale}
        width={bodyWidth}
        height={Math.max(bodyHeight * scale, 1)}
        fill={isGreen ? color : 'white'}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  );
};

// Indicator colors for dynamic rendering
const indicatorColors = {
  'EMA_9': '#ff6b35',
  'EMA_20': '#f7931e', 
  'EMA_50': '#ffcd3c',
  'VWAP': '#6a4c93',
  'BB_upper': '#00b4d8',
  'BB_lower': '#0077b6',
  'MACD': '#e63946',
  'RSI': '#2a9d8f'
};

// Helper function to get indicator color
const getIndicatorColor = (indicator) => {
  return indicatorColors[indicator] || '#ffffff';
};

const LiveChart = ({ data, selectedIndicators, symbol, technicalData }) => {
  console.log('LiveChart - Props received:', {
    symbol,
    dataLength: data?.length || 0,
    selectedIndicators,
    hasData: !!(data && data.length > 0),
    hasTechnicalData: !!technicalData
  });
  
  console.log('LiveChart - Selected indicators for chart rendering:', selectedIndicators);
  
  // Process chart data with proper formatting for interactivity
  const chartData = React.useMemo(() => {
    console.log('LiveChart - Processing data:', data?.slice(0, 2));
    if (!data || data.length === 0) return [];
    
    const { calculateAllIndicators } = require('../utils/technicalIndicators');
    const { indicators } = calculateAllIndicators(data);
    

    
    return data.map((item, index) => {
      const date = item.timestamp ? new Date(item.timestamp) : new Date();
      const close = parseFloat(item.close) || 0;
      const high = parseFloat(item.high) || close;
      const low = parseFloat(item.low) || close;
      const volume = parseInt(item.volume) || 0;
      
      return {
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        time: date.toLocaleTimeString(),
        fullDateTime: date.toLocaleString('en-US', {
          month: 'short',
          day: 'numeric', 
          hour: '2-digit',
          minute: '2-digit'
        }),
        open: parseFloat(item.open) || close,
        high: high,
        low: low,
        close: close,
        volume: volume,
        index: index,
        // Add indicators
        EMA_9: indicators.ema9?.[index],
        EMA_20: indicators.ema20?.[index], 
        EMA_50: indicators.ema50?.[index],
        RSI: indicators.rsi?.[index],
        MACD: indicators.macd?.macd?.[index],
        MACD_Signal: indicators.macd?.signal?.[index],
        VWAP: indicators.vwap?.[index],
        BB_upper: indicators.bb?.upper?.[index],
        BB_lower: indicators.bb?.lower?.[index],
        SMA_20: indicators.sma20?.[index]
      };
    }).filter(point => point && point.close > 0 && !isNaN(point.close));
  }, [data, selectedIndicators]);
  
  if (!data || data.length === 0) {
    return (
      <div style={{ 
        height: '400px', 
        width: '100%',
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: '8px',
        padding: '20px',
        paddingBottom: '60px'
      }}>
        <div style={{ textAlign: 'center', color: '#6c757d' }}>
          <div style={{ fontSize: '48px', marginBottom: '10px' }}>📈</div>
          <div style={{ fontSize: '18px', fontWeight: 'bold' }}>Live Chart for {symbol}</div>
          <div style={{ fontSize: '14px', marginTop: '5px' }}>
            {data ? 'No chart data available' : 'Loading chart data...'}
          </div>
        </div>
      </div>
    );
  }

  // Debug logging
  console.log('LiveChart - Raw data sample:', (data || []).slice(0, 2));
  console.log('LiveChart - Formatted data sample:', chartData.slice(0, 2));
  console.log('LiveChart - Total data points:', chartData.length);
  console.log('LiveChart - Chart will render:', chartData.length > 0);

  // Use the processed chartData for rendering

  return (
    <div className="live-chart-container" style={{ width: '100%', height: '400px' }}>
      {/* Title and Indicator Toggles - Side by Side */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: '200px', flexWrap: 'nowrap', overflowX: 'auto', width: '100%' }}>
        {/* Left side - Chart Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h3 style={{ margin: 0, color: 'var(--text-primary)', whiteSpace: 'nowrap', display: 'inline-block' }}>Live Chart for {symbol}</h3>
        </div>
        
        {/* Right side - Indicator Toggles */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-primary)' }}>Indicators:</span>
            <div style={{ display: 'flex', flexWrap: 'nowrap', gap: '8px', alignItems: 'center' }}>
              {['EMA_9', 'EMA_20', 'EMA_50', 'VWAP', 'BB_upper', 'BB_lower', 'MACD', 'RSI'].map(indicator => (
            <label key={indicator} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--text-secondary)' }}>
              <input
                type="checkbox"
                checked={selectedIndicators.includes(indicator)}
                onChange={(e) => {
                  if (e.target.checked) {
                    // Add indicator to selectedIndicators
                    const newIndicators = [...selectedIndicators, indicator];
                    // Call parent component's handler if available
                    if (window.updateSelectedIndicators) {
                      window.updateSelectedIndicators(newIndicators);
                    }
                  } else {
                    // Remove indicator from selectedIndicators
                    const newIndicators = selectedIndicators.filter(i => i !== indicator);
                    // Call parent component's handler if available
                    if (window.updateSelectedIndicators) {
                      window.updateSelectedIndicators(newIndicators);
                    }
                  }
                }}
              />
              <span style={{ color: getIndicatorColor(indicator) }}>{indicator}</span>
            </label>
              ))}
            </div>
          </div>
        </div>
      </div>
      {chartData.length === 0 ? (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <p style={{ color: '#f44336', fontSize: '14px' }}>No chart data available</p>
        </div>
      ) : (
        <>
          <div style={{ width: '100%', height: '380px', padding: '15px', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px', overflow: 'visible' }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={chartData}
                margin={{ top: 10, right: 10, left: 10, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="date" 
                  stroke="#666"
                  fontSize={9}
                  angle={0}
                  textAnchor="middle"
                  height={30}
                  interval={Math.floor(chartData.length / 8)}
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                  }}
                />
                <YAxis 
                  yAxisId="price"
                  orientation="left"
                  stroke="#666"
                  fontSize={11}
                  domain={['dataMin - 1', 'dataMax + 1']}
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                  width={60}
                />
                <YAxis 
                  yAxisId="volume"
                  orientation="right"
                  stroke="#999"
                  fontSize={9}
                  domain={[0, 'dataMax']}
                  hide={true}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '12px'
                  }}
                  labelStyle={{ color: '#333', fontWeight: 'bold' }}
                  labelFormatter={(label) => {
                    if (label) {
                      const date = new Date(label);
                      return date.toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: true
                      });
                    }
                    return label;
                  }}
                  formatter={(value, name) => {
                    if (name === 'volume') {
                      return [Number(value).toLocaleString(), 'Volume'];
                    }
                    if (typeof value === 'number') {
                      return [`$${value.toFixed(2)}`, name];
                    }
                    return [value, name];
                  }}
                />

                
                {/* Volume bars */}
                <Bar 
                  yAxisId="volume"
                  dataKey="volume" 
                  fill="#e0e0e0" 
                  opacity={0.3}
                  name="Volume"
                />
                
                {/* Candlestick bars for OHLC data */}
                <Bar 
                  yAxisId="price"
                  dataKey="close"
                  fill="#2196F3"
                  name="Price"
                  shape={(props) => {
                    const { payload, x, y, width, height } = props;
                    if (!payload || !payload.open || !payload.high || !payload.low || !payload.close) {
                      return <rect x={x} y={y} width={width} height={height} fill="#2196F3" />;
                    }
                    
                    const { open, high, low, close } = payload;
                    const isGreen = close >= open;
                    const color = isGreen ? '#22c55e' : '#ef4444';
                    const centerX = x + width / 2;
                    const bodyWidth = Math.max(width * 0.7, 2);
                    const bodyX = x + (width - bodyWidth) / 2;
                    
                    // Calculate positions (simplified for bar chart)
                    const bodyHeight = Math.abs(y - (y + height * (open - close) / (high - low)));
                    const bodyY = Math.min(y, y + height * (open - close) / (high - low));
                    
                    return (
                      <g>
                        {/* Wick line */}
                        <line
                          x1={centerX}
                          y1={y}
                          x2={centerX}
                          y2={y + height}
                          stroke={color}
                          strokeWidth={1}
                        />
                        {/* Body rectangle */}
                        <rect
                          x={bodyX}
                          y={bodyY}
                          width={bodyWidth}
                          height={Math.max(bodyHeight, 1)}
                          fill={isGreen ? color : 'white'}
                          stroke={color}
                          strokeWidth={1}
                        />
                      </g>
                    );
                  }}
                />
          
          {/* Dynamic indicator lines - only render selected indicators */}
          {selectedIndicators && selectedIndicators.length > 0 && selectedIndicators.map(indicator => {
            // Only render if the indicator data exists in the chart data
            const hasData = chartData.some(d => d[indicator] !== undefined && d[indicator] !== null && !isNaN(d[indicator]));
            if (!hasData || !selectedIndicators.includes(indicator)) {
              return null;
            }
            return (
              <Line
                key={`${indicator}-${selectedIndicators.join('-')}`}
                yAxisId="price"
                type="monotone"
                dataKey={indicator}
                stroke={indicatorColors[indicator] || '#666666'}
                strokeWidth={2}
                dot={false}
                name={indicator.replace('_', ' ')}
                connectNulls={false}
                animationDuration={300}
              />
            );
          })}
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

    </div>
  );
};

export default LiveChart;
