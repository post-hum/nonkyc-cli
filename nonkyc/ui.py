from textual.app import App, ComposeResult
from textual.widgets import Static, Input, Label
from textual.containers import Container
from textual.binding import Binding
from rich.text import Text

def candle_ascii(candles, width=60, height=25):
    if not candles:
        return Text("no data", style="dim")

    candles = candles[-width:]
        
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    mx, mn = max(highs), min(lows)
    rng = (mx - mn) or 1
        
    def price_to_row(price: float) -> int:
        return min(height, max(0, int((price - mn) / rng * height + 0.5)))

    columns = []
    for c in candles:
        o, h, l, cl = float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"])
        bullish = cl >= o
        color = "green" if bullish else "red"
        wick_style = "bright_green" if bullish else "bright_red"
                
        body_top = price_to_row(max(o, cl))
        body_bot = price_to_row(min(o, cl))
        wick_top = price_to_row(h)
        wick_bot = price_to_row(l)
                
        col = []
        for row in range(height + 1):
            if row > wick_top or row < wick_bot:
                col.append((" ", None))
            elif body_bot <= row <= body_top and body_top != body_bot:
                col.append(("#", color))
            elif body_top == body_bot and row == body_top:
                col.append(("-", color))
            else:
                col.append(("|", wick_style))
        columns.append(col)

    result = Text()
    for row in range(height, -1, -1):
        price_val = mn + (rng * row / height)
        if row % 5 == 0:
            result.append(f"{price_val:9.1f} | ", style="dim")
        else:
            result.append(" " * 12)
            
        for col in columns:
            char, style = col[row]
            if style:
                result.append(char, style=style)
            else:
                result.append(char)
        result.append("\n")

    result.append(" " * 12 + "+")
    for i in range(len(columns)):
        result.append("-" if i % 5 != 4 else "+", style="dim")
    result.append("\n")
        
    return result

class OrderBook(Static):
    def update_data(self, state):
        if "error" in state:
            self.update(Text(f"Error: {state['error']}", style="bold red"))
            return

        bids = state.get("bids", [])[:5]
        asks = state.get("asks", [])[:5]
        candles = state.get("candles", [])
        symbol = state.get("symbol", "N/A")
        tf = state.get("timeframe", 5)

        header = Text()
        header.append(f"Symbol: {symbol}  |  Timeframe: {tf}m", style="bold")
        header.append("\n\n")

        header.append("BIDS\n", style="underline")
        for b in bids:
            p, q = float(b.get("price", 0)), float(b.get("quantity", 0))
            header.append(f"{p:,.2f}", style="green")
            header.append(f"  x  {q:,.4f}\n", style="dim")

        header.append("\nASKS\n", style="underline")
        for a in asks:
            p, q = float(a.get("price", 0)), float(a.get("quantity", 0))
            header.append(f"{p:,.2f}", style="red")
            header.append(f"  x  {q:,.4f}\n", style="dim")

        header.append("\nCHART\n", style="underline")
        header.append(candle_ascii(candles, width=60, height=25))
        self.update(header)

