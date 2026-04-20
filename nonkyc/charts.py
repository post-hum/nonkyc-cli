from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from typing import List
from .models import Ticker, Balance, Order, Candle

console = Console()

def display_ticker(ticker: Ticker):
    """Display ticker information"""
    table = Table(title=f"📊 {ticker.symbol}", style="bold")
    table.add_column("Bid", justify="center")
    table.add_column("Ask", justify="center")
    table.add_column("Last", justify="center")
    table.add_column("24h Change", justify="center")
    table.add_column("24h Volume", justify="center")
    
    change_color = "green" if ticker.change_24h >= 0 else "red"
    change_symbol = "▲" if ticker.change_24h >= 0 else "▼"
    
    table.add_row(
        f"[cyan]${ticker.bid:.4f}[/cyan]",
        f"[cyan]${ticker.ask:.4f}[/cyan]",
        f"[bold yellow]${ticker.last:.4f}[/bold yellow]",
        f"[{change_color}]{change_symbol} {abs(ticker.change_24h):.2f}%[/{change_color}]",
        f"[dim]${ticker.volume_24h:,.0f}[/dim]"
    )
    console.print(table)

def display_balance(balances: List[Balance]):
    """Display account balance"""
    table = Table(title="💰 Account Balance", style="bold")
    table.add_column("Asset", justify="left")
    table.add_column("Free", justify="right")
    table.add_column("Locked", justify="right")
    table.add_column("Total", justify="right")
    
    total_usd = 0
    for balance in balances:
        if balance.total > 0:
            table.add_row(
                f"[bold]{balance.asset}[/bold]",
                f"[green]{balance.free:.4f}[/green]",
                f"[yellow]{balance.locked:.4f}[/yellow]",
                f"[cyan]{balance.total:.4f}[/cyan]"
            )
    
    console.print(table)

def display_orders(orders: List[Order]):
    """Display open orders"""
    if not orders:
        console.print("[dim]No open orders[/dim]")
        return
    
    table = Table(title="📋 Open Orders", style="bold")
    table.add_column("ID", justify="left")
    table.add_column("Symbol", justify="center")
    table.add_column("Side", justify="center")
    table.add_column("Price", justify="right")
    table.add_column("Amount", justify="right")
    table.add_column("Filled", justify="right")
    
    for order in orders:
        side_color = "green" if order.side == "buy" else "red"
        table.add_row(
            order.id[:8],
            order.symbol,
            f"[{side_color}]{order.side}[/{side_color}]",
            f"[cyan]${order.price:.4f}[/cyan]",
            f"{order.amount:.4f}",
            f"{order.filled:.2f}%"
        )
    
    console.print(table)

def display_orderbook(bids: list, asks: list, limit: int = 10):
    """Display order book"""
    layout = Layout()
    layout.split_row(
        Layout(name="asks"),
        Layout(name="bids")
    )
    
    asks_table = Table(title="📈 Asks", style="bold", show_header=True)
    asks_table.add_column("Price", justify="right")
    asks_table.add_column("Amount", justify="right")
    
    for price, amount in asks[:limit]:
        asks_table.add_row(f"[red]${price:.4f}[/red]", f"{amount:.4f}")
    
    bids_table = Table(title="📉 Bids", style="bold", show_header=True)
    bids_table.add_column("Price", justify="right")
    bids_table.add_column("Amount", justify="right")
    
    for price, amount in bids[:limit]:
        bids_table.add_row(f"[green]${price:.4f}[/green]", f"{amount:.4f}")
    
    layout["asks"].update(asks_table)
    layout["bids"].update(bids_table)
    console.print(layout)

def draw_ascii_chart(prices: List[float], width: int = 50, height: int = 10):
    """Draw simple ASCII chart"""
    if not prices:
        return
    
    min_price = min(prices)
    max_price = max(prices)
    price_range = max_price - min_price
    
    if price_range == 0:
        price_range = 1
    
    chart = []
    for i in range(height, 0, -1):
        level = min_price + (price_range * (i / height))
        line = ""
        for price in prices:
            if price >= level:
                line += "█"
            else:
                line += " "
        chart.append(f"{level:8.2f} │{line}")
    
    # Add x-axis
    chart.append(" " * 9 + "└" + "─" * width)
    
    console.print(Panel("\n".join(chart), title="📈 Price Chart", style="bold cyan"))
