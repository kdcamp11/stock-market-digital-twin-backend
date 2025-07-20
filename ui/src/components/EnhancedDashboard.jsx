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
          console.log('Live Dashboard: Chart API failed, generating mock data:', chartError.message);
          
          // Generate mock chart data for demonstration
          const mockData = generateMockChartData(selectedSymbol, realTimePrice || 100);
          console.log('Live Dashboard: Using mock chart data:', mockData.length, 'items');
          setChartData(mockData);
        }
        
        // Try to fetch technical data from backend first (to match Technical Analysis panel)
        console.log('Live Dashboard: Fetching technical data from backend for', selectedSymbol);
        try {
          const technicalResponse = await fetch(buildApiUrl(`/api/technical/${selectedSymbol}`));
          if (technicalResponse.ok) {
            const technicalDataResponse = await technicalResponse.json();
            if (technicalDataResponse.status === 'success') {
              console.log('Live Dashboard: Backend technical data received:', technicalDataResponse);
              setTechnicalData({
                indicators: technicalDataResponse.indicators,
                signals: technicalDataResponse.signals,
                timestamp: technicalDataResponse.timestamp,
                symbol: technicalDataResponse.symbol
              });
              setActiveSignals(technicalDataResponse.signals || []);
              
              // Calculate signal strength using tiered confirmation logic
              if (technicalDataResponse.signals && technicalDataResponse.signals.length > 0) {
                const strength = calculateSignalStrength(technicalDataResponse.signals);
                setSignalStrength(strength);
                console.log('Live Dashboard: Signal strength calculated:', strength);
              }
              
              console.log('Live Dashboard: Using backend signals:', technicalDataResponse.signals?.length || 0);
            } else {
              throw new Error('Backend technical analysis failed');
            }
          } else {
            throw new Error('Backend technical API not available');
          }
        } catch (backendError) {
          console.log('Live Dashboard: Backend failed, using frontend calculations:', backendError.message);
          
          // Fallback to frontend calculations - use chart data or generate fallback data
          const fallbackData = generateMockChartData(selectedSymbol, realTimePrice || 100);
          const dataForCalculation = chartData && chartData.length > 0 ? chartData : fallbackData;
          if (dataForCalculation && dataForCalculation.length > 0) {
            const { indicators, signals } = calculateAllIndicators(dataForCalculation);
            console.log('Live Dashboard: Calculated indicators:', Object.keys(indicators));
            console.log('Live Dashboard: Generated signals:', signals.length);
            
            // Get latest values for key indicators
            const latestIndex = dataForCalculation.length - 1;
            const keyIndicators = {
              Current_Price: dataForCalculation[latestIndex]?.close,
              RSI: indicators.rsi?.[latestIndex],
              MACD: indicators.macd?.macd?.[latestIndex],
              MACD_Signal: indicators.macd?.signal?.[latestIndex],
              EMA_9: indicators.ema9?.[latestIndex],
              EMA_20: indicators.ema20?.[latestIndex],
              EMA_50: indicators.ema50?.[latestIndex],
              VWAP: indicators.vwap?.[latestIndex],
              BB_upper: indicators.bb?.upper?.[latestIndex],
              BB_lower: indicators.bb?.lower?.[latestIndex],
              ATR: indicators.atr?.[latestIndex]
            };
            
            setTechnicalData({
              indicators: keyIndicators,
              signals: signals,
              timestamp: new Date().toISOString(),
              symbol: selectedSymbol
            });
            setActiveSignals(signals);
            
            // Calculate signal strength using tiered confirmation logic
            if (signals && signals.length > 0) {
              const strength = calculateSignalStrength(signals);
              setSignalStrength(strength);
              console.log('Live Dashboard: Frontend signal strength calculated:', strength);
            }
            
            console.log('Live Dashboard: Frontend technical data calculated and set:', {
              indicators: keyIndicators,
              signalsCount: signals.length
            });
          }
        }

        // Load trade recommendation (realistic pricing based on market data)
        console.log('Live Dashboard: Generating realistic options data for', selectedSymbol);
        const currentPrice = technicalData?.indicators?.Current_Price || chartData[chartData.length - 1]?.close || 20;
        const rsi = technicalData?.indicators?.RSI || 50;
        
        // Calculate realistic options pricing based on current market conditions
        const nearestFridayExpiration = () => {
          const today = new Date();
          const daysUntilFriday = (5 - today.getDay() + 7) % 7 || 7; // Next Friday
          const nextFriday = new Date(today.getTime() + daysUntilFriday * 24 * 60 * 60 * 1000);
          return nextFriday.toISOString().split('T')[0];
        };
        
        // More realistic strike and premium calculation
        const atm_strike = Math.round(currentPrice); // At-the-money
        const otm_strike = atm_strike + 1; // $1 out-of-the-money
        const timeToExpiry = 6; // days
        
        // Realistic premium calculation (simplified Black-Scholes approximation)
        const intrinsicValue = Math.max(0, currentPrice - otm_strike);
        const timeValue = Math.max(0.05, (otm_strike - currentPrice) * 0.1 * (timeToExpiry / 30)); // Time decay
        const volatilityPremium = Math.abs(rsi - 50) * 0.01; // RSI-based volatility
        const realisticPremium = (intrinsicValue + timeValue + volatilityPremium).toFixed(2);
        
        // Calculate realistic bid/ask spread for options
        const premiumValue = parseFloat(realisticPremium);
        const bidAskSpread = Math.max(0.01, premiumValue * 0.05); // 5% spread, minimum 1 cent
        const bid = Math.max(0.01, premiumValue - bidAskSpread / 2).toFixed(2);
        const ask = (premiumValue + bidAskSpread / 2).toFixed(2);
        const midPrice = ((parseFloat(bid) + parseFloat(ask)) / 2).toFixed(2);
        
        const mockOptionsData = {
          symbol: selectedSymbol,
          recommendation: rsi < 40 ? 'CALL' : rsi > 60 ? 'PUT' : 'WAIT',
          confidence: Math.abs(rsi - 50) + 25, // Higher confidence when RSI is extreme
          reasoning: `Technical Analysis: RSI ${rsi?.toFixed(1)} ${rsi < 40 ? '(oversold - bullish signal)' : rsi > 60 ? '(overbought - bearish signal)' : '(neutral)'}, Current Price $${currentPrice.toFixed(2)}`,
          contract: {
            type: rsi < 40 ? 'CALL' : 'PUT',
            strike: otm_strike.toFixed(2),
            expiration: nearestFridayExpiration(),
            premium: midPrice, // Use mid price as the main premium
            bid: bid,
            ask: ask,
            delta: rsi < 40 ? '0.35' : '-0.35', // Realistic delta for OTM options
            volume: Math.floor(Math.random() * 2000 + 500).toLocaleString(),
            openInterest: Math.floor(Math.random() * 5000 + 1000).toLocaleString()
          },
          entry: currentPrice.toFixed(2),
          target: rsi < 40 ? (currentPrice * 1.08).toFixed(2) : (currentPrice * 0.92).toFixed(2),
          stopLoss: rsi < 40 ? (currentPrice * 0.96).toFixed(2) : (currentPrice * 1.04).toFixed(2),
          // Add bid/ask to trade plan
          tradePlan: {
            entryBid: bid,
            entryAsk: ask,
            entryMid: midPrice,
            recommendation: `Buy at ${bid} or better (avoid paying full ask of ${ask})`
          }
        };
        
        setTradeRecommendation(mockOptionsData);
        console.log('Live Dashboard: Mock options data set:', mockOptionsData);
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
          {signalStrength && (
            <div className={`mb-3 p-3 rounded border ${
              signalStrength.strength.includes('STRONG BUY') ? 'bg-green-900/20 border-green-600' :
              signalStrength.strength.includes('MODERATE BUY') ? 'bg-green-900/10 border-green-700' :
              signalStrength.strength.includes('WEAK BUY') ? 'bg-green-900/5 border-green-800' :
              signalStrength.strength.includes('STRONG SELL') ? 'bg-red-900/20 border-red-600' :
              signalStrength.strength.includes('MODERATE SELL') ? 'bg-red-900/10 border-red-700' :
              signalStrength.strength.includes('WEAK SELL') ? 'bg-red-900/5 border-red-800' :
              'bg-yellow-900/20 border-yellow-600'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span 
                  className="text-sm font-medium px-2 py-1 rounded"
                  style={{
                    backgroundColor: 
                      signalStrength.strength.includes('STRONG BUY') ? '#16a34a' :
                      signalStrength.strength.includes('MODERATE BUY') ? '#15803d' :
                      signalStrength.strength.includes('WEAK BUY') ? '#166534' :
                      signalStrength.strength.includes('STRONG SELL') ? '#dc2626' :
                      signalStrength.strength.includes('MODERATE SELL') ? '#ef4444' :
                      signalStrength.strength.includes('WEAK SELL') ? '#991b1b' :
                      '#ca8a04',
                    color: '#ffffff',
                    fontWeight: '600'
                  }}>
                  {signalStrength.strength}
                </span>
                <div className="text-xs" style={{ color: 'var(--text-primary)' }}>
                  {signalStrength.totalSignals} signals
                </div>
              </div>
              <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>{signalStrength.description}</div>
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
              <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>No active signals detected</div>
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
