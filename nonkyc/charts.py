from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from typing import List
from .models import Ticker, Balance, Order, Candle

console = Console()

def display_ticker(ticker: Ticker):
    table = Table(title=f"{ticker.symbol}")
    table.add_column("Bid", justify="right", style="bright_green")
    table.add_column("Ask", justify="right", style="bright_red")
    table.add_column("Last", justify="right", style="bold")
    table.add_column("24h %", justify="right")
    table.add_column("Volume", justify="right")

    change_style = "bright_green" if ticker.change_24h >= 0 else "bright_red"
    change_symbol = "▲" if ticker.change_24h >= 0 else "▼"

    table.add_row(
        f"{ticker.bid:.6f}",
        f"{ticker.ask:.6f}",
        f"{ticker.last:.6f}",
        f"[{change_style}]{change_symbol} {abs(ticker.change_24h):.2f}%[/{change_style}]",
        f"{ticker.volume_24h:.0f}"
    )
    console.print(table)


def display_balance(balances: List[Balance]):
    table = Table(title="Balance")
    table.add_column("Asset")
    table.add_column("Free", justify="right")
    table.add_column("Locked", justify="right")
    table.add_column("Total", justify="right", style="bold")

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
        console.print("No open orders", style="dim")
        return

    table = Table(title="Orders")
    table.add_column("ID")
    table.add_column("Symbol")
    table.add_column("Side")
    table.add_column("Price", justify="right")
    table.add_column("Amount", justify="right")

    for o in orders:
        side_style = "bright_green" if o.side.lower() == "buy" else "bright_red"
        table.add_row(
            o.id[:8],
            o.symbol,
            f"[{side_style}]{o.side}[/{side_style}]",
            f"{o.price:.6f}",
            f"{o.amount:.4f}"
        )
    console.print(table)


def display_orderbook(bids: list, asks: list, limit: int = 10):
    table = Table(title="Order Book")
    table.add_column("Bid Price", justify="right", style="bright_green")
    table.add_column("Bid Amount", justify="right")
    table.add_column("Ask Price", justify="right", style="bright_red")
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
    """CLI version with price labels and pump/dump colors"""
    if not prices:
        console.print("✗ No data", style="dim italic")
        return

    prices = prices[-width:]
    mn, mx = min(prices), max(prices)
    rng = mx - mn or 1

    def price_to_row(p): return min(height, max(0, int((p - mn) / rng * height)))

    lines = []
    for row in range(height, -1, -1):
        price_val = mn + (rng * row / height)
        line = Text()
        
        if row % 2 == 0:
            line.append(f"{price_val:8.2f} │ ", style="dim cyan")
        else:
            line.append(" " * 12)
        
        for i, p in enumerate(prices):
            if i > 0:
                prev = prices[i-1]
                is_up = p >= prev
                color = "bright_green" if is_up else "bright_red"
                ch = "█" if abs(p - prev) > rng * 0.02 else "▒"
                line.append(ch, style=color)
            else:
                line.append(" ")
        lines.append(line)

    result = Text()
    for i, ln in enumerate(lines):
        result.append(ln)
        if i < len(lines) - 1:
            result.append("\n")
    result.append("\n" + " " * 12 + "└" + "─" * len(prices), style="dim")
    
    console.print(Panel(result, title="Price Chart", border_style="dim"))
