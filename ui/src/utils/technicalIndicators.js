// Technical Indicators Utility Functions
// Direct implementation for reliable frontend calculations

export const calculateSMA = (data, period) => {
  const result = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(null);
    } else {
      const sum = data.slice(i - period + 1, i + 1).reduce((acc, val) => {
        const value = typeof val === 'number' ? val : val.close;
        return acc + value;
      }, 0);
      result.push(sum / period);
    }
  }
  return result;
};

export const calculateEMA = (data, period) => {
  const result = [];
  const multiplier = 2 / (period + 1);
  
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      // Handle both array of numbers and array of objects with .close
      result.push(typeof data[i] === 'number' ? data[i] : data[i].close);
    } else {
      const currentValue = typeof data[i] === 'number' ? data[i] : data[i].close;
      const ema = (currentValue * multiplier) + (result[i - 1] * (1 - multiplier));
      result.push(ema);
    }
  }
  return result;
};

export const calculateRSI = (data, period = 14) => {
  const result = [];
  const gains = [];
  const losses = [];
  
  for (let i = 1; i < data.length; i++) {
    const change = data[i].close - data[i - 1].close;
    gains.push(change > 0 ? change : 0);
    losses.push(change < 0 ? Math.abs(change) : 0);
  }
  
  for (let i = 0; i < data.length; i++) {
    if (i < period) {
      result.push(null);
    } else {
      const avgGain = gains.slice(i - period, i).reduce((a, b) => a + b, 0) / period;
      const avgLoss = losses.slice(i - period, i).reduce((a, b) => a + b, 0) / period;
      
      if (avgLoss === 0) {
        result.push(100);
      } else {
        const rs = avgGain / avgLoss;
        const rsi = 100 - (100 / (1 + rs));
        result.push(rsi);
      }
    }
  }
  return result;
};

export const calculateMACD = (data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) => {
  const fastEMA = calculateEMA(data, fastPeriod);
  const slowEMA = calculateEMA(data, slowPeriod);
  
  const macdLine = fastEMA.map((fast, i) => {
    if (fast === null || slowEMA[i] === null) return null;
    return fast - slowEMA[i];
  });
  
  // Calculate signal line (EMA of MACD line)
  const macdData = macdLine.map((value, i) => ({ close: value || 0 }));
  const signalLine = calculateEMA(macdData, signalPeriod);
  
  const histogram = macdLine.map((macd, i) => {
    if (macd === null || signalLine[i] === null) return null;
    return macd - signalLine[i];
  });
  
  return {
    macd: macdLine,
    signal: signalLine,
    histogram: histogram
  };
};

export const calculateBollingerBands = (data, period = 20, stdDev = 2) => {
  const sma = calculateSMA(data, period);
  const result = { upper: [], middle: [], lower: [] };
  
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.upper.push(null);
      result.middle.push(null);
      result.lower.push(null);
    } else {
      const slice = data.slice(i - period + 1, i + 1);
      const mean = sma[i];
      const variance = slice.reduce((acc, val) => acc + Math.pow(val.close - mean, 2), 0) / period;
      const standardDeviation = Math.sqrt(variance);
      
      result.upper.push(mean + (standardDeviation * stdDev));
      result.middle.push(mean);
      result.lower.push(mean - (standardDeviation * stdDev));
    }
  }
  return result;
};

export const calculateVWAP = (data) => {
  const result = [];
  let cumulativeVolume = 0;
  let cumulativeVolumePrice = 0;
  
  for (let i = 0; i < data.length; i++) {
    const typicalPrice = (data[i].high + data[i].low + data[i].close) / 3;
    const volume = data[i].volume || 1;
    
    cumulativeVolumePrice += typicalPrice * volume;
    cumulativeVolume += volume;
    
    result.push(cumulativeVolumePrice / cumulativeVolume);
  }
  return result;
};

export const calculateATR = (data, period = 14) => {
  const result = [];
  const trueRanges = [];
  
  for (let i = 1; i < data.length; i++) {
    const high = data[i].high;
    const low = data[i].low;
    const prevClose = data[i - 1].close;
    
    const tr = Math.max(
      high - low,
      Math.abs(high - prevClose),
      Math.abs(low - prevClose)
    );
    
    trueRanges.push(tr);
    
    if (trueRanges.length >= period) {
      const atr = trueRanges.slice(-period).reduce((sum, tr) => sum + tr, 0) / period;
      result.push(atr);
    } else {
      result.push(null);
    }
  }
  
  return result;
};

