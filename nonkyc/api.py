import requests
import hmac
import hashlib
import time
import json
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode

from .models import Ticker, Balance, Order, Candle
from .utils import load_config

class NonKYCClient:
    def __init__(self, api_key=None, api_secret=None, base_url=None):
        config = load_config()
        self.api_key = api_key or config['api_key']
        self.api_secret = api_secret or config['api_secret']
        self.base_url = base_url or config['base_url']
        self.base_url = self.base_url.rstrip('/') + '/api/v2'
        self.session = requests.Session()
        
    def _generate_signature(self, url: str, nonce: str, body: str = None) -> str:
        """Generate HMAC-SHA256 signature for request"""
        if not self.api_secret:
            return ""
        
        if body:
            data_to_sign = f"{self.api_key}{url}{body}{nonce}"
        else:
            data_to_sign = f"{self.api_key}{url}{nonce}"
            
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            data_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, params: Dict = None, 
                 data: Dict = None, signed: bool = False) -> Any:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if signed and self.api_key and self.api_secret:
            nonce = str(int(time.time() * 1000))
            body = json.dumps(data, separators=(',', ':')) if data else None
            signature = self._generate_signature(url, nonce, body)
            
            headers.update({
                'X-API-KEY': self.api_key,
                'X-API-NONCE': nonce,
                'X-API-SIGN': signature
            })
        
        # For GET requests, params go in URL
        if method == 'GET' and params:
            url = f"{url}?{urlencode(params)}"
        
        response = self.session.request(method, url, json=data, headers=headers)
        
        try:
            return response.json()
        except:
            return response.text
    
    # Public endpoints (no auth required)
    def get_ticker(self, symbol: str) -> Ticker:
        """Get current ticker for a symbol"""
        # Try different endpoint formats
        try:
            # Try /ticker/{symbol}
            data = self._request('GET', f'/ticker/{symbol}')
        except:
            # Fallback to /tickers and filter
            data = self._request('GET', '/tickers')
            for item in data:
                if item.get('symbol') == symbol:
                    data = item
                    break
        
        return Ticker(
            symbol=symbol,
            bid=float(data.get('bid', 0)),
            ask=float(data.get('ask', 0)),
            last=float(data.get('last', 0)),
            volume_24h=float(data.get('volume', 0)),
            change_24h=float(data.get('change', 0)),
            high_24h=float(data.get('high', 0)),
            low_24h=float(data.get('low', 0))
        )
    
    def get_orderbook(self, symbol: str, limit: int = 20) -> dict:
        """Get order book for a symbol"""
        data = self._request('GET', '/orderbook', {'symbol': symbol, 'limit': limit})
        return {
            'bids': [(float(b[0]), float(b[1])) for b in data.get('bids', [])],
            'asks': [(float(a[0]), float(a[1])) for a in data.get('asks', [])]
        }
    
    def get_candles(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Candle]:
        """Get OHLCV candles"""
        data = self._request('GET', '/market/candles', {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        })
        
        candles = []
        for item in data:
            candles.append(Candle(
                timestamp=item['timestamp'],
                open=float(item['open']),
                high=float(item['high']),
                low=float(item['low']),
                close=float(item['close']),
                volume=float(item['volume'])
            ))
        return candles
    
    def get_markets(self) -> List[Dict]:
        """Get all available markets"""
        return self._request('GET', '/market/getlist')
    
    # Private endpoints (require authentication)
    def get_balance(self) -> List[Balance]:
        """Get account balance"""
        data = self._request('GET', '/balances', signed=True)
        balances = []
        for item in data:
            balances.append(Balance(
                asset=item['asset'],
                free=float(item['free']),
                locked=float(item['locked']),
                total=float(item['total'])
            ))
        return balances
    
    def create_order(self, symbol: str, side: str, order_type: str, 
                     amount: float, price: float = None) -> Order:
        """Create new order"""
        order_data = {
            'symbol': symbol,
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': str(amount)
        }
        if price:
            order_data['price'] = str(price)
        
        data = self._request('POST', '/createorder', data=order_data, signed=True)
        return Order(
            id=str(data['id']),
            symbol=symbol,
            side=side,
            type=order_type,
            price=float(data.get('price', price or 0)),
            amount=amount,
            filled=float(data.get('executed_quantity', 0)),
            status=data.get('status', 'open'),
            created_at=data.get('created_at', '')
        )
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel existing order"""
        result = self._request('POST', '/cancelorder', data={'id': order_id}, signed=True)
        return result.get('success', False)
    
    def get_orders(self, symbol: str = None, status: str = 'open') -> List[Order]:
        """Get list of orders"""
        params = {'status': status}
        if symbol:
            params['symbol'] = symbol
            
        data = self._request('GET', '/account/orders', params, signed=True)
        orders = []
        for item in data:
            orders.append(Order(
                id=str(item['id']),
                symbol=item['symbol'],
                side=item['side'].lower(),
                type=item['type'].lower(),
                price=float(item['price']),
                amount=float(item['quantity']),
                filled=float(item.get('executed_quantity', 0)),
                status=item['status'],
                created_at=item['created_at']
            ))
        return orders
    
    def get_deposit_address(self, ticker: str) -> str:
        """Get deposit address for asset"""
        data = self._request('GET', f'/getdepositaddress/{ticker}', signed=True)
        return data.get('address', '')
    
    def get_server_time(self) -> int:
        """Get server time"""
        data = self._request('GET', '/time')
        return data.get('serverTime', 0)
