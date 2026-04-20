#!/usr/bin/env python3
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .api import NonKYCClient
from .charts import display_ticker, display_balance, display_orders, display_orderbook, draw_ascii_chart

console = Console()

@click.group()
def cli():
    """NonKYC.io Trading CLI - Trade crypto from your terminal"""
    pass

@cli.command()
@click.argument('symbol')
def price(symbol):
    """Get current price for a symbol (e.g., BTC/USDT)"""
    client = NonKYCClient()
    ticker = client.get_ticker(symbol)
    display_ticker(ticker)

@cli.command()
def balance():
    """Show account balance"""
    client = NonKYCClient()
    balances = client.get_balance()
    display_balance(balances)

@cli.command()
@click.argument('symbol')
@click.argument('amount', type=float)
@click.option('--price', type=float, help='Limit price (for limit orders)')
def buy(symbol, amount, price):
    """Buy cryptocurrency"""
    client = NonKYCClient()
    order_type = 'limit' if price else 'market'
    order = client.create_order(symbol, 'buy', order_type, amount, price)
    
    console.print(f"[green]✓ Order created![/green]")
    console.print(f"  ID: {order.id}")
    console.print(f"  Type: {order_type}")
    if price:
        console.print(f"  Price: ${price:.4f}")
    console.print(f"  Amount: {amount}")

@cli.command()
@click.argument('symbol')
@click.argument('amount', type=float)
@click.option('--price', type=float, help='Limit price (for limit orders)')
def sell(symbol, amount, price):
    """Sell cryptocurrency"""
    client = NonKYCClient()
    order_type = 'limit' if price else 'market'
    order = client.create_order(symbol, 'sell', order_type, amount, price)
    
    console.print(f"[green]✓ Order created![/green]")
    console.print(f"  ID: {order.id}")
    console.print(f"  Type: {order_type}")
    if price:
        console.print(f"  Price: ${price:.4f}")
    console.print(f"  Amount: {amount}")

@cli.command()
@click.argument('symbol')
@click.option('--limit', default=20, help='Number of orders to show')
def orderbook(symbol, limit):
    """Show order book"""
    client = NonKYCClient()
    orderbook = client.get_orderbook(symbol, limit)
    display_orderbook(orderbook['bids'], orderbook['asks'], limit)

@cli.command()
@click.option('--symbol', help='Filter by symbol')
def orders(symbol):
    """Show open orders"""
    client = NonKYCClient()
    orders = client.get_orders(symbol)
    display_orders(orders)

@cli.command()
@click.argument('order_id')
def cancel(order_id):
    """Cancel an order"""
    client = NonKYCClient()
    success = client.cancel_order(order_id)
    if success:
        console.print(f"[green]✓ Order {order_id} cancelled[/green]")
    else:
        console.print(f"[red]✗ Failed to cancel order {order_id}[/red]")

@cli.command()
@click.argument('symbol')
@click.option('--interval', default='1h', help='Candle interval (1m, 5m, 1h, 4h, 1d)')
@click.option('--limit', default=50, help='Number of candles to show')
def chart(symbol, interval, limit):
    """Show price chart"""
    client = NonKYCClient()
    candles = client.get_candles(symbol, interval, limit)
    prices = [c.close for c in candles]
    draw_ascii_chart(prices, width=60, height=15)
    
    # Show latest info
    latest = candles[-1]
    console.print(f"\n[bold]{symbol}[/bold] - Last: [cyan]${latest.close:.4f}[/cyan] | High: [green]${latest.high:.4f}[/green] | Low: [red]${latest.low:.4f}[/red]")

if __name__ == '__main__':
    cli()
