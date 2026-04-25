import time
from threading import Thread
from decimal import Decimal
from .api import NonKYCClient

class TraderController:
    """
    Контроллер, опрашивающий биржу и управляющий ордерами.
    """
    def __init__(self):
        self.client = NonKYCClient()
        self.subscribers = []
        self.running = False
        self.symbol = "BTC/USDT"
        self.timeframe = 5
        self.orders = []  # последние полученные открытые ордера

    def set_symbol(self, symbol: str):
        self.symbol = symbol.upper()

    def set_timeframe(self, tf: int):
        self.timeframe = tf

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def _emit(self, state: dict):
        for cb in self.subscribers:
            cb(state)

    def run(self):
        """Запустить цикл обновления данных (в отдельном потоке)."""
        self.running = True
        def loop():
            while self.running:
                try:
                    # Получаем стакан и свечи по символу
                    ob = self.client.get_orderbook(self.symbol)
                    candles = self.client.get_candles(self.symbol, resolution=self.timeframe, count_back=60)
                    # Обновляем список открытых ордеров
                    self.orders = self.client.get_orders(self.symbol)
                    # Формируем состояние для UI
                    state = {
                        "symbol": self.symbol,
                        "timeframe": self.timeframe,
                        "bids": ob.get("bids", []),
                        "asks": ob.get("asks", []),
                        "candles": candles.get("bars", []),
                        "orders": self.orders
                    }
                    self._emit(state)
                except Exception as e:
                    self._emit({"error": str(e)})
                time.sleep(2)
        Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False

    def place_order(self, side: str, qty: Decimal, price: Decimal = None) -> Any:
        """Разместить ордер (limit или market)."""
        otype = "limit" if price is not None else "market"
        return self.client.create_order(self.symbol, side, otype, qty, price)

    def cancel_order(self, order_id: str) -> Any:
        """Отменить ордер по ID."""
        return self.client.cancel_order(order_id)

    def refresh_orders(self):
        """Обновить локальный список ордеров."""
        self.orders = self.client.get_orders(self.symbol)
        return self.orders
