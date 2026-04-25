import os
import time
import json
import hmac
import hashlib
import requests

from nonkyc.utils import symbol_to_api

BASE_URL = "https://api.nonkyc.io/api/v2"


class NonKYCClient:
    def __init__(self, api_key=None, api_secret=None):
        self.session = requests.Session()
        self.timeout = 10

        self.api_key = api_key or os.getenv("NONKYC_API_KEY")
        self.api_secret = api_secret or os.getenv("NONKYC_API_SECRET")

    # -------------------------
    # AUTH CORE
    # -------------------------
    def _sign(self, url: str, body: str = ""):
        if not self.api_key or not self.api_secret:
            raise ValueError("Missing API credentials")

        nonce = str(int(time.time() * 1000))

        payload = f"{self.api_key}{url}{body}{nonce}"
        signature = hmac.new(
            self.api_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "X-API-KEY": self.api_key,
            "X-API-NONCE": nonce,
            "X-API-SIGN": signature,
            "Content-Type": "application/json"
        }

        return headers

    def _get(self, path, params=None):
        url = f"{BASE_URL}{path}"
        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, path, body=None, signed=False):
        url = f"{BASE_URL}{path}"
        body_json = json.dumps(body or {}, separators=(',', ':'))

        headers = {}

        if signed:
            headers = self._sign(url, body_json)

        r = self.session.post(url, data=body_json, headers=headers, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # -------------------------
    # PUBLIC
    # -------------------------
    def get_ticker(self, symbol: str):
        return self._get("/ticker/" + symbol_to_api(symbol))

    def get_orderbook(self, symbol: str, limit=20):
        return self._get("/market/orderbook", {
            "symbol": symbol,
            "limit": limit
        })

    def get_candles(self, symbol: str, resolution=5, count_back=50):
        return self._get("/market/candles", {
            "symbol": symbol,
            "resolution": resolution,
            "countBack": count_back,
            "firstDataRequest": 1
        })

    # -------------------------
    # PRIVATE (AUTH REQUIRED)
    # -------------------------
    def get_orders(self, symbol=None, status=None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        if status:
            params["status"] = status

        return self._get("/account/orders", params)

    def get_balances(self):
        return self._get("/balances")

    def create_order(self, symbol, side, order_type, quantity, price=None):
        body = {
            "symbol": symbol_to_api(symbol),
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }
        if price:
            body["price"] = str(price)

        return self._post("/createorder", body, signed=True)

    def cancel_order(self, order_id: str):
        return self._post("/cancelorder", {"id": order_id}, signed=True)

    def cancel_all(self, symbol: str):
        return self._post("/cancelallorders", {
            "symbol": symbol_to_api(symbol)
        }, signed=True)
