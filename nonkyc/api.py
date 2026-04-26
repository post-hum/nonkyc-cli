import requests

BASE_URL = "https://api.nonkyc.io/api/v2"

class NonKYCClient:
    def __init__(self):
        self.session = requests.Session()
        self.timeout = 10

    def get_orderbook(self, symbol: str, limit: int = 20):
        url = f"{BASE_URL}/market/orderbook"
        r = self.session.get(url, params={"symbol": symbol, "limit": limit}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_candles(self, symbol: str, resolution=5, count_back=50):
        url = f"{BASE_URL}/market/candles"
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "countBack": count_back,
            "firstDataRequest": 1
        }
        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