// Calculate TTM Squeeze
export const calculateTTMSqueeze = (data, bbPeriod = 20, bbStdDev = 2, kcPeriod = 20, kcMultiplier = 1.5) => {
  const result = [];
  
  // Calculate Bollinger Bands
  const bb = calculateBollingerBands(data, bbPeriod, bbStdDev);
  
  // Calculate Keltner Channels (using EMA and ATR)
  const ema = calculateEMA(data.map(d => d.close), kcPeriod);
  const atr = calculateATR(data, kcPeriod);
  
  for (let i = 0; i < data.length; i++) {
    if (bb.upper[i] && bb.lower[i] && ema[i] && atr[i]) {
      const kcUpper = ema[i] + (kcMultiplier * atr[i]);
      const kcLower = ema[i] - (kcMultiplier * atr[i]);
      
      // Squeeze occurs when BB is inside KC
      const inSqueeze = bb.lower[i] > kcLower && bb.upper[i] < kcUpper;
      
      // Momentum oscillator (close relative to midpoint of KC)
      const momentum = data[i].close - ((kcUpper + kcLower) / 2);
      
      // Determine bar color based on momentum direction
      let barColor = 'gray';
      if (i > 0 && result[i-1]) {
        if (momentum > result[i-1].momentum) {
          barColor = momentum > 0 ? 'lime' : 'red';
        } else {
          barColor = momentum > 0 ? 'green' : 'maroon';
        }
      }
      
      result.push({
        inSqueeze,
        momentum,
        barColor,
        kcUpper,
        kcLower
      });
    } else {
      result.push(null);
    }
  }
  
  return result;
};

// Detect Support and Resistance Levels
export const detectSupportResistance = (data, lookback = 20, touchThreshold = 0.02) => {
  const levels = [];
  const highs = [];
  const lows = [];
  
  // Find local highs and lows
  for (let i = lookback; i < data.length - lookback; i++) {
    let isHigh = true;
    let isLow = true;
    
    for (let j = i - lookback; j <= i + lookback; j++) {
      if (j !== i) {
        if (data[j].high >= data[i].high) isHigh = false;
        if (data[j].low <= data[i].low) isLow = false;
      }
    }
    
    if (isHigh) highs.push({ price: data[i].high, index: i, type: 'resistance' });
    if (isLow) lows.push({ price: data[i].low, index: i, type: 'support' });
  }
  
  // Group similar levels
  const allLevels = [...highs, ...lows];
  const groupedLevels = [];
  
  allLevels.forEach(level => {
    const existing = groupedLevels.find(g => 
      Math.abs(g.price - level.price) / level.price < touchThreshold
    );
    
    if (existing) {
      existing.touches++;
      existing.lastTouch = Math.max(existing.lastTouch, level.index);
    } else {
      groupedLevels.push({
        price: level.price,
        type: level.type,
        touches: 1,
        lastTouch: level.index
      });
    }
  });
  
  // Return only significant levels (multiple touches)
  return groupedLevels.filter(level => level.touches >= 2);
};

// Detect Double Top/Bottom Patterns
export const detectDoubleTopBottom = (data, lookback = 50, tolerance = 0.03) => {
  const patterns = [];
  const peaks = [];
  const troughs = [];
  
  // Find significant peaks and troughs
  for (let i = lookback; i < data.length - lookback; i++) {
    let isPeak = true;
    let isTrough = true;
    
    for (let j = i - lookback; j <= i + lookback; j++) {
      if (j !== i) {
        if (data[j].high >= data[i].high) isPeak = false;
        if (data[j].low <= data[i].low) isTrough = false;
      }
    }
    
    if (isPeak) peaks.push({ price: data[i].high, index: i });
    if (isTrough) troughs.push({ price: data[i].low, index: i });
  }
  
  // Look for double tops
  for (let i = 0; i < peaks.length - 1; i++) {
    for (let j = i + 1; j < peaks.length; j++) {
      const peak1 = peaks[i];
      const peak2 = peaks[j];
      
      if (Math.abs(peak1.price - peak2.price) / peak1.price < tolerance &&
          peak2.index - peak1.index > 10) {
        patterns.push({
          type: 'Double Top',
          price: (peak1.price + peak2.price) / 2,
          startIndex: peak1.index,
          endIndex: peak2.index,
          signal: 'BEARISH'
        });
      }
    }
  }
  
  // Look for double bottoms
  for (let i = 0; i < troughs.length - 1; i++) {
    for (let j = i + 1; j < troughs.length; j++) {
      const trough1 = troughs[i];
      const trough2 = troughs[j];
      
      if (Math.abs(trough1.price - trough2.price) / trough1.price < tolerance &&
          trough2.index - trough1.index > 10) {
        patterns.push({
          type: 'Double Bottom',
          price: (trough1.price + trough2.price) / 2,
          startIndex: trough1.index,
          endIndex: trough2.index,
          signal: 'BULLISH'
        });
      }
    }
  }
  
  return patterns;
};

