def normalize_symbol(symbol: str) -> str:
    """
    API NonKYC принимает оба формата, но лучше унифицировать.
    """
    return symbol.replace("-", "/").replace("_", "/").upper()


def symbol_to_api(symbol: str) -> str:
    """
    Иногда API хочет BTC_USDT
    """
    return symbol.replace("/", "_").upper()
