from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class Ticker:
    symbol: str
    bid: float
    ask: float
    last: float
    volume_24h: float
    change_24h: float
    high_24h: float
    low_24h: float
    
@dataclass
class Balance:
    asset: str
    free: float
    locked: float
    total: float
    
@dataclass
class Order:
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    type: str  # 'limit' or 'market'
    price: float
    amount: float
    filled: float
    status: str
    created_at: str
    fee: float = 0.0
    
@dataclass
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