// Advanced Technical Analysis Signal Generation
export const generateSignals = (data, indicators) => {
  const signals = [];
  const latest = data[data.length - 1];
  const latestIndex = data.length - 1;
  const price = latest.close;
  
  // 1. ENHANCED RSI SIGNALS WITH DIVERGENCE DETECTION
  if (indicators.rsi && indicators.rsi[latestIndex] && indicators.macd) {
    const rsi = indicators.rsi[latestIndex];
    const macd = indicators.macd.macd[latestIndex];
    const macdSignal = indicators.macd.signal[latestIndex];
    const prevMacd = indicators.macd.macd[latestIndex - 1];
    
    // RSI Overbought with MACD Divergence Check
    if (rsi > 70) {
      let divergenceWarning = '';
      if (macd && prevMacd && macd < prevMacd) {
        divergenceWarning = ' - MACD weakening, caution advised';
      }
      signals.push({
        type: 'RSI Overbought',
        signal: 'BEARISH',
        value: rsi.toFixed(2),
        description: `RSI above 70 indicates overbought conditions${divergenceWarning}`,
        confidence: macd && prevMacd && macd < prevMacd ? 'HIGH' : 'MEDIUM'
      });
    } 
    // RSI Oversold with MACD Confirmation
    else if (rsi < 30) {
      let macdConfirmation = '';
      if (macd && macdSignal && macd > macdSignal) {
        macdConfirmation = ' - MACD supports bounce';
      }
      signals.push({
        type: 'RSI Oversold',
        signal: 'BULLISH',
        value: rsi.toFixed(2),
        description: `RSI below 30 indicates oversold conditions${macdConfirmation}`,
        confidence: macd && macdSignal && macd > macdSignal ? 'HIGH' : 'MEDIUM'
      });
    }
    // RSI Bullish Zone
    else if (rsi > 50) {
      signals.push({
        type: 'RSI Bullish Zone',
        signal: 'BULLISH',
        value: rsi.toFixed(2),
        description: 'RSI above 50 indicates bullish momentum',
        confidence: 'LOW'
      });
    }
    // RSI Bearish Zone
    else {
      signals.push({
        type: 'RSI Bearish Zone',
        signal: 'BEARISH',
        value: rsi.toFixed(2),
        description: 'RSI below 50 indicates bearish pressure',
        confidence: 'LOW'
      });
    }
  }
  
  // 2. ENHANCED MACD SIGNALS WITH REVERSAL DETECTION
  if (indicators.macd && indicators.macd.macd[latestIndex] && indicators.macd.signal[latestIndex]) {
    const macd = indicators.macd.macd[latestIndex];
    const signal = indicators.macd.signal[latestIndex];
    const prevMacd = indicators.macd.macd[latestIndex - 1];
    const prevSignal = indicators.macd.signal[latestIndex - 1];
    const prev2Macd = indicators.macd.macd[latestIndex - 2];
    
    if (prevMacd && prevSignal) {
      // MACD Bullish Crossover
      if (prevMacd <= prevSignal && macd > signal) {
        signals.push({
          type: 'MACD Bullish Crossover',
          signal: 'BULLISH',
          value: `${macd.toFixed(4)} / ${signal.toFixed(4)}`,
          description: 'MACD line crossed above signal line - momentum turning bullish',
          confidence: 'HIGH'
        });
      } 
      // MACD Bearish Crossover
      else if (prevMacd >= prevSignal && macd < signal) {
        signals.push({
          type: 'MACD Bearish Crossover',
          signal: 'BEARISH',
          value: `${macd.toFixed(4)} / ${signal.toFixed(4)}`,
          description: 'MACD line crossed below signal line - momentum turning bearish',
          confidence: 'HIGH'
        });
      }
      // MACD Reversal Detection (flattening or dropping)
      else if (prev2Macd && macd > signal) {
        const macdMomentum = macd - prevMacd;
        const prevMomentum = prevMacd - prev2Macd;
        
        if (prevMomentum > 0 && macdMomentum < prevMomentum * 0.5) {
          signals.push({
            type: 'MACD Momentum Weakening',
            signal: 'CAUTION',
            value: `${macd.toFixed(4)} (slowing)`,
            description: 'MACD bullish momentum is flattening - potential reversal ahead',
            confidence: 'MEDIUM'
          });
        }
      }
    }
  }
  
  // Bollinger Bands Signals
  if (indicators.bb && indicators.bb.upper[latestIndex] && indicators.bb.lower[latestIndex]) {
    const price = latest.close;
    const upper = indicators.bb.upper[latestIndex];
    const lower = indicators.bb.lower[latestIndex];
    
    if (price >= upper) {
      signals.push({
        type: 'Bollinger Upper Band',
        signal: 'BEARISH',
        value: `$${price.toFixed(2)} >= $${upper.toFixed(2)}`,
        description: 'Price touching upper Bollinger Band'
      });
    } else if (price <= lower) {
      signals.push({
        type: 'Bollinger Lower Band',
        signal: 'BULLISH',
        value: `$${price.toFixed(2)} <= $${lower.toFixed(2)}`,
        description: 'Price touching lower Bollinger Band'
      });
    }
  }
  
  // 3. ENHANCED EMA SIGNALS WITH DYNAMIC GOLDEN/DEATH CROSS
  if (indicators.ema9 && indicators.ema20 && indicators.ema50) {
    const ema9 = indicators.ema9[latestIndex];
    const ema20 = indicators.ema20[latestIndex];
    const ema50 = indicators.ema50[latestIndex];
    const prevEma9 = indicators.ema9[latestIndex - 1];
    const prevEma20 = indicators.ema20[latestIndex - 1];
    const prevEma50 = indicators.ema50[latestIndex - 1];
    
    // Perfect EMA Alignment Detection
    if (price > ema9 && ema9 > ema20 && ema20 > ema50) {
      signals.push({
        type: 'EMA Perfect Bullish Stack',
        signal: 'BULLISH',
        value: `Price > EMA9 > EMA20 > EMA50`,
        description: 'Perfect bullish alignment - strong uptrend confirmed',
        confidence: 'HIGH'
      });
    } else if (price < ema9 && ema9 < ema20 && ema20 < ema50) {
      signals.push({
        type: 'EMA Perfect Bearish Stack',
        signal: 'BEARISH',
        value: `Price < EMA9 < EMA20 < EMA50`,
        description: 'Perfect bearish alignment - strong downtrend confirmed',
        confidence: 'HIGH'
      });
    }
    
    // Dynamic Golden Cross and Death Cross Detection
    if (prevEma9 && prevEma20) {
      // Golden Cross (9/20)
      if (prevEma9 <= prevEma20 && ema9 > ema20) {
        // Check if this is recent (within last 5 periods)
        let recentCross = false;
        for (let i = 1; i <= Math.min(5, latestIndex); i++) {
          const checkEma9 = indicators.ema9[latestIndex - i];
          const checkEma20 = indicators.ema20[latestIndex - i];
          if (checkEma9 <= checkEma20) {
            recentCross = true;
            break;
          }
        }
        
        signals.push({
          type: recentCross ? 'Golden Cross (Recent)' : 'Golden Cross Active',
          signal: 'BULLISH',
          value: `$${ema9.toFixed(2)} > $${ema20.toFixed(2)}`,
          description: recentCross ? 'FRESH Golden Cross - EMA 9 just crossed above EMA 20!' : 'Golden Cross active - EMA 9 above EMA 20',
          confidence: recentCross ? 'HIGH' : 'MEDIUM'
        });
      } 
      // Death Cross (9/20)
      else if (prevEma9 >= prevEma20 && ema9 < ema20) {
        // Check if this is recent
        let recentCross = false;
        for (let i = 1; i <= Math.min(5, latestIndex); i++) {
          const checkEma9 = indicators.ema9[latestIndex - i];
          const checkEma20 = indicators.ema20[latestIndex - i];
          if (checkEma9 >= checkEma20) {
            recentCross = true;
            break;
          }
        }
        
        signals.push({
          type: recentCross ? 'Death Cross (Recent)' : 'Death Cross Active',
          signal: 'BEARISH',
          value: `$${ema9.toFixed(2)} < $${ema20.toFixed(2)}`,
          description: recentCross ? 'FRESH Death Cross - EMA 9 just crossed below EMA 20!' : 'Death Cross active - EMA 9 below EMA 20',
          confidence: recentCross ? 'HIGH' : 'MEDIUM'
        });
      }
    }
    
    // 4. ENHANCED VWAP ZONE ANALYSIS
    if (indicators.vwap && indicators.vwap[latestIndex]) {
      const vwap = indicators.vwap[latestIndex];
      const vwapDistance = ((price - vwap) / vwap) * 100;
      
      if (vwapDistance > 2) {
        signals.push({
          type: 'VWAP Upper Zone',
          signal: 'CAUTION',
          value: `+${vwapDistance.toFixed(1)}% above VWAP`,
          description: 'Price extended above VWAP - potential pullback zone',
          confidence: 'MEDIUM'
        });
      } else if (vwapDistance > 0) {
        signals.push({
          type: 'VWAP Bullish Zone',
          signal: 'BULLISH',
          value: `+${vwapDistance.toFixed(1)}% above VWAP`,
          description: 'Between mid & top VWAP = bullish zone - institutional support',
          confidence: 'MEDIUM'
        });
      } else if (vwapDistance > -2) {
        signals.push({
          type: 'VWAP Support Zone',
          signal: 'NEUTRAL',
          value: `${vwapDistance.toFixed(1)}% from VWAP`,
          description: 'Near VWAP support - watch for direction',
          confidence: 'LOW'
        });
      } else {
        signals.push({
          type: 'VWAP Bounce Opportunity',
          signal: 'BULLISH',
          value: `${vwapDistance.toFixed(1)}% below VWAP`,
          description: 'Below lower VWAP = bounce opportunity - oversold vs institutions',
          confidence: 'HIGH'
        });
      }
    }
  }
  
  // 5. TTM SQUEEZE SIGNALS
  if (indicators.ttmSqueeze && indicators.ttmSqueeze[latestIndex]) {
    const squeeze = indicators.ttmSqueeze[latestIndex];
    const prevSqueeze = indicators.ttmSqueeze[latestIndex - 1];
    
    if (squeeze.inSqueeze) {
      signals.push({
        type: 'TTM Squeeze Active',
        signal: 'NEUTRAL',
        value: `${squeeze.barColor} bar`,
        description: 'TTM Squeeze active - volatility compression, breakout imminent',
        confidence: 'HIGH'
      });
    } else if (prevSqueeze && prevSqueeze.inSqueeze) {
      // Squeeze just ended - breakout signal
      const breakoutDirection = squeeze.momentum > 0 ? 'BULLISH' : 'BEARISH';
      signals.push({
        type: 'TTM Squeeze Breakout',
        signal: breakoutDirection,
        value: `${squeeze.barColor} breakout`,
        description: `TTM Squeeze BREAKOUT - ${breakoutDirection.toLowerCase()} momentum explosion!`,
        confidence: 'HIGH'
      });
    }
    
    // Momentum bar color signals
    if (squeeze.barColor === 'lime') {
      signals.push({
        type: 'TTM Green Bar',
        signal: 'BULLISH',
        value: 'Accelerating up',
        description: 'TTM momentum accelerating upward - strong bullish signal',
        confidence: 'HIGH'
      });
    } else if (squeeze.barColor === 'red') {
      signals.push({
        type: 'TTM Red Bar',
        signal: 'BEARISH',
        value: 'Accelerating down',
        description: 'TTM momentum accelerating downward - strong bearish signal',
        confidence: 'HIGH'
      });
    }
  }
  
  // 6. SUPPORT/RESISTANCE SIGNALS
  if (indicators.supportResistance && indicators.supportResistance.length > 0) {
    const currentPrice = latest.close;
    
    indicators.supportResistance.forEach(level => {
      const distance = Math.abs(currentPrice - level.price) / level.price;
      
      if (distance < 0.01) { // Within 1% of level
        if (level.type === 'support') {
          signals.push({
            type: 'At Support Level',
            signal: 'BULLISH',
            value: `$${level.price.toFixed(2)} (${level.touches} touches)`,
            description: `Price at key support level - bounce opportunity (${level.touches} previous touches)`,
            confidence: level.touches >= 3 ? 'HIGH' : 'MEDIUM'
          });
        } else {
          signals.push({
            type: 'At Resistance Level',
            signal: 'BEARISH',
            value: `$${level.price.toFixed(2)} (${level.touches} touches)`,
            description: `Price at key resistance level - reversal likely (${level.touches} previous touches)`,
            confidence: level.touches >= 3 ? 'HIGH' : 'MEDIUM'
          });
        }
      }
    });
  }
  
  // 7. PATTERN RECOGNITION SIGNALS
  if (indicators.patterns && indicators.patterns.length > 0) {
    // Check for recent patterns (within last 20 bars)
    const recentPatterns = indicators.patterns.filter(pattern => 
      latestIndex - pattern.endIndex < 20
    );
    
    recentPatterns.forEach(pattern => {
      signals.push({
        type: pattern.type,
        signal: pattern.signal,
        value: `$${pattern.price.toFixed(2)}`,
        description: `${pattern.type} pattern detected - ${pattern.signal.toLowerCase()} reversal expected`,
        confidence: 'HIGH'
      });
    });
  }
  
  return signals;
};

