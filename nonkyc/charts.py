from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List
from .models import Ticker, Balance, Order, Candle

console = Console()

def display_ticker(ticker: Ticker):
    table = Table(title=f"{ticker.symbol}")
    table.add_column("Bid", justify="right")
    table.add_column("Ask", justify="right")
    table.add_column("Last", justify="right")
    table.add_column("24h %", justify="right")
    table.add_column("Volume", justify="right")

    change_symbol = "▲" if ticker.change_24h >= 0 else "▼"

    table.add_row(
        f"{ticker.bid:.6f}",
        f"{ticker.ask:.6f}",
        f"{ticker.last:.6f}",
        f"{change_symbol} {abs(ticker.change_24h):.2f}%",
        f"{ticker.volume_24h:.0f}"
    )

    console.print(table)


def display_balance(balances: List[Balance]):
    table = Table(title="Balance")
    table.add_column("Asset")
    table.add_column("Free", justify="right")
    table.add_column("Locked", justify="right")
    table.add_column("Total", justify="right")

    for b in balances:
        if b.total > 0:
            table.add_row(
                b.asset,
                f"{b.free:.4f}",
                f"{b.locked:.4f}",
                f"{b.total:.4f}"
            )

    console.print(table)


def display_orders(orders: List[Order]):
    if not orders:
        console.print("No open orders")
        return

    table = Table(title="Orders")
    table.add_column("ID")
    table.add_column("Symbol")
    table.add_column("Side")
    table.add_column("Price", justify="right")
    table.add_column("Amount", justify="right")

    for o in orders:
        table.add_row(
            o.id[:8],
            o.symbol,
            o.side,
            f"{o.price:.6f}",
            f"{o.amount:.4f}"
        )

    console.print(table)


def display_orderbook(bids: list, asks: list, limit: int = 10):
    table = Table(title="Order Book")
    table.add_column("Bid Price", justify="right")
    table.add_column("Bid Amount", justify="right")
    table.add_column("Ask Price", justify="right")
    table.add_column("Ask Amount", justify="right")

    for i in range(limit):
        bid = bids[i] if i < len(bids) else ("", "")
        ask = asks[i] if i < len(asks) else ("", "")

        table.add_row(
            f"{bid[0]:.6f}" if bid[0] else "",
            f"{bid[1]:.4f}" if bid[1] else "",
            f"{ask[0]:.6f}" if ask[0] else "",
            f"{ask[1]:.4f}" if ask[1] else ""
        )

    console.print(table)


def draw_ascii_chart(prices: List[float], width: int = 50, height: int = 10):
    if not prices:
        console.print("No data")
        return

    prices = prices[-width:]
    mn, mx = min(prices), max(prices)
    rng = mx - mn or 1

    lines = []
    for lvl in range(height, 0, -1):
        threshold = mn + rng * (lvl / height)
        line = "".join("█" if p >= threshold else " " for p in prices)
        lines.append(line)

    console.print(Panel("\n".join(lines), title="Price Chart"))
