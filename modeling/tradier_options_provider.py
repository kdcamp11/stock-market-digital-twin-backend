"""
Tradier Options Data Provider - Real-time, accurate options data
Provides live options chains, pricing, Greeks, and contract selection
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

class TradierOptionsProvider:
    def __init__(self):
        self.api_token = os.getenv('TRADIER_TOKEN')
        self.base_url = 'https://api.tradier.com/v1'
        self.sandbox_url = 'https://sandbox.tradier.com/v1'  # For testing
        
        # Use sandbox for testing, production for live data
        self.use_sandbox = os.getenv('TRADIER_SANDBOX', 'true').lower() == 'true'
        self.api_url = self.sandbox_url if self.use_sandbox else self.base_url
        
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Accept': 'application/json'
        }
        
    def is_available(self) -> bool:
        """Check if Tradier API is available and configured"""
        return bool(self.api_token)
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price from Tradier"""
        try:
            url = f'{self.api_url}/markets/quotes'
            params = {'symbols': symbol}
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                quotes = data.get('quotes', {}).get('quote', {})
                if isinstance(quotes, list):
                    quotes = quotes[0] if quotes else {}
                
                return float(quotes.get('last', 0))
            
            return None
            
        except Exception as e:
            print(f"Error fetching current price for {symbol}: {e}")
            return None
    
    def get_options_expirations(self, symbol: str) -> List[str]:
        """Get available options expiration dates"""
        try:
            url = f'{self.api_url}/markets/options/expirations'
            params = {'symbol': symbol}
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                expirations = data.get('expirations', {}).get('date', [])
                
                # Return next 4 expirations
                return expirations[:4] if isinstance(expirations, list) else []
            
            return []
            
        except Exception as e:
            print(f"Error fetching expirations for {symbol}: {e}")
            return []
    
    def get_options_chain(self, symbol: str, expiration: str = None) -> Dict:
        """Get complete options chain for a symbol and expiration"""
        try:
            if not expiration:
                # Get next Friday expiration
                expirations = self.get_options_expirations(symbol)
                if not expirations:
                    return {'error': 'No expirations available'}
                expiration = expirations[0]
            
            url = f'{self.api_url}/markets/options/chains'
            params = {
                'symbol': symbol,
                'expiration': expiration,
                'greeks': 'true'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                options = data.get('options', {}).get('option', [])
                
                if not isinstance(options, list):
                    options = [options] if options else []
                
                # Separate calls and puts
                calls = [opt for opt in options if opt.get('option_type') == 'call']
                puts = [opt for opt in options if opt.get('option_type') == 'put']
                
                return {
                    'symbol': symbol,
                    'expiration': expiration,
                    'calls': calls,
                    'puts': puts,
                    'total_contracts': len(options),
                    'timestamp': datetime.now().isoformat()
                }
            
            return {'error': f'API error: {response.status_code}'}
            
        except Exception as e:
            return {'error': f'Failed to fetch options chain: {str(e)}'}
    
    def filter_contracts(self, options_chain: Dict, option_type: str = 'call', 
                        min_delta: float = 0.4, max_delta: float = 0.6,
                        min_volume: int = 100, max_ask: float = 5.0,
                        min_open_interest: int = 500) -> List[Dict]:
        """Filter options contracts based on criteria"""
        try:
            contracts = options_chain.get('calls' if option_type.lower() == 'call' else 'puts', [])
            
            filtered = []
            for contract in contracts:
                # Extract values with defaults
                delta = abs(float(contract.get('delta', 0)))
                volume = int(contract.get('volume', 0))
                ask = float(contract.get('ask', 999))
                open_interest = int(contract.get('open_interest', 0))
                bid = float(contract.get('bid', 0))
                
                # Apply filters
                if (min_delta <= delta <= max_delta and
                    volume >= min_volume and
                    ask <= max_ask and
                    ask > 0 and  # Valid ask price
                    open_interest >= min_open_interest and
                    bid > 0):  # Valid bid price
                    
                    filtered.append({
                        'symbol': contract.get('symbol'),
                        'strike': float(contract.get('strike')),
                        'expiration': contract.get('expiration_date'),
                        'ask': ask,
                        'bid': bid,
                        'delta': delta,
                        'gamma': float(contract.get('gamma', 0)),
                        'theta': float(contract.get('theta', 0)),
                        'vega': float(contract.get('vega', 0)),
                        'volume': volume,
                        'open_interest': open_interest,
                        'type': option_type.upper(),
                        'last_price': float(contract.get('last', 0)),
                        'change': float(contract.get('change', 0)),
                        'change_percentage': float(contract.get('change_percentage', 0))
                    })
            
            # Sort by volume (descending) and delta (closest to 0.5)
            filtered.sort(key=lambda x: (x['volume'], 1 - abs(x['delta'] - 0.5)), reverse=True)
            
            return filtered[:10]  # Return top 10 contracts
            
        except Exception as e:
            print(f"Error filtering contracts: {e}")
            return []
    
    def get_best_contract(self, symbol: str, option_type: str = 'call') -> Optional[Dict]:
        """Get the best options contract based on our criteria"""
        try:
            # Get options chain
            chain = self.get_options_chain(symbol)
            if 'error' in chain:
                return None
            
            # Filter contracts
            contracts = self.filter_contracts(chain, option_type)
            
            # Return best contract (highest volume, good delta)
            return contracts[0] if contracts else None
            
        except Exception as e:
            print(f"Error getting best contract: {e}")
            return None
    
    def get_options_analysis(self, symbol: str) -> Dict:
        """Get comprehensive options analysis with real data"""
        try:
            current_price = self.get_current_price(symbol)
            if not current_price:
                return {'error': 'Unable to fetch current price'}
            
            # Get options chain
            chain = self.get_options_chain(symbol)
            if 'error' in chain:
                return chain
            
            # Analyze put/call ratio
            calls = chain.get('calls', [])
            puts = chain.get('puts', [])
            
            total_call_volume = sum(int(c.get('volume', 0)) for c in calls)
            total_put_volume = sum(int(p.get('volume', 0)) for p in puts)
            
            put_call_ratio = total_put_volume / max(total_call_volume, 1)
            
            # Calculate implied volatility average
            all_options = calls + puts
            iv_values = [float(opt.get('implied_volatility', 0)) for opt in all_options 
                        if opt.get('implied_volatility')]
            avg_iv = sum(iv_values) / len(iv_values) if iv_values else 0
            
            # Find max pain (strike with highest total open interest)
            strike_oi = {}
            for opt in all_options:
                strike = float(opt.get('strike', 0))
                oi = int(opt.get('open_interest', 0))
                strike_oi[strike] = strike_oi.get(strike, 0) + oi
            
            max_pain = max(strike_oi.keys(), key=lambda k: strike_oi[k]) if strike_oi else current_price
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'expiration': chain.get('expiration'),
                'sentiment': {
                    'put_call_ratio': round(put_call_ratio, 2),
                    'implied_volatility': round(avg_iv * 100, 1),  # Convert to percentage
                    'max_pain': round(max_pain, 2),
                    'total_call_volume': total_call_volume,
                    'total_put_volume': total_put_volume
                },
                'chain_stats': {
                    'total_contracts': len(all_options),
                    'calls_count': len(calls),
                    'puts_count': len(puts)
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'tradier_live'
            }
            
        except Exception as e:
            return {'error': f'Options analysis failed: {str(e)}'}

# Global instance
tradier_provider = TradierOptionsProvider()

def get_tradier_options_provider():
    """Get the global Tradier options provider instance"""
    return tradier_provider if tradier_provider.is_available() else None