// TIERED CONFIRMATION LOGIC - Calculate Signal Strength
export const calculateSignalStrength = (signals) => {
  let bullishCount = 0;
  let bearishCount = 0;
  let highConfidenceCount = 0;
  let totalWeight = 0;
  
  // Weight signals by confidence and type
  signals.forEach(signal => {
    const weight = signal.confidence === 'HIGH' ? 3 : signal.confidence === 'MEDIUM' ? 2 : 1;
    totalWeight += weight;
    
    if (signal.confidence === 'HIGH') highConfidenceCount++;
    
    if (signal.signal === 'BULLISH') {
      bullishCount += weight;
    } else if (signal.signal === 'BEARISH') {
      bearishCount += weight;
    }
  });
  
  const netScore = bullishCount - bearishCount;
  const confirmationCount = Math.max(bullishCount, bearishCount);
  
  // Determine signal strength with more realistic thresholds
  let strength = 'WAIT';
  let color = 'yellow';
  let description = 'Mixed signals - wait for clearer direction';
  
  // Strong signals: 5+ weighted confirmations with 2+ high-confidence OR 7+ total confirmations
  if ((confirmationCount >= 5 && highConfidenceCount >= 2) || confirmationCount >= 7) {
    strength = netScore > 0 ? 'STRONG BUY' : 'STRONG SELL';
    color = netScore > 0 ? 'green' : 'red';
    description = `${confirmationCount} confirmations with ${highConfidenceCount} high-confidence signals`;
  }
  // Moderate signals: 3+ weighted confirmations with 1+ high-confidence OR 4+ total confirmations
  else if ((confirmationCount >= 3 && highConfidenceCount >= 1) || confirmationCount >= 4) {
    strength = netScore > 0 ? 'MODERATE BUY' : 'MODERATE SELL';
    color = netScore > 0 ? 'green' : 'red';
    description = `${confirmationCount} confirmations - moderate confidence`;
  }
  // Weak signals: 2+ weighted confirmations (but still actionable)
  else if (confirmationCount >= 2 && Math.abs(netScore) >= 2) {
    strength = netScore > 0 ? 'WEAK BUY' : 'WEAK SELL';
    color = netScore > 0 ? 'green' : 'red';
    description = `${confirmationCount} confirmations - low confidence, watch closely`;
  }
  
  return {
    strength,
    color,
    description,
    bullishCount,
    bearishCount,
    highConfidenceCount,
    netScore: Math.abs(netScore),
    totalSignals: signals.length
  };
};

// Calculate all indicators and generate signals
export const calculateAllIndicators = (data) => {
  if (!data || data.length < 20) {
    return { indicators: {}, signals: [] };
  }
  
  // Extract close prices for indicators that need them
  const closePrices = data.map(d => d.close);
  
  const indicators = {
    sma20: calculateSMA(closePrices, 20),
    ema9: calculateEMA(closePrices, 9),
    ema20: calculateEMA(closePrices, 20),
    ema50: calculateEMA(closePrices, 50),
    rsi: calculateRSI(closePrices),
    macd: calculateMACD(closePrices),
    bb: calculateBollingerBands(data),
    vwap: calculateVWAP(data),
    atr: calculateATR(data),
    ttmSqueeze: calculateTTMSqueeze(data),
    supportResistance: detectSupportResistance(data),
    patterns: detectDoubleTopBottom(data)
  };
  
  const signals = generateSignals(data, indicators);
  
  return { indicators, signals };
};
