"""
Options Data Integration for Stock Market Digital Twin
Fetches options chains, calculates Greeks, and provides options analysis
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from scipy.stats import norm
import math

class OptionsDataProvider:
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.environ.get('ALPACA_API_KEY')
        self.api_secret = api_secret or os.environ.get('ALPACA_API_SECRET')
        
        # Try to initialize Alpaca options client
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.trading.client import TradingClient
            self.alpaca_client = StockHistoricalDataClient(self.api_key, self.api_secret)
            self.trading_client = TradingClient(self.api_key, self.api_secret, paper=True)
        except Exception as e:
            print(f"Alpaca options client not available: {e}")
            self.alpaca_client = None
            self.trading_client = None
    
    def get_options_chain(self, symbol: str, expiration_date: str = None) -> Dict:
        """
        Get options chain for a symbol
        
        Args:
            symbol: Stock symbol
            expiration_date: Expiration date in YYYY-MM-DD format (optional)
        
        Returns:
            Dict containing calls and puts data
        """
        try:
            # For now, we'll use a mock implementation since Alpaca's options API
            # may have limitations. In production, you'd integrate with a proper options provider
            return self._get_mock_options_chain(symbol, expiration_date)
        except Exception as e:
            print(f"Error fetching options chain for {symbol}: {e}")
            return {}
    
    def _get_mock_options_chain(self, symbol: str, expiration_date: str = None) -> Dict:
        """
        Generate mock options chain data for demonstration
        In production, replace with actual options data provider
        """
        # Get current stock price (you'd fetch this from your data provider)
        current_price = 150.0  # Mock price
        
        if expiration_date is None:
            # Default to next Friday
            today = datetime.now()
            days_ahead = 4 - today.weekday()  # Friday is 4
            if days_ahead <= 0:
                days_ahead += 7
            expiration_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        # Generate strike prices around current price
        strikes = []
        for i in range(-10, 11):
            strike = round(current_price + (i * 5), 2)
            strikes.append(strike)
        
        calls = []
        puts = []
        
        for strike in strikes:
            # Mock options data
            time_to_expiry = (datetime.strptime(expiration_date, '%Y-%m-%d') - datetime.now()).days / 365.0
            
            # Calculate theoretical option prices using Black-Scholes
            call_price, put_price = self._black_scholes(current_price, strike, time_to_expiry, 0.02, 0.25)
            
            # Calculate Greeks
            greeks = self._calculate_greeks(current_price, strike, time_to_expiry, 0.02, 0.25)
            
            calls.append({
                'strike': strike,
                'expiration': expiration_date,
                'bid': round(call_price * 0.95, 2),
                'ask': round(call_price * 1.05, 2),
                'last': round(call_price, 2),
                'volume': np.random.randint(0, 1000),
                'open_interest': np.random.randint(0, 5000),
                'implied_volatility': 0.25,
                'delta': greeks['call_delta'],
                'gamma': greeks['gamma'],
                'theta': greeks['theta'],
                'vega': greeks['vega'],
                'rho': greeks['call_rho']
            })
            
            puts.append({
                'strike': strike,
                'expiration': expiration_date,
                'bid': round(put_price * 0.95, 2),
                'ask': round(put_price * 1.05, 2),
                'last': round(put_price, 2),
                'volume': np.random.randint(0, 1000),
                'open_interest': np.random.randint(0, 5000),
                'implied_volatility': 0.25,
                'delta': greeks['put_delta'],
                'gamma': greeks['gamma'],
                'theta': greeks['theta'],
                'vega': greeks['vega'],
                'rho': greeks['put_rho']
            })
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'expiration_date': expiration_date,
            'calls': calls,
            'puts': puts,
            'timestamp': datetime.now().isoformat()
        }
    
    def _black_scholes(self, S: float, K: float, T: float, r: float, sigma: float) -> tuple:
        """
        Calculate Black-Scholes option prices
        
        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (in years)
            r: Risk-free rate
            sigma: Volatility
        
        Returns:
            Tuple of (call_price, put_price)
        """
        if T <= 0:
            # Option has expired
            call_price = max(S - K, 0)
            put_price = max(K - S, 0)
            return call_price, put_price
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
        return call_price, put_price
    
    def _calculate_greeks(self, S: float, K: float, T: float, r: float, sigma: float) -> Dict:
        """
        Calculate option Greeks
        
        Returns:
            Dict containing delta, gamma, theta, vega, rho for calls and puts
        """
        if T <= 0:
            return {
                'call_delta': 1.0 if S > K else 0.0,
                'put_delta': -1.0 if S < K else 0.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0,
                'call_rho': 0.0,
                'put_rho': 0.0
            }
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Delta
        call_delta = norm.cdf(d1)
        put_delta = call_delta - 1
        
        # Gamma
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Theta
        call_theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                     - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        put_theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                    + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
        
        # Vega
        vega = S * norm.pdf(d1) * np.sqrt(T) / 100
        
        # Rho
        call_rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        put_rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        
        return {
            'call_delta': round(call_delta, 4),
            'put_delta': round(put_delta, 4),
            'gamma': round(gamma, 4),
            'theta': round(call_theta, 4),  # Using call theta as default
            'vega': round(vega, 4),
            'call_rho': round(call_rho, 4),
            'put_rho': round(put_rho, 4)
        }
    
    def get_options_analysis(self, symbol: str) -> Dict:
        """
        Get comprehensive options analysis for a symbol
        
        Returns:
            Dict containing options metrics and insights
        """
        chain = self.get_options_chain(symbol)
        if not chain:
            return {}
        
        calls = pd.DataFrame(chain['calls'])
        puts = pd.DataFrame(chain['puts'])
        current_price = chain['current_price']
        
        # Calculate key metrics
        analysis = {
            'symbol': symbol,
            'current_price': current_price,
            'expiration_date': chain['expiration_date'],
            'total_call_volume': calls['volume'].sum(),
            'total_put_volume': puts['volume'].sum(),
            'put_call_ratio': puts['volume'].sum() / max(calls['volume'].sum(), 1),
            'max_pain': self._calculate_max_pain(calls, puts),
            'implied_volatility_avg': (calls['implied_volatility'].mean() + puts['implied_volatility'].mean()) / 2,
            'most_active_call_strike': calls.loc[calls['volume'].idxmax(), 'strike'] if not calls.empty else None,
            'most_active_put_strike': puts.loc[puts['volume'].idxmax(), 'strike'] if not puts.empty else None,
            'atm_call': self._find_atm_option(calls, current_price),
            'atm_put': self._find_atm_option(puts, current_price),
            'support_levels': self._find_support_resistance(puts, 'support'),
            'resistance_levels': self._find_support_resistance(calls, 'resistance'),
            'gamma_exposure': self._calculate_gamma_exposure(calls, puts, current_price),
            'options_sentiment': self._analyze_options_sentiment(calls, puts)
        }
        
        return analysis
    
    def _calculate_max_pain(self, calls: pd.DataFrame, puts: pd.DataFrame) -> float:
        """Calculate max pain price (price where most options expire worthless)"""
        if calls.empty or puts.empty:
            return 0.0
        
        strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
        max_pain_values = []
        
        for strike in strikes:
            call_pain = calls[calls['strike'] > strike]['open_interest'].sum() * (calls[calls['strike'] > strike]['strike'] - strike).sum()
            put_pain = puts[puts['strike'] < strike]['open_interest'].sum() * (strike - puts[puts['strike'] < strike]['strike']).sum()
            total_pain = call_pain + put_pain
            max_pain_values.append((strike, total_pain))
        
        if max_pain_values:
            return min(max_pain_values, key=lambda x: x[1])[0]
        return 0.0
    
    def _find_atm_option(self, options: pd.DataFrame, current_price: float) -> Dict:
        """Find at-the-money option"""
        if options.empty:
            return {}
        
        closest_idx = (options['strike'] - current_price).abs().idxmin()
        return options.loc[closest_idx].to_dict()
    
    def _find_support_resistance(self, options: pd.DataFrame, level_type: str) -> List[float]:
        """Find support/resistance levels based on options open interest"""
        if options.empty:
            return []
        
        # Find strikes with high open interest
        high_oi = options[options['open_interest'] > options['open_interest'].quantile(0.8)]
        levels = high_oi.nlargest(3, 'open_interest')['strike'].tolist()
        
        return sorted(levels)
    
    def _calculate_gamma_exposure(self, calls: pd.DataFrame, puts: pd.DataFrame, current_price: float) -> float:
        """Calculate total gamma exposure"""
        if calls.empty or puts.empty:
            return 0.0
        
        call_gamma_exposure = (calls['gamma'] * calls['open_interest'] * 100 * current_price * current_price * 0.01).sum()
        put_gamma_exposure = (puts['gamma'] * puts['open_interest'] * 100 * current_price * current_price * 0.01 * -1).sum()
        
        return call_gamma_exposure + put_gamma_exposure
    
    def _analyze_options_sentiment(self, calls: pd.DataFrame, puts: pd.DataFrame) -> str:
        """Analyze overall options sentiment"""
        if calls.empty or puts.empty:
            return "NEUTRAL"
        
        call_volume = calls['volume'].sum()
        put_volume = puts['volume'].sum()
        put_call_ratio = put_volume / max(call_volume, 1)
        
        call_oi = calls['open_interest'].sum()
        put_oi = puts['open_interest'].sum()
        
        # Sentiment based on volume and open interest
        if put_call_ratio > 1.2 and put_oi > call_oi:
            return "BEARISH"
        elif put_call_ratio < 0.8 and call_oi > put_oi:
            return "BULLISH"
        else:
            return "NEUTRAL"
    
    def get_options_strategies(self, symbol: str, outlook: str = "BULLISH") -> List[Dict]:
        """
        Suggest options strategies based on market outlook
        
        Args:
            symbol: Stock symbol
            outlook: Market outlook ("BULLISH", "BEARISH", "NEUTRAL")
        
        Returns:
            List of suggested options strategies
        """
        chain = self.get_options_chain(symbol)
        if not chain:
            return []
        
        strategies = []
        current_price = chain['current_price']
        calls = pd.DataFrame(chain['calls'])
        puts = pd.DataFrame(chain['puts'])
        
        if outlook == "BULLISH":
            strategies.extend([
                {
                    'name': 'Long Call',
                    'description': 'Buy call option for unlimited upside potential',
                    'max_profit': 'Unlimited',
                    'max_loss': 'Premium paid',
                    'breakeven': 'Strike + Premium',
                    'complexity': 'Beginner'
                },
                {
                    'name': 'Bull Call Spread',
                    'description': 'Buy lower strike call, sell higher strike call',
                    'max_profit': 'Limited',
                    'max_loss': 'Net premium paid',
                    'breakeven': 'Lower strike + Net premium',
                    'complexity': 'Intermediate'
                }
            ])
        
        elif outlook == "BEARISH":
            strategies.extend([
                {
                    'name': 'Long Put',
                    'description': 'Buy put option for downside protection',
                    'max_profit': 'Strike - Premium',
                    'max_loss': 'Premium paid',
                    'breakeven': 'Strike - Premium',
                    'complexity': 'Beginner'
                },
                {
                    'name': 'Bear Put Spread',
                    'description': 'Buy higher strike put, sell lower strike put',
                    'max_profit': 'Limited',
                    'max_loss': 'Net premium paid',
                    'breakeven': 'Higher strike - Net premium',
                    'complexity': 'Intermediate'
                }
            ])
        
        else:  # NEUTRAL
            strategies.extend([
                {
                    'name': 'Iron Condor',
                    'description': 'Sell call spread and put spread',
                    'max_profit': 'Net premium received',
                    'max_loss': 'Strike width - Net premium',
                    'breakeven': 'Two breakeven points',
                    'complexity': 'Advanced'
                },
                {
                    'name': 'Straddle',
                    'description': 'Buy call and put at same strike',
                    'max_profit': 'Unlimited',
                    'max_loss': 'Total premium paid',
                    'breakeven': 'Strike ± Total premium',
                    'complexity': 'Intermediate'
                }
            ])
        
        return strategies

# Convenience function
def get_options_provider():
    """Get an instance of OptionsDataProvider"""
    try:
        return OptionsDataProvider()
    except Exception as e:
        print(f"Could not initialize options data provider: {e}")
        return None
