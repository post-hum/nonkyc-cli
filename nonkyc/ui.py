from textual.app import App
from textual.widgets import Static, Input
from textual.containers import Vertical
from rich.text import Text


def candle_ascii(candles, width=50, height=10):
    if not candles:
        return "no candles"

    candles = candles[-width:]

    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    mx, mn = max(highs), min(lows)
    rng = (mx - mn) or 1

    def level(y):
        return mn + (rng * y / height)

    out = []

    for i in range(height, -1, -1):
        lv = level(i)
        line = ""

        for c in candles:
            o = float(c["open"])
            h = float(c["high"])
            l = float(c["low"])
            cl = float(c["close"])

            if l <= lv <= h:
                line += "█" if cl >= o else "▒"
            else:
                line += " "

        out.append(line)

    return "\n".join(out)


class OrderBook(Static):
    def update_data(self, state):
        if "error" in state:
            self.update(state["error"])
            return

        bids = state.get("bids", [])[:5]
        asks = state.get("asks", [])[:5]
        candles = state.get("candles", [])
        symbol = state.get("symbol")
        tf = state.get("timeframe")

        text = f"SYMBOL: {symbol} | TF: {tf}m\n\n"

        text += "BIDS\n"
        for b in bids:
            text += f"{b['price']} | {b['quantity']}\n"

        text += "\nASKS\n"
        for a in asks:
            text += f"{a['price']} | {a['quantity']}\n"

        text += "\nCANDLES (ASCII)\n"
        text += candle_ascii(candles)

        self.update(text)


class NonKYCApp(App):
    CSS = "Screen { layout: vertical; }"

    def __init__(self, controller, symbol="BTC/USDT"):
        super().__init__()
        self.controller = controller
        self.symbol = symbol

    def compose(self):
        yield Input(placeholder="symbol (BTC/USDT)")
        yield Input(placeholder="timeframe (5,15,60...)")
        self.view = OrderBook()
        yield self.view

    def on_mount(self):
        self.controller.subscribe(self.update_ui)
        self.controller.set_symbol(self.symbol)
        self.controller.run()

    def update_ui(self, state):
        self.view.update_data(state)

    async def on_input_submitted(self, message: Input.Submitted):
        value = message.value.strip()

        if "/" in value:
            self.controller.set_symbol(value)
        elif value.isdigit():
            self.controller.set_timeframe(int(value))
