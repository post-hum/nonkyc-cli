import time
import hmac
import hashlib
import json

class NonKYCClient:
    def __init__(self, api_key=None, api_secret=None):
        self.session = requests.Session()
        self.timeout = 10
        self.api_key = api_key
        self.api_secret = api_secret

    def _sign(self, url: str, body: str = ""):
        nonce = str(int(time.time() * 1000))
        data = f"{self.api_key}{url}{body}{nonce}"
        signature = hmac.new(
            self.api_secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            "X-API-KEY": self.api_key,
            "X-API-NONCE": nonce,
            "X-API-SIGN": signature,
            "Content-Type": "application/json"
        }

    # --- ORDERS ---

    def create_order(self, symbol, side, order_type, quantity, price=None):
        url = f"{BASE_URL}/createorder"

        payload = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        if price:
            payload["price"] = str(price)

        body = json.dumps(payload, separators=(',', ':'))
        headers = self._sign(url, body)

        r = self.session.post(url, data=body, headers=headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def cancel_order(self, order_id):
        url = f"{BASE_URL}/cancelorder"
        payload = {"id": order_id}

        body = json.dumps(payload)
        headers = self._sign(url, body)

        r = self.session.post(url, data=body, headers=headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_orders(self, symbol=None):
        url = f"{BASE_URL}/account/orders"
        params = {}
        if symbol:
            params["symbol"] = symbol
        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
