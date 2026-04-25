import os
import time
import hmac
import hashlib
from urllib.parse import urlparse, parse_qsl, urlencode
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from decimal import Decimal

# Базовый URL API NonKYC
BASE_URL = "https://api.nonkyc.io/api/v2"

class NonKYCClient:
    def __init__(self):
        load_dotenv()  # Загружаем .env (API_KEY, API_SECRET)
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("API_SECRET")
        if not self.api_key or not self.api_secret:
            raise ValueError("API_KEY and API_SECRET must be set in .env")
        
        # Настраиваем сессию с повторами для устойчивости
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.timeout = 10

    def _sign_headers(self, url: str, body: str = "") -> dict:
        """
        Собираем HMAC-SHA256 подпись для запроса в соответствии с документацией NonKYC.
        Подписание: concat(API_KEY, URL, body, nonce) -> HMAC_SHA256 -> signature.
        """
        nonce = str(int(time.time() * 1000))  # Генерируем уникальный nonce

        # Формируем URL с правильным символом _ вместо /
        parsed_url = urlparse(url)
        query_params = dict(parse_qsl(parsed_url.query))
        sorted_query = urlencode(sorted(query_params.items()))  # Сортируем параметры запроса

        # Формируем строку для подписи
        data = f"{self.api_key}{parsed_url.path}{sorted_query}{body}{nonce}"

        # Логирование для отладки
        print(f"Signing data: {data}")  # Логирование строки для подписи

        # Вычисляем подпись с использованием HMAC SHA256
        signature = hmac.new(self.api_secret.encode(), data.encode(), hashlib.sha256).hexdigest()

        # Логирование для отладки
        print(f"Signature: {signature}")
        
        return {
            "X-API-KEY": self.api_key,
            "X-API-NONCE": nonce,
            "X-API-SIGN": signature,
            "Content-Type": "application/json"
        }

    def get_orderbook(self, symbol: str, limit: int = 50) -> dict:
        """GET /market/orderbook (публичный)."""
        symbol = symbol.replace("/", "_").upper()  # Заменяем / на _
        url = f"{BASE_URL}/market/orderbook"
        params = {"symbol": symbol, "limit": limit}
        
        # Формируем запрос с параметрами
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()  # Проверяем на ошибки
        data = resp.json()

        # Приводим цены и кол-во к Decimal
        for side in ["bids", "asks"]:
            for item in data.get(side, []):
                item["price"] = Decimal(item["price"])
                item["quantity"] = Decimal(item["quantity"])

        return data

    def get_balance(self) -> list:
        """GET /balances (приватный)."""
        url = f"{BASE_URL}/balances"
        headers = self._sign_headers(url)
        resp = self.session.get(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        balances = resp.json()
        # Приводим к Decimal (str) для безопасного вывода
        for b in balances:
            for field in ("available", "pending", "held"):
                b[field] = Decimal(b.get(field, "0") or "0")
        return balances

    def get_orders(self, symbol: str = None) -> list:
        """GET /account/orders (приватный). Можно фильтровать по symbol."""
        url = f"{BASE_URL}/account/orders"
        params = {}
        if symbol:
            params["symbol"] = symbol
        headers = self._sign_headers(url + ("?" + "&".join(f"{k}={v}" for k,v in params.items()) if params else ""), "")
        resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        orders = resp.json()
        # Decimal-парсинг
        for o in orders:
            o["price"] = Decimal(o.get("price", "0") or "0")
            o["quantity"] = Decimal(o.get("quantity", "0") or "0")
            o["executedQuantity"] = Decimal(o.get("executedQuantity", "0") or "0")
        return orders

    def create_order(self, symbol: str, side: str, otype: str, quantity: Decimal, price: Decimal = None) -> dict:
        """POST /createorder (приватный). Тип: 'limit' или 'market'."""
        url = f"{BASE_URL}/createorder"
        payload = {
            "symbol": symbol,
            "side": side.lower(),
            "type": otype,
            "quantity": str(quantity)
        }
        if price is not None:
            payload["price"] = str(price)
        body = json.dumps(payload, separators=(',', ':'))
        headers = self._sign_headers(url, body)
        resp = self.session.post(url, data=body, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        result = resp.json()
        return result

    def cancel_order(self, order_id: str) -> dict:
        """POST /cancelorder (приватный)."""
        url = f"{BASE_URL}/cancelorder"
        payload = {"id": order_id}
        body = json.dumps(payload)
        headers = self._sign_headers(url, body)
        resp = self.session.post(url, data=body, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_candles(self, symbol: str, resolution: int = 5, count_back: int = 50) -> dict:
        """GET /market/candles (публичный)."""
        symbol = symbol.replace("/", "_").upper()  # Заменяем / на _
        url = f"{BASE_URL}/market/candles"
        params = {"symbol": symbol, "resolution": resolution, "countBack": count_back, "firstDataRequest": 1}
        
        # Формируем запрос с параметрами
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()  # Проверяем на ошибки
        data = resp.json()

        # Приводим данные о свечах к Decimal
        for bar in data.get("bars", []):
            for k in ("open", "high", "low", "close", "volume"):
                bar[k] = Decimal(str(bar[k]))

        return data
