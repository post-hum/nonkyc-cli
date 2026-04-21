from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(slots=True)
class Ticker:
    symbol: str
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    volume_24h: float = 0.0
    change_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    timestamp: Optional[str] = None

    @property
    def spread(self) -> float:
        return max(self.ask - self.bid, 0.0)

    @property
    def mid(self) -> float:
        if self.bid and self.ask:
            return (self.bid + self.ask) / 2
        return self.last or self.bid or self.ask or 0.0


@dataclass(slots=True)
class Balance:
    asset: str
    free: float = 0.0
    locked: float = 0.0
    total: float = 0.0


@dataclass(slots=True)
class Order:
    id: str
    symbol: str
    side: str
    type: str
    price: float = 0.0
    amount: float = 0.0
    filled: float = 0.0
    status: str = "open"
    created_at: str = ""
    fee: float = 0.0

    @property
    def fill_pct(self) -> float:
        if self.amount <= 0:
            return 0.0
        return max(0.0, min(100.0, (self.filled / self.amount) * 100))


@dataclass(slots=True)
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class Trade:
    timestamp: str
    price: float
    amount: float
    side: str = ""


@dataclass(slots=True)
class AppState:
    symbol: str = "BTC/USDT"
    ticker: Optional[Ticker] = None
    orderbook: Dict[str, List[Tuple[float, float]]] = field(default_factory=lambda: {"bids": [], "asks": []})
    balances: List[Balance] = field(default_factory=list)
    orders: List[Order] = field(default_factory=list)
    candles: List[Candle] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    last_error: str = ""
    auth_error: str = ""
    status: str = "Starting..."
