from textual.app import App
from textual.widgets import Static, Input
from rich.text import Text


def candle_ascii(candles, width=60, height=25):
    """
    Render smooth ASCII candles using column-first approach:
    1. Build each candle column bottom→top with integer rows
    2. Transpose to row→column for display
    3. No floating-point gaps, clean body/wick transitions
    """
    if not candles:
        return Text("✗ no data", style="dim italic")

    candles = candles[-width:]
    
    # Extract price range
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    mx, mn = max(highs), min(lows)
    rng = (mx - mn) or 1
    
    def price_to_row(price: float) -> int:
        """Map price to integer row index (0 = bottom, height = top)"""
        return min(height, max(0, int((price - mn) / rng * height + 0.5)))

    # Pre-build each candle column as list of (char, style) from row 0 to height
    columns = []
    for c in candles:
        o, h, l, cl = float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"])
        bullish = cl >= o
        color = "bright_green" if bullish else "bright_red"
        wick_style = "green" if bullish else "red"
        
        body_top = price_to_row(max(o, cl))
        body_bot = price_to_row(min(o, cl))
        wick_top = price_to_row(h)
        wick_bot = price_to_row(l)
        
        col = []
        for row in range(height + 1):
            if row > wick_top or row < wick_bot:
                col.append((" ", None))  # empty space
            elif body_bot <= row <= body_top and body_top != body_bot:
                col.append(("█", color))  # body
            elif body_top == body_bot and row == body_top:
                col.append(("━", color))  # doji
            else:
                col.append(("│", wick_style))  # wick
        columns.append(col)
    
    # Transpose: build output row by row (top→bottom for display)
    result = Text()
    for row in range(height, -1, -1):
        # Price label on Y-axis (every 5 rows)
        price_val = mn + (rng * row / height)
        if row % 5 == 0:
            result.append(f"{price_val:9.1f} │ ", style="dim cyan")
        else:
            result.append(" " * 12)
        
        # Add each candle's character for this row
        for col in columns:
            char, style = col[row]
            if style:
                result.append(char, style=style)
            else:
                result.append(char)
        result.append("\n")
    
    # X-axis baseline
    result.append(" " * 12 + "└")
    for i in range(len(columns)):
        result.append("─" if i % 5 != 4 else "┼", style="dim")
    result.append("\n")
    
    return result


class OrderBook(Static):
    def update_data(self, state):
        if "error" in state:
            self.update(Text(f"⚠ {state['error']}", style="bold red"))
            return

        bids = state.get("bids", [])[:5]
        asks = state.get("asks", [])[:5]
        candles = state.get("candles", [])
        symbol = state.get("symbol", "N/A")
        tf = state.get("timeframe", 5)

        header = Text()
        header.append(f"SYMBOL: {symbol}", style="bold cyan")
        header.append(f"  |  TF: {tf}m\n\n", style="dim")

        header.append("▼ BIDS\n", style="bright_green")
        for b in bids:
            p, q = float(b.get("price", 0)), float(b.get("quantity", 0))
            header.append(f"{p:,.2f}", style="bright_green")
            header.append(f"  ×  {q:,.4f}\n", style="dim")

        header.append("\n▲ ASKS\n", style="bright_red")
        for a in asks:
            p, q = float(a.get("price", 0)), float(a.get("quantity", 0))
            header.append(f"{p:,.2f}", style="bright_red")
            header.append(f"  ×  {q:,.4f}\n", style="dim")

        header.append("\n📈 PRICE CHART\n", style="bold")
        header.append(candle_ascii(candles, width=60, height=25))
        self.update(header)


class NonKYCApp(App):
    CSS = """
    Screen { layout: vertical; background: $background; }
    Input { margin: 0 1; width: 100%; }
    #main_view { height: 1fr; }
    """

    def __init__(self, controller, symbol="BTC/USDT"):
        super().__init__()
        self.controller = controller
        self.symbol = symbol

    def compose(self):
        yield Input(placeholder="symbol → BTC/USDT", id="symbol_input")
        yield Input(placeholder="timeframe → 5, 15, 60", id="tf_input")
        self.view = OrderBook(id="main_view")
        yield self.view

    def on_mount(self):
        self.controller.subscribe(self.update_ui)
        self.controller.set_symbol(self.symbol)
        self.controller.run()
        self.query_one("#symbol_input").focus()

    def update_ui(self, state):
        self.view.update_data(state)

    async def on_input_submitted(self, message: Input.Submitted):
        val = message.value.strip()
        if message.input.id == "symbol_input" and "/" in val:
            self.controller.set_symbol(val.upper())
            self.query_one("#tf_input").focus()
        elif message.input.id == "tf_input" and val.isdigit():
            self.controller.set_timeframe(int(val))
            self.query_one("#symbol_input").focus()
