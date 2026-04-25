from typing import List
from rich.text import Text
from rich.table import Table
from rich.panel import Panel

def candle_ascii(candles: List[dict], width=60, height=20) -> Text:
    """
    Рисует ASCII-Chart свечей (каждая свеча одним столбцом).
    """
    if not candles:
        return Text("No data", style="dim")
    candles = candles[-width:]
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    max_h, min_l = max(highs), min(lows)
    rng = max_h - min_l or 1
    def scale(p): return int((p - min_l) / rng * height)
    canvas = [[" " for _ in range(len(candles))] for _ in range(height+1)]
    for i, c in enumerate(candles):
        o, h, l, cl = float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"])
        top = height - scale(h)
        bottom = height - scale(l)
        body_top = height - scale(max(o, cl))
        body_bottom = height - scale(min(o, cl))
        # Рисуем тень
        for y in range(top, bottom+1):
            canvas[y][i] = "│"
        # Рисуем тело свечи
        if body_top == body_bottom:  # если тело 0 (doji)
            canvas[body_top][i] = "─"
        else:
            for y in range(body_top, body_bottom+1):
                canvas[y][i] = "█"
    text = Text()
    for row in canvas:
        text.append("".join(row) + "\n")
    return text

def display_balance(balances: List[Any]):
    """
    Форматированный вывод балансов (Rich Table).
    """
    table = Table(title="Balance")
    table.add_column("Asset", justify="left")
    table.add_column("Total", justify="right")
    table.add_column("Available", justify="right")
    for b in balances:
        asset = b.get("asset")
        total = str(b.get("available", 0))
        held = str(b.get("held", 0))
        table.add_row(asset, total, held)
    return table

def display_orders(orders: List[Any]):
    """
    Форматированный вывод открытых ордеров (Rich Table).
    """
    if not orders:
        return Text("No open orders", style="dim")
    table = Table(title="Open Orders")
    table.add_column("ID")
    table.add_column("Symbol")
    table.add_column("Side")
    table.add_column("Price", justify="right")
    table.add_column("Quantity", justify="right")
    for o in orders:
        table.add_row(
            o.get("id","")[:8],
            o.get("symbol",""),
            o.get("side",""),
            str(o.get("price","")),
            str(o.get("quantity",""))
        )
    return table
