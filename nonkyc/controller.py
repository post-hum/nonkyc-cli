import time
from threading import Thread
from nonkyc.api import NonKYCClient
from nonkyc.utils import normalize_symbol

class TraderController:
    def __init__(self):
        self.client = NonKYCClient()
        self.subscribers = []
        self.running = False

        self.symbol = "BTC/USDT"
        self.timeframe = 5

    def set_symbol(self, symbol: str):
        self.symbol = normalize_symbol(symbol)

    def set_timeframe(self, tf: int):
        self.timeframe = tf

    def subscribe(self, cb):
        self.subscribers.append(cb)

    def _emit(self, data):
        for cb in self.subscribers:
            cb(data)

    def run(self):
        self.running = True

        def loop():
            while self.running:
                try:
                    ob = self.client.get_orderbook(self.symbol)
                    candles = self.client.get_candles(
                        self.symbol,
                        resolution=self.timeframe,
                        count_back=60
                    )

                    self._emit({
                        "symbol": self.symbol,
                        "timeframe": self.timeframe,
                        "bids": ob.get("bids", []),
                        "asks": ob.get("asks", []),
                        "candles": candles.get("bars", [])
                    })
                except Exception as e:
                    self._emit({"error": str(e)})

                time.sleep(2)

        Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
