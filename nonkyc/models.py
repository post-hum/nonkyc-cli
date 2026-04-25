from dataclasses import dataclass, field
from typing import List, Optional
from decimal import Decimal

@dataclass(slots=True)
class Ticker:
    symbol: str
    bid: Decimal = Decimal(0)
    ask: Decimal = Decimal(0)
    last: Decimal = Decimal(0)
    volume_24h: Decimal = Decimal(0)
    change_24h: Decimal = Decimal(0)
    high_24h: Decimal = Decimal(0)
    low_24h: Decimal = Decimal(0)
    timestamp: Optional[str] = None

@dataclass(slots=True)
class Balance:
    asset: str
    free: Decimal = Decimal(0)
    locked: Decimal = Decimal(0)
    total: Decimal = Decimal(0)

@dataclass(slots=True)
class Order:
    id: str
    symbol: str
    side: str
    type: str
    price: Decimal = Decimal(0)
    amount: Decimal = Decimal(0)
    filled: Decimal = Decimal(0)
    status: str = "open"

@dataclass(slots=True)
class Candle:
    time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

@dataclass(slots=True)
class Trade:
    timestamp: int
    price: Decimal
    quantity: Decimal
    side: str = ""

@dataclass(slots=True)
class AppState:
    symbol: str = "BTC/USDT"
    ticker: Optional[Ticker] = None
    orderbook: dict = field(default_factory=lambda: {"bids": [], "asks": []})
    balances: List[Balance] = field(default_factory=list)
    orders: List[Order] = field(default_factory=list)
    candles: List[Candle] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    last_error: str = ""
    auth_error: str = ""
    status: str = "Starting..."
