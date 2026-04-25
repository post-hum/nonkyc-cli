from decimal import Decimal, InvalidOperation

def normalize_symbol(symbol: str) -> str:
    """Normalize symbol to API format (e.g. BTC/USDT -> BTC_USDT)."""
    return symbol.replace("/", "_").upper()

def to_decimal(x) -> Decimal:
    """Convert a value (str/float) to Decimal, default 0 on error."""
    try:
        return Decimal(str(x))
    except (InvalidOperation, TypeError):
        return Decimal(0)
