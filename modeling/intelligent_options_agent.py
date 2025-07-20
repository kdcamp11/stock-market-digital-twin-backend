"""
Intelligent Options Trading Agent
Analyzes market conditions, recommends Call/Put, selects contracts, and generates trade plans
"""

import os
import requests
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas_ta as ta

class IntelligentOptionsAgent:
    def __init__(self):
        self.alpaca_api_key = os.getenv('ALPACA_API_KEY')
        self.alpaca_api_secret = os.getenv('ALPACA_API_SECRET')
        self.tradier_token = os.getenv('TRADIER_TOKEN')  # User will need to add this
        
        # Import Tradier provider
        try:
            from modeling.tradier_options_provider import get_tradier_options_provider
            self.tradier_provider = get_tradier_options_provider()
        except ImportError:
            self.tradier_provider = None
        
        # Trading parameters
        self.profit_target_pct = 35  # 30-40% profit target
        self.stop_loss_pct = 17.5   # 15-20% stop loss
        self.min_delta = 0.4
        self.max_delta = 0.6
        self.min_volume = 500
        self.max_ask = 3.50
        self.min_open_interest = 1000
        
    def _get_last_trading_day(self) -> str:
        """
        Get the last active trading day (skip weekends and holidays)
        Returns date string in YYYY-MM-DD format
        """
        from datetime import datetime, timedelta
        
        today = datetime.now()
        
        # Go back day by day until we find a weekday
        current_date = today
        while current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            current_date -= timedelta(days=1)
        
        # For simplicity, assume weekdays are trading days
        # In production, you'd check against a holiday calendar
        return current_date.strftime('%Y-%m-%d')
    
    def analyze_stock_chart(self, symbol: str, timeframe: str = '1D') -> Dict:
        """
        STEP 1: Analyze Stock Chart via Alpaca API
        Returns trend analysis and indicator signals based on last trading day
        """
        try:
            # Get last trading day for analysis
            last_trading_day = self._get_last_trading_day()
            
            # Get OHLCV data from database up to last trading day
            conn = sqlite3.connect('data_ingestion/stocks.db')
            query = '''
            SELECT Date, Open, High, Low, Close, Volume 
            FROM stock_prices 
            WHERE Symbol = ? AND Date <= ?
            ORDER BY Date DESC 
            LIMIT 200
            '''
            df = pd.read_sql_query(query, conn, params=(symbol, last_trading_day))
            conn.close()
            
            if df.empty:
                return {'error': f'No data found for {symbol}'}
            
            # Reverse to chronological order for technical analysis
            df = df.sort_values('Date').reset_index(drop=True)
            
            # Convert to numeric
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(df)
            
            # Analyze trend and signals
            analysis = self._analyze_trend_and_signals(df, indicators)
            
            # Detect support/resistance levels
            sr_levels = self._detect_support_resistance(df)
            
            # Analyze price action
            price_action = self._analyze_price_action(df)
            
            # Get the actual date of the data being analyzed
            analysis_date = df['Date'].iloc[-1] if not df.empty else last_trading_day
            
            return {
                'symbol': symbol,
                'current_price': float(df['Close'].iloc[-1]),
                'trend_direction': analysis['trend'],
                'trend_strength': analysis['strength'],
                'recommendation': analysis['recommendation'],
                'confidence': analysis['confidence'],
                'indicators': indicators,
                'support_resistance': sr_levels,
                'price_action': price_action,
                'signals_aligned': analysis['signals_aligned'],
                'explanation': analysis['explanation'],
                'analysis_date': analysis_date,
                'last_trading_day': last_trading_day
            }
            
        except Exception as e:
            return {'error': f'Chart analysis failed: {str(e)}'}
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all technical indicators"""
        try:
            # EMAs and SMAs
            df['EMA_9'] = ta.ema(df['Close'], length=9)
            df['EMA_20'] = ta.ema(df['Close'], length=20)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            
            # VWAP
            df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
            
            # MACD
            macd = ta.macd(df['Close'])
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_Signal'] = macd['MACDs_12_26_9']
            df['MACD_Histogram'] = macd['MACDh_12_26_9']
            
            # RSI
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # Bollinger Bands for TTM Squeeze approximation
            bb = ta.bbands(df['Close'], length=20)
            kc = ta.kc(df['High'], df['Low'], df['Close'], length=20)
            
            # TTM Squeeze (simplified)
            df['BB_Upper'] = bb['BBU_20_2.0']
            df['BB_Lower'] = bb['BBL_20_2.0']
            df['KC_Upper'] = kc['KCUe_20_2']
            df['KC_Lower'] = kc['KCLe_20_2']
            
            # Squeeze condition: BB inside KC
            df['TTM_Squeeze'] = (df['BB_Upper'] < df['KC_Upper']) & (df['BB_Lower'] > df['KC_Lower'])
            
            # Get latest values
            latest = df.iloc[-1]
            
            return {
                'EMA_9': float(latest['EMA_9']) if not pd.isna(latest['EMA_9']) else None,
                'EMA_20': float(latest['EMA_20']) if not pd.isna(latest['EMA_20']) else None,
                'SMA_50': float(latest['SMA_50']) if not pd.isna(latest['SMA_50']) else None,
                'SMA_200': float(latest['SMA_200']) if not pd.isna(latest['SMA_200']) else None,
                'VWAP': float(latest['VWAP']) if not pd.isna(latest['VWAP']) else None,
                'MACD': float(latest['MACD']) if not pd.isna(latest['MACD']) else None,
                'MACD_Signal': float(latest['MACD_Signal']) if not pd.isna(latest['MACD_Signal']) else None,
                'RSI': float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
                'TTM_Squeeze': bool(latest['TTM_Squeeze']) if not pd.isna(latest['TTM_Squeeze']) else False,
                'current_price': float(latest['Close'])
            }
            
        except Exception as e:
            print(f"Indicator calculation error: {e}")
            return {}
    
    def _analyze_trend_and_signals(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """Analyze trend direction and signal alignment"""
        try:
            current_price = indicators.get('current_price', 0)
            signals = []
            bullish_signals = 0
            bearish_signals = 0
            
            # EMA Analysis
            if indicators.get('EMA_9') and indicators.get('EMA_20'):
                if indicators['EMA_9'] > indicators['EMA_20']:
                    signals.append("EMA 9 > EMA 20 (Bullish)")
                    bullish_signals += 1
                else:
                    signals.append("EMA 9 < EMA 20 (Bearish)")
                    bearish_signals += 1
            
            # Price vs VWAP
            if indicators.get('VWAP'):
                if current_price > indicators['VWAP']:
                    signals.append("Price > VWAP (Bullish)")
                    bullish_signals += 1
                else:
                    signals.append("Price < VWAP (Bearish)")
                    bearish_signals += 1
            
            # MACD Analysis
            if indicators.get('MACD') and indicators.get('MACD_Signal'):
                if indicators['MACD'] > indicators['MACD_Signal']:
                    signals.append("MACD > Signal (Bullish)")
                    bullish_signals += 1
                else:
                    signals.append("MACD < Signal (Bearish)")
                    bearish_signals += 1
            
            # RSI Analysis
            if indicators.get('RSI'):
                rsi = indicators['RSI']
                if rsi > 70:
                    signals.append("RSI Overbought (Bearish)")
                    bearish_signals += 1
                elif rsi < 30:
                    signals.append("RSI Oversold (Bullish)")
                    bullish_signals += 1
                elif 45 < rsi < 55:
                    signals.append("RSI Neutral")
                elif rsi > 50:
                    signals.append("RSI Above 50 (Bullish)")
                    bullish_signals += 0.5
                else:
                    signals.append("RSI Below 50 (Bearish)")
                    bearish_signals += 0.5
            
            # TTM Squeeze
            if indicators.get('TTM_Squeeze'):
                signals.append("TTM Squeeze Active (Volatility Building)")
            
            # Determine overall trend
            total_signals = bullish_signals + bearish_signals
            if total_signals == 0:
                trend = 'NEUTRAL'
                recommendation = 'WAIT'
                confidence = 0
            else:
                bullish_pct = bullish_signals / total_signals
                if bullish_pct >= 0.55:  
                    trend = 'BULLISH'
                    recommendation = 'CALL'
                    confidence = min(5, int(bullish_signals))
                elif bullish_pct <= 0.45:  
                    trend = 'BEARISH'
                    recommendation = 'PUT'
                    confidence = min(5, int(bearish_signals))
                elif bullish_signals > bearish_signals and bullish_signals >= 1:
                    trend = 'BULLISH'
                    recommendation = 'CALL'
                    confidence = min(3, int(bullish_signals))
                elif bearish_signals > bullish_signals and bearish_signals >= 1:
                    trend = 'BEARISH'
                    recommendation = 'PUT'
                    confidence = min(3, int(bearish_signals))
                else:
                    trend = 'NEUTRAL'
                    recommendation = 'WAIT'
                    confidence = 2
            
            explanation = f"Analysis shows {bullish_signals} bullish and {bearish_signals} bearish signals. " + \
                         f"Trend: {trend}. Recommendation: {recommendation}. Signals: {', '.join(signals[:3])}"
            
            return {
                'trend': trend,
                'strength': confidence,
                'recommendation': recommendation,
                'confidence': confidence,
                'signals_aligned': int(max(bullish_signals, bearish_signals)),
                'explanation': explanation,
                'all_signals': signals
            }
            
        except Exception as e:
            return {
                'trend': 'NEUTRAL',
                'recommendation': 'WAIT',
                'confidence': 0,
                'signals_aligned': 0,
                'explanation': f'Analysis error: {str(e)}'
            }
    
    def _detect_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Detect support and resistance levels"""
        try:
            # Simple pivot point detection
            highs = df['High'].rolling(window=5, center=True).max()
            lows = df['Low'].rolling(window=5, center=True).min()
            
            resistance_levels = []
            support_levels = []
            
            for i in range(2, len(df) - 2):
                if df['High'].iloc[i] == highs.iloc[i]:
                    resistance_levels.append(float(df['High'].iloc[i]))
                if df['Low'].iloc[i] == lows.iloc[i]:
                    support_levels.append(float(df['Low'].iloc[i]))
            
            # Get recent levels
            current_price = float(df['Close'].iloc[-1])
            nearby_resistance = [r for r in resistance_levels if r > current_price][:3]
            nearby_support = [s for s in support_levels if s < current_price][-3:]
            
            return {
                'resistance_levels': sorted(nearby_resistance),
                'support_levels': sorted(nearby_support, reverse=True),
                'current_price': current_price
            }
            
        except Exception as e:
            return {'error': f'S/R detection failed: {str(e)}'}
    
    def _analyze_price_action(self, df: pd.DataFrame) -> Dict:
        """Analyze price action patterns"""
        try:
            recent_df = df.tail(10)  # Last 10 candles
            
            # Wick analysis
            recent_df['upper_wick'] = recent_df['High'] - recent_df[['Open', 'Close']].max(axis=1)
            recent_df['lower_wick'] = recent_df[['Open', 'Close']].min(axis=1) - recent_df['Low']
            recent_df['body_size'] = abs(recent_df['Close'] - recent_df['Open'])
            
            # Pattern detection
            patterns = []
            
            # Doji detection
            avg_body = recent_df['body_size'].mean()
            if recent_df['body_size'].iloc[-1] < avg_body * 0.3:
                patterns.append("Doji (Indecision)")
            
            # Hammer/Shooting Star
            latest = recent_df.iloc[-1]
            if latest['lower_wick'] > latest['body_size'] * 2:
                patterns.append("Hammer (Bullish Reversal)")
            elif latest['upper_wick'] > latest['body_size'] * 2:
                patterns.append("Shooting Star (Bearish Reversal)")
            
            return {
                'patterns': patterns,
                'avg_body_size': float(avg_body),
                'latest_candle': {
                    'body_size': float(latest['body_size']),
                    'upper_wick': float(latest['upper_wick']),
                    'lower_wick': float(latest['lower_wick'])
                }
            }
            
        except Exception as e:
            return {'error': f'Price action analysis failed: {str(e)}'}
    
    def get_options_chain_tradier(self, symbol: str, option_type: str = 'call') -> Dict:
        """
        STEP 2: Pull Live Options Chain via Tradier API
        """
        if self.tradier_provider and self.tradier_provider.is_available():
            try:
                # Get real-time options chain
                chain = self.tradier_provider.get_options_chain(symbol)
                if 'error' not in chain:
                    # Filter contracts based on our criteria
                    contracts = self.tradier_provider.filter_contracts(
                        chain, 
                        option_type,
                        min_delta=self.min_delta,
                        max_delta=self.max_delta,
                        min_volume=self.min_volume,
                        max_ask=self.max_ask,
                        min_open_interest=self.min_open_interest
                    )
                    
                    return {
                        'contracts': contracts,
                        'total_found': len(contracts),
                        'source': 'tradier_live',
                        'expiration': chain.get('expiration'),
                        'current_price': self.tradier_provider.get_current_price(symbol)
                    }
                
                return {'error': chain.get('error', 'Unknown Tradier error')}
                
            except Exception as e:
                return {'error': f'Tradier API error: {str(e)}'}
        
        # Fallback: return error instead of mock data for accuracy
        return {'error': 'Real-time options data unavailable. Please configure Tradier API token.'}
    
    def _filter_options_contracts(self, chain_data: Dict, option_type: str) -> Dict:
        """Filter options contracts based on criteria"""
        try:
            contracts = []
            options = chain_data.get('options', {}).get('option', [])
            
            for option in options:
                if option.get('option_type').lower() != option_type.lower():
                    continue
                
                # Apply filters
                delta = abs(float(option.get('delta', 0)))
                volume = int(option.get('volume', 0))
                ask = float(option.get('ask', 999))
                open_interest = int(option.get('open_interest', 0))
                
                if (self.min_delta <= delta <= self.max_delta and
                    volume >= self.min_volume and
                    ask <= self.max_ask and
                    open_interest >= self.min_open_interest):
                    
                    contracts.append({
                        'symbol': option.get('symbol'),
                        'strike': float(option.get('strike')),
                        'expiration': option.get('expiration_date'),
                        'ask': ask,
                        'bid': float(option.get('bid', 0)),
                        'delta': delta,
                        'volume': volume,
                        'open_interest': open_interest,
                        'type': option_type.upper()
                    })
            
            # Sort by volume and delta
            contracts.sort(key=lambda x: (x['volume'], abs(x['delta'] - 0.5)), reverse=True)
            
            return {
                'contracts': contracts[:5],  # Top 5 contracts
                'total_found': len(contracts)
            }
            
        except Exception as e:
            return {'error': f'Contract filtering failed: {str(e)}'}
    

    
    def build_trade_plan(self, contract: Dict, analysis: Dict) -> Dict:
        """
        STEP 3: Build Trade Plan Based on Contract Price
        """
        try:
            entry_price = contract['ask']
            target_price = entry_price * (1 + self.profit_target_pct / 100)
            stop_price = entry_price * (1 - self.stop_loss_pct / 100)
            
            return {
                'entry_price': round(entry_price, 2),
                'target_price': round(target_price, 2),
                'stop_price': round(stop_price, 2),
                'profit_target_pct': self.profit_target_pct,
                'stop_loss_pct': self.stop_loss_pct,
                'risk_reward_ratio': round(self.profit_target_pct / self.stop_loss_pct, 2),
                'max_risk': round(entry_price * (self.stop_loss_pct / 100), 2),
                'max_profit': round(entry_price * (self.profit_target_pct / 100), 2)
            }
            
        except Exception as e:
            return {'error': f'Trade plan generation failed: {str(e)}'}
    
    def generate_recommendation(self, symbol: str) -> Dict:
        """
        STEP 4: Generate Complete Trading Recommendation
        """
        try:
            # Step 1: Analyze chart
            analysis = self.analyze_stock_chart(symbol)
            if 'error' in analysis:
                return analysis
            
            # Check if we should trade
            if analysis['recommendation'] == 'WAIT':
                return {
                    'symbol': symbol,
                    'recommendation': 'WAIT',
                    'reason': 'Market conditions not favorable for options trading',
                    'confidence': analysis['confidence'],
                    'explanation': analysis['explanation']
                }
            
            # Step 2: Get options chain
            option_type = analysis['recommendation'].lower()  # 'call' or 'put'
            options_data = self.get_options_chain_tradier(symbol, option_type)
            
            if 'error' in options_data or not options_data.get('contracts'):
                return {
                    'symbol': symbol,
                    'error': 'No suitable options contracts found'
                }
            
            # Select best contract
            best_contract = options_data['contracts'][0]
            
            # Step 3: Build trade plan
            trade_plan = self.build_trade_plan(best_contract, analysis)
            
            # Step 4: Format recommendation
            return {
                'symbol': symbol,
                'recommendation': analysis['recommendation'],
                'contract': best_contract,
                'trade_plan': trade_plan,
                'analysis': {
                    'trend': analysis['trend_direction'],
                    'confidence': analysis['confidence'],
                    'signals_aligned': analysis['signals_aligned'],
                    'explanation': analysis['explanation']
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Recommendation generation failed: {str(e)}'}

# Global instance
intelligent_agent = IntelligentOptionsAgent()

def get_intelligent_options_recommendation(symbol: str) -> Dict:
    """Get intelligent options trading recommendation"""
    return intelligent_agent.generate_recommendation(symbol)