class CommandBar(Container):
    DEFAULT_CSS = """
    CommandBar {
        dock: bottom;
        height: 3;
        background: $surface;
        border-top: solid $secondary;
        padding: 0 1;
        layout: vertical;
        align: left middle;
    }
    #cmd_status {
        height: 1;
        color: $text-muted;
    }
    #cmd_input {
        height: 1;
        width: 1fr;
        background: $surface;
        color: $text;
        border: none;
        padding: 0;
        visibility: hidden;
    }
    """
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active = False
            
    def compose(self) -> ComposeResult:
        yield Label("", id="cmd_status")
        yield Input(placeholder="type command", id="cmd_input")
            
    def on_mount(self):
        self.update_prompt()
            
    def update_prompt(self):
        if not hasattr(self.app, 'controller'):
            return
        status = "READY" if self.app.controller.running else "STOPPED"
        sym = self.app.controller.symbol
        self.query_one("#cmd_status").update(f"[{status}] {sym} | Press ':' for command, '?' for help")
            
    def activate(self):
        self.active = True
        self.query_one("#cmd_status").styles.visibility = "hidden"
        inp = self.query_one("#cmd_input")
        inp.styles.visibility = "visible"
        inp.value = ""
        inp.focus()
            
    def deactivate(self):
        self.active = False
        inp = self.query_one("#cmd_input")
        inp.styles.visibility = "hidden"
        inp.value = ""
        inp.blur()
        self.query_one("#cmd_status").styles.visibility = "visible"
        self.update_prompt()
            
    def execute_command(self, cmd: str):
        cmd = cmd.strip()
        if not cmd:
            self.deactivate()
            return
                
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
                
        if command in ("help", "h", "?"):
            self.show_help()
        elif command in ("symbol", "sym", "s"):
            if args and "/" in args:
                self.app.controller.set_symbol(args.upper())
                self.app.notify(f"Symbol set to {args.upper()}")
            else:
                self.app.notify("Usage: symbol BTC/USDT", severity="warning")
        elif command in ("timeframe", "tf", "t"):
            if args.isdigit():
                tf = int(args)
                if tf in (1, 3, 5, 15, 30, 60, 240, 1440):
                    self.app.controller.set_timeframe(tf)
                    self.app.notify(f"Timeframe set to {tf}m")
                else:
                    self.app.notify("Valid timeframes: 1,3,5,15,30,60,240,1440", severity="warning")
            else:
                self.app.notify("Usage: tf 15", severity="warning")
        elif command in ("refresh", "r"):
            self.app.controller.stop()
            self.app.controller.run()
            self.app.notify("Data refresh started")
        elif command in ("stop", "pause"):
            self.app.controller.stop()
            self.app.notify("Data updates paused")
        elif command in ("start", "resume"):
            if not self.app.controller.running:
                self.app.controller.run()
            self.app.notify("Data updates resumed")
        elif command in ("exit", "quit", "q"):
            self.app.exit()
        elif command in ("clear", "cls"):
            self.app.query_one(OrderBook).update("")
            self.app.notify("Screen cleared")
        else:
            self.app.notify(f"Unknown command: {command}. Type 'help'", severity="error")
                    
        self.deactivate()
            
    def show_help(self):
        help_text = (
            "[bold]Available commands:[/bold]\n"
            "  symbol <PAIR>   Set trading pair (e.g. symbol BTC/USDT)\n"
            "  tf <MINUTES>    Set candle timeframe (1,3,5,15,30,60,240,1440)\n"
            "  refresh         Restart data polling\n"
            "  stop/start      Pause/resume updates\n"
            "  clear           Clear chart area\n"
            "  help            Show this message\n"
            "  exit            Close application\n\n"
            "[bold]Keyboard shortcuts:[/bold]\n"
            "  :               Open command bar\n"
            "  ?               Show help\n"
            "  q               Quit\n"
            "  r               Refresh data\n"
            "  +/-             Increase/decrease timeframe\n"
            "  h/l or <-/->    Scroll chart horizontally\n"
        )
        self.app.notify(help_text, title="Help", severity="information", timeout=10)

class NonKYCApp(App):
    CSS = """
    Screen {
        layout: vertical;
        background: $surface;
    }
        
    #main_view {
        height: 1fr;
        border: solid $primary;
    }
    """
        
    BINDINGS = [
        Binding(":", "activate_command", "Command", show=False),
        Binding("?", "show_help_overlay", "Help", show=False),
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh_data", "Refresh", show=True),
        Binding("+", "increase_tf", "TF+", show=True),
        Binding("-", "decrease_tf", "TF-", show=True),
        Binding("h,left", "scroll_left", "Scroll Left", show=False),
        Binding("l,right", "scroll_right", "Scroll Right", show=False),
    ]
        
    def __init__(self, controller, symbol="BTC/USDT", **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.symbol = symbol
        self.scroll_offset = 0
            
    def compose(self) -> ComposeResult:
        yield OrderBook(id="main_view")
        yield CommandBar(id="command_bar")
            
    def on_mount(self):
        self.controller.subscribe(self.update_ui)
        self.controller.set_symbol(self.symbol)
        self.controller.run()
        self.query_one(CommandBar).update_prompt()
            
    def update_ui(self, state):
        self.query_one(OrderBook).update_data(state)
        self.query_one(CommandBar).update_prompt()
            
    def action_activate_command(self):
        self.query_one(CommandBar).activate()
            
    def action_show_help_overlay(self):
        self.query_one(CommandBar).show_help()
            
    def action_refresh_data(self):
        self.controller.stop()
        self.controller.run()
        self.notify("Data refresh started")
            
    def action_increase_tf(self):
        tf_map = [1, 3, 5, 15, 30, 60, 240, 1440]
        current = self.controller.timeframe
        try:
            idx = tf_map.index(current)
            new_tf = tf_map[min(idx + 1, len(tf_map) - 1)]
            self.controller.set_timeframe(new_tf)
            self.notify(f"Timeframe: {new_tf}m")
        except ValueError:
            pass
                
    def action_decrease_tf(self):
        tf_map = [1, 3, 5, 15, 30, 60, 240, 1440]
        current = self.controller.timeframe
        try:
            idx = tf_map.index(current)
            new_tf = tf_map[max(idx - 1, 0)]
            self.controller.set_timeframe(new_tf)
            self.notify(f"Timeframe: {new_tf}m")
        except ValueError:
            pass
                
    def action_scroll_left(self):
        self.scroll_offset = max(0, self.scroll_offset - 5)
            
    def action_scroll_right(self):
        self.scroll_offset += 5
            
    def on_input_submitted(self, message: Input.Submitted):
        if message.input.id == "cmd_input":
            self.query_one(CommandBar).execute_command(message.value)
