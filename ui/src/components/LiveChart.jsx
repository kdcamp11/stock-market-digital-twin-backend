import React from 'react';
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
      <h3>Live Chart for {symbol}</h3>
      {chartData.length === 0 ? (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <p style={{ color: '#f44336', fontSize: '14px' }}>No chart data available</p>
        </div>
      ) : (
        <>
          <div style={{ width: '100%', height: '400px', padding: '10px', backgroundColor: 'var(--bg-secondary)', borderRadius: '8px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                width={800}
                height={400}
                data={chartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="date" 
                  stroke="#666"
                  fontSize={10}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                  interval={Math.floor(chartData.length / 10)}
                />
                <YAxis 
                  yAxisId="price"
                  orientation="left"
                  stroke="#666"
                  fontSize={12}
                  domain={['dataMin - 5', 'dataMax + 5']}
                />
                <YAxis 
                  yAxisId="volume"
                  orientation="right"
                  stroke="#999"
                  fontSize={10}
                  domain={[0, 'dataMax']}
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
