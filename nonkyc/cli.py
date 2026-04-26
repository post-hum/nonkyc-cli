#!/usr/bin/env python3
import click
from rich.console import Console
from rich.table import Table

from .api import NonKYCClient

console = Console()

@click.group()
def cli():
    pass

@cli.command()
@click.argument('symbol')
def price(symbol):
    client = NonKYCClient()
    t = client.get_ticker(symbol)

    table = Table(title=symbol)
    table.add_column("Bid")
    table.add_column("Ask")
    table.add_column("Last")

    table.add_row(
        f"{t.bid:.6f}",
        f"{t.ask:.6f}",
        f"{t.last:.6f}",
    )

    console.print(table)

@cli.command()
def balance():
    client = NonKYCClient()
    balances = client.get_balance()

    table = Table(title="Balance")
    table.add_column("Asset")
    table.add_column("Total")

    for b in balances:
        if b.total > 0:
            table.add_row(b.asset, f"{b.total:.4f}")

    console.print(table)

@cli.command()
@click.argument('symbol')
@click.option('--limit', default=20)
def orderbook(symbol, limit):
    client = NonKYCClient()
    ob = client.get_orderbook(symbol, limit)

    table = Table(title="OrderBook")
    table.add_column("Bid")
    table.add_column("Ask")

    for i in range(limit):
        bid = ob["bids"][i] if i < len(ob["bids"]) else ("", "")
        ask = ob["asks"][i] if i < len(ob["asks"]) else ("", "")

        table.add_row(
            f"{bid[0]:.6f}" if bid[0] else "",
            f"{ask[0]:.6f}" if ask[0] else "",
        )

    console.print(table)

if __name__ == '__main__':
    cli()
