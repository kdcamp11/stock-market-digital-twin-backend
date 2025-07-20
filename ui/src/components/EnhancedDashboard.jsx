import React, { useState, useEffect } from 'react';
import LiveChart from './LiveChart';
import TradeRecommendationCard from './TradeRecommendationCard';
import AgentChatPanel from './AgentChatPanel';
import { calculateAllIndicators, calculateSignalStrength } from '../utils/technicalIndicators';
import { buildApiUrl } from '../api';

// Helper function for indicator colors
const getIndicatorColor = (indicator) => {
  const colors = {
    'EMA_9': '#ff6b35',
    'EMA_20': '#f7931e', 
    'EMA_50': '#ffcd3c',
    'VWAP': '#6a4c93',
    'BB_upper': '#00b4d8',
    'BB_lower': '#0077b6',
    'MACD': '#e63946',
    'RSI': '#2a9d8f'
  };
  return colors[indicator] || '#666';
};

const EnhancedDashboard = () => {
  // Enhanced state for advanced features
  const [selectedSymbol, setSelectedSymbol] = useState('MARA');
  const [realTimePrice, setRealTimePrice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeSignals, setActiveSignals] = useState([]);
  const [signalStrength, setSignalStrength] = useState(null);
  const [tradeRecommendation, setTradeRecommendation] = useState(null);
  const [timeframe, setTimeframe] = useState('30m');
  const [period, setPeriod] = useState('1M');
  const [selectedIndicators, setSelectedIndicators] = useState(['EMA_9', 'EMA_20', 'EMA_50', 'VWAP', 'BB_upper']);
  const [technicalData, setTechnicalData] = useState(null);
  const [hypotheticalTrades, setHypotheticalTrades] = useState([
    {
      id: 1,
      type: 'BUY',
      symbol: 'MARA',
      price: 19.51,
      target: 21.50,
      stop: 18.75,
      reason: 'RSI Oversold + MACD Bullish Cross',
      timestamp: new Date().toISOString(),
      status: 'active'
    },
    {
      id: 2,
      type: 'SELL',
      symbol: 'MARA', 
      price: 20.85,
      entry: 19.51,
      pnl: 1.34,
      pnlPercent: 6.9,
      reason: 'RSI Overbought + Resistance Level',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      status: 'closed'
    }
  ]);
  const [showOptions, setShowOptions] = useState(true);
  const [chartData, setChartData] = useState([]);
  const [showChart, setShowChart] = useState(true);

  // Generate mock chart data when API is not available
  const generateMockChartData = (symbol, currentPrice) => {
    const data = [];
    const basePrice = currentPrice || 100;
    const now = new Date();
    
    for (let i = 59; i >= 0; i--) { // Increase to 60 days for proper indicator calculation
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      const variation = (Math.random() - 0.5) * 0.1;
      const price = basePrice * (1 + variation * (i / 30));
      
      data.push({
        timestamp: date.toISOString(),
        open: price * (1 + (Math.random() - 0.5) * 0.02),
        high: price * (1 + Math.random() * 0.03),
        low: price * (1 - Math.random() * 0.03),
        close: price,
        volume: Math.floor(Math.random() * 1000000) + 100000
      });
    }
    
    return data;
  };

  // Function to log hypothetical trades based on options analysis
  const logHypotheticalTrade = async (tradeType) => {
    try {
      // Get current price and options analysis for trade details
      const currentPrice = realTimePrice || 19.51; // Fallback price
      const signals = activeSignals.length > 0 ? activeSignals : [{ type: 'Technical Analysis', description: 'Manual trade entry' }];
      
      let tradeData;
      if (tradeType === 'BUY') {
        tradeData = {
          id: Date.now(),
          type: 'BUY',
          symbol: selectedSymbol,
          price: currentPrice,
          target: currentPrice * 1.10, // 10% target
          stop: currentPrice * 0.96,   // 4% stop loss
          reason: signals[0]?.description || 'Manual BUY entry',
          timestamp: new Date().toISOString(),
          status: 'active'
        };
      } else {
        // For SELL, find the most recent BUY trade to calculate P&L
        const lastBuyTrade = hypotheticalTrades
          .filter(t => t.symbol === selectedSymbol && t.type === 'BUY' && t.status === 'active')
          .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];
        
        const entryPrice = lastBuyTrade?.price || currentPrice * 0.95;
        const pnl = currentPrice - entryPrice;
        const pnlPercent = ((pnl / entryPrice) * 100);
        
        tradeData = {
          id: Date.now(),
          type: 'SELL',
          symbol: selectedSymbol,
          price: currentPrice,
          entry: entryPrice,
          pnl: parseFloat(pnl.toFixed(2)),
          pnlPercent: parseFloat(pnlPercent.toFixed(1)),
          reason: signals[0]?.description || 'Manual SELL entry',
          timestamp: new Date().toISOString(),
          status: 'closed'
        };
        
        // Mark the corresponding BUY trade as closed
        if (lastBuyTrade) {
          setHypotheticalTrades(prev => 
            prev.map(trade => 
              trade.id === lastBuyTrade.id 
                ? { ...trade, status: 'closed' }
                : trade
            )
          );
        }
      }
      
      // Add the new trade to the list
      setHypotheticalTrades(prev => [tradeData, ...prev]);
      
      console.log(`Logged ${tradeType} trade:`, tradeData);
      
    } catch (error) {
      console.error('Error logging hypothetical trade:', error);
    }
  };

  // Load real-time price data and chart data
  useEffect(() => {
    console.log('Live Dashboard: useEffect triggered for symbol:', selectedSymbol);
    const loadData = async () => {
      try {
        // Fetch current price
        try {
          const priceResponse = await fetch(buildApiUrl(`/api/current-price/${selectedSymbol}`));
          if (priceResponse.ok) {
            const priceData = await priceResponse.json();
            if (priceData.status === 'success') {
              setRealTimePrice(priceData.price);
              console.log('Live Dashboard: Current price fetched:', priceData.price);
            }
          } else {
            console.log('Live Dashboard: Price API not available, will use chart data');
          }
        } catch (priceError) {
          console.log('Live Dashboard: Price fetch failed:', priceError.message);
        }
        
        // Fetch chart data
        try {
          const chartResponse = await fetch(buildApiUrl(`/api/chart/${selectedSymbol}?timeframe=${timeframe}&period=${period}`));
          console.log('Live Dashboard: Chart response status:', chartResponse.status);
          
          if (chartResponse.ok) {
            const chartDataResponse = await chartResponse.json();
            console.log('Live Dashboard: Chart data received:', chartDataResponse);
            
            // Handle both direct array and wrapped response formats
            const actualChartData = chartDataResponse.data || chartDataResponse;
            console.log('Live Dashboard: Setting chart data:', actualChartData.length, 'items');
            setChartData(actualChartData);
          } else {
            throw new Error(`Chart API returned ${chartResponse.status}`);
          }
        } catch (chartError) {
          console.log('Live Dashboard: Chart API failed:', chartError.message);
          setChartData([]);
          console.log('Live Dashboard: No chart data available - backend connection required');
        }
        
        // Fetch comprehensive signals data from unified endpoint
        try {
          const signalsResponse = await fetch(buildApiUrl(`/api/signals/${selectedSymbol}`));
          if (signalsResponse.ok) {
            const signalsData = await signalsResponse.json();
            console.log('Live Dashboard: Unified signals data fetched:', signalsData);
            
            if (signalsData.status === 'success' && signalsData.data) {
              const analysis = signalsData.data;
              
              // Format signals for display
              const formattedSignals = analysis.signals.all_signals.map(signal => ({
                type: signal,
                description: signal,
                strength: analysis.signals.confidence >= 4 ? 'high' : 
                         analysis.signals.confidence >= 2 ? 'medium' : 'low'
              }));
              
              // Set technical data with unified backend signals
              setTechnicalData({
                indicators: analysis.indicators || {},
                signals: formattedSignals,
                confidence: analysis.signals.confidence,
                trend: analysis.signals.trend,
                recommendation: analysis.signals.recommendation,
                total_signals: analysis.signals.total_signals,
                bullish_signals: analysis.signals.bullish_signals,
                bearish_signals: analysis.signals.bearish_signals,
                timestamp: analysis.timestamp,
                symbol: selectedSymbol
              });
              setActiveSignals(formattedSignals);
              
              // Set signal strength based on backend analysis
              setSignalStrength({
                overall: analysis.signals.trend,
                confidence: analysis.signals.confidence,
                strength: analysis.signals.strength
              });
              
              console.log('Live Dashboard: Processed unified signals:', {
                signals: formattedSignals,
                confidence: analysis.signals.confidence,
                trend: analysis.signals.trend
              });
            }
          } else {
            console.log('Live Dashboard: Unified signals API not available, using fallback');
            console.error('Signals API Response:', signalsResponse.status, signalsResponse.statusText);
            
            // Fallback: Calculate signals from chart data if available
            if (chartData && chartData.length > 0) {
              const indicators = calculateAllIndicators(chartData);
              const latestIndex = chartData.length - 1;
              
              // Generate signals based on latest indicators
              const signals = [];
              
              // RSI signals
              if (indicators.rsi && indicators.rsi[latestIndex]) {
                const rsi = indicators.rsi[latestIndex];
                if (rsi > 70) {
                  signals.push({ type: 'RSI Overbought', description: 'BEARISH HIGH', strength: 'high' });
                } else if (rsi < 30) {
                  signals.push({ type: 'RSI Oversold', description: 'BULLISH HIGH', strength: 'high' });
                } else if (rsi > 55) {
                  signals.push({ type: 'RSI Bullish', description: 'BULLISH MEDIUM', strength: 'medium' });
                } else if (rsi < 45) {
                  signals.push({ type: 'RSI Bearish', description: 'BEARISH MEDIUM', strength: 'medium' });
                }
              }
              
              // Store key indicators for display
              const keyIndicators = {
                RSI: indicators.rsi?.[latestIndex],
                MACD: indicators.macd?.MACD?.[latestIndex],
                EMA_9: indicators.ema9?.[latestIndex],
                EMA_20: indicators.ema20?.[latestIndex],
                EMA_50: indicators.ema50?.[latestIndex],
                VWAP: indicators.vwap?.[latestIndex]
              };
              
              setTechnicalData({
                indicators: keyIndicators,
                signals: signals,
                confidence: signals.length,
                timestamp: new Date().toISOString(),
                symbol: selectedSymbol
              });
              setActiveSignals(signals);
              
              // Calculate signal strength using the signals
              const strength = calculateSignalStrength(signals);
              setSignalStrength(strength);
              
              console.log('Live Dashboard: Generated fallback signals from chart data:', signals);
            }
          }
        } catch (signalsError) {
          console.error('Live Dashboard: Error fetching signals data:', signalsError);
          console.error('Live Dashboard: Signals API failed - no fallback data will be shown');
        }

        // Load trade recommendation from backend API
        console.log('Live Dashboard: Fetching live options data for', selectedSymbol);
        try {
          const optionsResponse = await fetch(buildApiUrl(`/api/intelligent-options/${selectedSymbol}`));
          const optionsResult = await optionsResponse.json();
          
          if (optionsResult.status === 'success' && optionsResult.recommendation) {
            setTradeRecommendation(optionsResult.recommendation);
            console.log('Live Dashboard: Options data loaded:', optionsResult.recommendation);
          } else {
            console.log('Live Dashboard: Options API failed:', optionsResult.message || 'Unknown error');
            setTradeRecommendation(null);
          }
        } catch (optionsError) {
          console.error('Live Dashboard: Options API error:', optionsError);
          setTradeRecommendation(null);
        }
      } catch (error) {
        console.log('Data loading error:', error);
        // Set fallback data
        setActiveSignals([
          { type: 'Volume Spike', value: '+45%', status: 'neutral', description: `${selectedSymbol} volume 45% above average` }
        ]);
      }
    };

    loadData();
  }, [selectedSymbol, timeframe, period, selectedIndicators]);

  return (
    <div className="min-h-screen dashboard-container" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Header Section - Single Row Layout */}
      <div className="card mb-6">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '40px', flexWrap: 'nowrap', overflowX: 'auto' }}>
          {/* Left side - Symbol, Price, Date */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* Symbol Search */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label className="text-sm" style={{ color: 'var(--text-primary)' }}>Symbol:</label>
              <input
                type="text"
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value.toUpperCase())}
                placeholder="Enter symbol..."
                className="form-control text-sm"
                style={{ width: '120px', minWidth: '80px' }}
              />
            </div>
            
            {/* Quick Symbol Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Quick:</span>
              <select 
                value={selectedSymbol} 
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="form-control text-xs"
                style={{ width: 'auto', minWidth: '60px', fontSize: '12px' }}
              >
                <option value="MARA">MARA</option>
                <option value="AAPL">AAPL</option>
                <option value="TSLA">TSLA</option>
                <option value="MSFT">MSFT</option>
                <option value="GOOGL">GOOGL</option>
                <option value="AMZN">AMZN</option>
                <option value="NVDA">NVDA</option>
                <option value="META">META</option>
              </select>
            </div>
            
            {/* Price Display */}
            <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
              {realTimePrice ? `$${realTimePrice.price?.toFixed(2) || '0.00'}` : '$19.51'}
            </div>
            
            {/* Ticker */}
            <div className="text-lg font-medium" style={{ color: 'var(--text-primary)' }}>
              {selectedSymbol}
            </div>
            
            {/* Date */}
            <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              {new Date().toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </div>
          </div>
          
          {/* Right side - Timeframe, Period */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* Timeframe */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label className="text-sm" style={{ color: 'var(--text-primary)' }}>Timeframe:</label>
              <select 
                value={timeframe} 
                onChange={(e) => setTimeframe(e.target.value)}
                className="form-control text-sm"
                style={{ width: 'auto', minWidth: '70px' }}
              >
                <option value="1m">1m</option>
                <option value="5m">5m</option>
                <option value="15m">15m</option>
                <option value="30m">30m</option>
                <option value="1h">1h</option>
                <option value="4h">4h</option>
                <option value="1D">1D</option>
                <option value="1W">1W</option>
              </select>
            </div>
            
            {/* Period */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label className="text-sm" style={{ color: 'var(--text-primary)' }}>Period:</label>
              <select 
                value={period} 
                onChange={(e) => setPeriod(e.target.value)}
                className="form-control text-sm"
                style={{ width: 'auto', minWidth: '90px' }}
              >
                <option value="1D">1 Day</option>
                <option value="1W">1 Week</option>
                <option value="1M">1 Month</option>
                <option value="3M">3 Months</option>
                <option value="6M">6 Months</option>
                <option value="1Y">1 Year</option>
                <option value="2Y">2 Years</option>
                <option value="5Y">5 Years</option>
              </select>
            </div>
          </div>
        </div>
      </div>
      
      {/* Chart & Indicators Section */}
      <div className="chart-container">
        <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
          <div></div>
          
          <div className="flex gap-6 items-center flex-wrap">
            
            {/* Show Chart Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ fontSize: '14px', color: 'var(--text-primary)' }}>Show Chart:</label>
              <input
                type="checkbox"
                checked={showChart}
                onChange={(e) => setShowChart(e.target.checked)}
              />
            </div>
          </div>
        </div>
        

        
        {showChart ? (
          <div className="card" style={{ padding: '24px' }}>

            
            {/* Chart and Indicator Values - Side by Side */}
            <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
              {/* Chart Section */}
              <div style={{ flex: '1', minWidth: '0', overflow: 'hidden' }}>
                {chartData && chartData.length > 0 ? (
                  <>

                    <LiveChart 
                      key={`${selectedSymbol}-${timeframe}-${period}-${selectedIndicators.join('-')}`}
                      data={chartData} 
                      selectedIndicators={selectedIndicators}
                      symbol={selectedSymbol}
                      technicalData={technicalData}
                    />
                  </>
                ) : (
                  <div style={{
                    padding: '40px',
                    textAlign: 'center',
                    color: 'var(--text-secondary)',
                    backgroundColor: 'var(--bg-tertiary)',
                    borderRadius: '8px'
                  }}>
                    <div style={{ fontSize: '18px', marginBottom: '10px', color: 'var(--text-primary)' }}>Chart</div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px', color: 'var(--text-primary)' }}>No Chart Data</div>
                    <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Chart data: {chartData ? chartData.length : 'null'} items</div>
                    <div style={{ fontSize: '12px', marginTop: '8px', color: 'var(--text-secondary)' }}>Check browser console for debugging info</div>
                  </div>
                )}
              </div>
              
              {/* Live Indicator Values Card */}
              <div style={{ minWidth: '250px', maxWidth: '280px', flexShrink: 0 }}>
                <div className="card" style={{ margin: '0' }}>
                  <div className="text-lg text-medium mb-4" style={{ color: 'var(--text-primary)' }}>Live Indicator Values</div>
                  {technicalData?.indicators ? (
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {technicalData.indicators.RSI && (
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--text-secondary)' }}>RSI:</span>
                          <span className="text-bold" style={{ color: 'var(--text-primary)' }}>
                            {technicalData.indicators.RSI?.toFixed(2) || 'N/A'}
                          </span>
                        </div>
                      )}
                      {technicalData.indicators.MACD && (
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--text-secondary)' }}>MACD:</span>
                          <span className="text-bold" style={{ color: 'var(--text-primary)' }}>
                            {technicalData.indicators.MACD?.toFixed(4) || 'N/A'}
                          </span>
                        </div>
                      )}
                      {technicalData.indicators.EMA_9 && (
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--text-secondary)' }}>EMA 9:</span>
                          <span className="text-bold" style={{ color: 'var(--text-primary)' }}>
                            ${technicalData.indicators.EMA_9?.toFixed(2) || 'N/A'}
                          </span>
                        </div>
                      )}
                      {technicalData.indicators.EMA_20 && (
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--text-secondary)' }}>EMA 20:</span>
                          <span className="text-bold" style={{ color: 'var(--text-primary)' }}>
                            ${technicalData.indicators.EMA_20?.toFixed(2) || 'N/A'}
                          </span>
                        </div>
                      )}
                      {technicalData.indicators.VWAP && (
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--text-secondary)' }}>VWAP:</span>
                          <span className="text-bold" style={{ color: 'var(--text-primary)' }}>
                            ${technicalData.indicators.VWAP?.toFixed(2) || 'N/A'}
                          </span>
                        </div>
                      )}
                      {technicalData.indicators.EMA_50 && (
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--text-secondary)' }}>EMA 50:</span>
                          <span className="text-bold" style={{ color: 'var(--text-primary)' }}>
                            ${technicalData.indicators.EMA_50?.toFixed(2) || 'N/A'}
                          </span>
                        </div>
                      )}
                      {technicalData.indicators.BB_upper && (
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--text-secondary)' }}>BB Upper:</span>
                          <span className="text-bold" style={{ color: 'var(--text-primary)' }}>
                            ${technicalData.indicators.BB_upper?.toFixed(2) || 'N/A'}
                          </span>
                        </div>
                      )}
                      {technicalData.indicators.BB_lower && (
                        <div className="flex justify-between">
                          <span style={{ color: 'var(--text-secondary)' }}>BB Lower:</span>
                          <span className="text-bold" style={{ color: 'var(--text-primary)' }}>
                            ${technicalData.indicators.BB_lower?.toFixed(2) || 'N/A'}
                          </span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="col-span-full text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
                      Loading key indicators...
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div style={{
            padding: '40px',
            textAlign: 'center',
            color: 'var(--text-secondary)',
            backgroundColor: 'var(--bg-tertiary)',
            borderRadius: '8px'
          }}>
            <div style={{ fontSize: '18px', marginBottom: '10px', color: 'var(--text-primary)' }}>Chart</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: 'var(--text-primary)' }}>Chart Hidden</div>
            <div style={{ fontSize: '14px', marginTop: '8px', color: 'var(--text-secondary)' }}>Enable "Show Chart" to view live price data</div>
          </div>
        )}
      </div>

      {/* Trading Information Panels - Horizontal Layout */}
      <div style={{ display: 'flex', flexDirection: 'row', gap: '24px', width: '100%' }}>
        {/* Active Signals Panel */}
        <div className="signals-panel" style={{ flex: '1', minWidth: '0' }}>
          <div className="flex items-center mb-6">
            <div className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: 'var(--accent-secondary)' }}></div>
            <h3 className="text-xl text-bold" style={{ color: 'var(--text-primary)' }}>Active Signals</h3>
          </div>
          

          
          {/* Signal Strength Display */}
          {technicalData && (
            <div className={`mb-3 p-3 rounded border ${
              technicalData.trend === 'BULLISH' ? 'bg-green-900/10 border-green-700' :
              technicalData.trend === 'BEARISH' ? 'bg-red-900/10 border-red-700' :
              'bg-yellow-900/20 border-yellow-600'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span 
                  className="text-sm font-medium px-2 py-1 rounded"
                  style={{
                    backgroundColor: 
                      technicalData.trend === 'BULLISH' ? '#15803d' :
                      technicalData.trend === 'BEARISH' ? '#ef4444' :
                      '#ca8a04',
                    color: '#ffffff',
                    fontWeight: '600'
                  }}>
                  {technicalData.trend === 'BULLISH' ? 'MODERATE BUY' : technicalData.trend === 'BEARISH' ? 'MODERATE SELL' : 'WAIT'}
                </span>
                <div className="text-xs" style={{ color: 'var(--text-primary)' }}>
                  Confidence: {technicalData.confidence || 0}/5
                </div>
              </div>
              <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                {technicalData.total_signals || activeSignals.length} signals
                {technicalData.bullish_signals !== undefined && technicalData.bearish_signals !== undefined && 
                  ` (${technicalData.bullish_signals} bullish, ${technicalData.bearish_signals} bearish)`
                }
              </div>
              <div className="flex justify-between mt-2 text-xs" style={{ color: 'var(--text-secondary)' }}>
                <span>↗ {signalStrength.bullishCount}</span>
                <span>↘ {signalStrength.bearishCount}</span>
                <span>Score: {signalStrength.netScore}</span>
              </div>
            </div>
          )}
          
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {activeSignals.length > 0 ? (
              activeSignals.map((signal, index) => (
                <div key={index} className={`p-2 rounded border text-xs ${
                  signal.signal === 'BULLISH' ? 'bg-green-900/20 border-green-600' :
                  signal.signal === 'BEARISH' ? 'bg-red-900/20 border-red-600' :
                  signal.signal === 'CAUTION' ? 'bg-yellow-900/20 border-yellow-600' :
                  'bg-gray-700 border-gray-600'
                }`} style={{ color: 'var(--text-primary)' }}>
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="font-medium" style={{ color: 'var(--text-primary)' }}>{signal.type?.replace(/([A-Z])(?=[A-Z][a-z])|([a-z])(?=[A-Z])/g, '$1$2 ')}</div>
                      <div className="flex items-center space-x-1 mt-1">
                        <span style={{ color: 'var(--text-primary)' }}>{signal.signal?.replace(/([A-Z])(?=[A-Z][a-z])|([a-z])(?=[A-Z])/g, '$1$2 ')}</span>
                        {signal.confidence && (
                          <span className={`px-1 py-0.5 rounded text-xs ${
                            signal.confidence === 'HIGH' ? 'bg-green-600 text-white' :
                            signal.confidence === 'MEDIUM' ? 'bg-yellow-600 text-white' :
                            'bg-red-600 text-white'
                          }`}>
                            {signal.confidence}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>{signal.value}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                <h3 className="text-xl text-bold" style={{ color: 'var(--text-primary)' }}>Active Signals</h3>
                <div className="signal-summary" style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                  {technicalData ? (
                    <>
                      <div className="signal-strength" style={{ fontSize: '1.1rem', fontWeight: 'bold', color: technicalData.trend === 'BULLISH' ? '#10b981' : technicalData.trend === 'BEARISH' ? '#ef4444' : '#6b7280' }}>
                        {technicalData.trend === 'BULLISH' ? 'MODERATE BUY' : technicalData.trend === 'BEARISH' ? 'MODERATE SELL' : 'WAIT'}
                      </div>
                      <div style={{ fontSize: '0.9rem', marginTop: '0.25rem' }}>
                        {technicalData.total_signals || activeSignals.length} signals
                      </div>
                      <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
                        {technicalData.bullish_signals || 0} bullish, {technicalData.bearish_signals || 0} bearish - confidence {technicalData.confidence || 0}/5
                      </div>
                    </>
                  ) : (
                    <div>Loading signals...</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Options Analysis Panel */}
        <div className="options-panel" style={{ flex: '1', minWidth: '0' }}>
          <div className="flex items-center mb-6">
            <div className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: 'var(--accent-primary)' }}></div>
            <h3 className="text-xl text-bold" style={{ color: 'var(--text-primary)' }}>Options Analysis</h3>
          </div>
          {tradeRecommendation ? (
            <TradeRecommendationCard 
              symbol={selectedSymbol}
              recommendation={tradeRecommendation}
            />
          ) : (
            <div className="text-center py-8">
              <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Loading options analysis for {selectedSymbol}...
              </div>
            </div>
          )}
        </div>

        {/* Trade Log Panel */}
        <div className="trade-log" style={{ flex: '1', minWidth: '0' }}>
          <div className="flex items-center mb-6">
            <div className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: '#a855f7' }}></div>
            <h3 className="text-xl text-bold" style={{ color: 'var(--text-primary)' }}>Trade Log</h3>
          </div>
          <div className="rounded-lg p-4 max-h-80 overflow-y-auto" style={{ backgroundColor: 'var(--bg-tertiary)', border: '1px solid var(--border-primary)' }}>
            <div className="text-sm text-medium mb-4" style={{ color: 'var(--text-primary)' }}>
              Recent trades for {selectedSymbol}:
            </div>
            
            {/* Trade Buttons */}
            <div className="mb-6 flex gap-3">
              <button
                onClick={() => logHypotheticalTrade('BUY')}
                className="btn btn-success"
              >
                BUY
              </button>
              <button
                onClick={() => logHypotheticalTrade('SELL')}
                className="btn btn-danger"
              >
                SELL
              </button>
            </div>
            
            {/* Trade Entries */}
            <div className="space-y-2">
              {hypotheticalTrades.filter(trade => trade.symbol === selectedSymbol).map(trade => (
                <div key={trade.id} className={`p-2 rounded border text-xs ${
                  trade.type === 'BUY' 
                    ? 'bg-green-900/20 border-green-600' 
                    : 'bg-red-900/20 border-red-600'
                }`} style={{ color: 'var(--text-primary)' }}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-medium">{trade.type}</span>
                    <span className={`px-1 py-0.5 rounded text-xs ${
                      trade.status === 'active' 
                        ? 'bg-green-600 text-white' 
                        : 'bg-gray-600 text-white'
                    }`}>
                      {trade.status === 'active' ? 'Active' : 'Closed'}
                    </span>
                  </div>
                  <div className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>
                    {trade.type === 'BUY' ? (
                      `$${trade.price} → $${trade.target} (Stop: $${trade.stop})`
                    ) : (
                      `Exit: $${trade.price} | P&L: ${trade.pnl > 0 ? '+' : ''}$${trade.pnl}`
                    )}
                  </div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                    {new Date(trade.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
            
            {hypotheticalTrades.filter(trade => trade.symbol === selectedSymbol).length === 0 && (
              <div className="text-center py-4">
                <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  No trades for {selectedSymbol}
                </div>
                <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                  Click BUY/SELL to start
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Agent Chat Panel */}
      <div className="card">
        <div className="flex items-center mb-6">
          <div className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: 'var(--accent-primary)' }}></div>
          <h3 className="text-xl text-bold" style={{ color: 'var(--text-primary)' }}>Agent Chat</h3>
        </div>
        <AgentChatPanel />
      </div>
    </div>
  );
};

export default EnhancedDashboard;
