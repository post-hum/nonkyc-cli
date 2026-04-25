from textual.app import App, ComposeResult
from textual.widgets import Static, Input
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from rich.table import Table
from rich.text import Text
from .charts import candle_ascii
from .controller import TraderController

class CommandBar(Static):
    """
    Строка команд (внизу). Обрабатывает ввод после ':'.
    """
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Type command", id="cmd_input")
    def on_mount(self):
        self.app.set_interval(0.5, self._blink_cursor)  # курсор для красоты
        self.active = False
    def _blink_cursor(self):
        inp = self.query_one("#cmd_input")
        # простой курсор, мигающий на конце
        if not self.active:
            inp.placeholder = ""
        else:
            inp.placeholder = "|"
    def activate(self):
        self.active = True
        self.query_one("#cmd_input").focus()
    def deactivate(self):
        self.active = False
        inp = self.query_one("#cmd_input")
        inp.value = ""
        self.app.set_focus(None)

    def execute_command(self, command: str):
        parts = command.strip().split()
        if not parts:
            self.deactivate()
            return
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        if cmd in ("help", "?"):
            self.app.show_help_overlay()
        elif cmd in ("symbol", "sym", "s") and args:
            pair = args[0].upper()
            if "/" in pair:
                self.app.controller.set_symbol(pair)
                self.app.notify(f"Symbol set to {pair}")
            else:
                self.app.notify("Usage: symbol BTC/USDT", severity="warning")
        elif cmd in ("timeframe", "tf", "t") and args:
            if args[0].isdigit():
                tf = int(args[0])
                if tf in (1,3,5,15,30,60,240,1440):
                    self.app.controller.set_timeframe(tf)
                    self.app.notify(f"Timeframe set to {tf}m")
                else:
                    self.app.notify("Valid TF: 1,3,5,15,30,60,240,1440", severity="warning")
            else:
                self.app.notify("Usage: tf <minutes>", severity="warning")
        elif cmd == "refresh":
            self.app.controller.stop()
            self.app.controller.run()
            self.app.notify("Data refresh started")
        elif cmd in ("stop", "pause"):
            self.app.controller.stop()
            self.app.notify("Data updates paused")
        elif cmd in ("start", "resume"):
            if not self.app.controller.running:
                self.app.controller.run()
            self.app.notify("Data updates resumed")
        elif cmd in ("exit", "quit", "q"):
            self.app.exit()
        elif cmd in ("clear", "cls"):
            self.app.query_one("#chart").update("") 
            self.app.query_one("#orderbook").update("")
            self.app.query_one("#orders").update("")
            self.app.notify("Screen cleared")
        elif cmd == "orders":
            orders = self.app.controller.refresh_orders()
            self.app.notify(f"Open orders: {len(orders)}", title="Orders")
        elif cmd == "buy" or cmd == "sell":
            if args:
                try:
                    qty = Decimal(args[0])
                    price = Decimal(args[1]) if len(args) > 1 else None
                except Exception:
                    self.app.notify("Invalid quantity/price", severity="error")
                    self.deactivate()
                    return
                side = "buy" if cmd == "buy" else "sell"
                res = self.app.controller.place_order(side, qty, price)
                self.app.notify(f"{cmd.upper()} order sent: {res.get('id','')}")
            else:
                self.app.notify(f"Usage: {cmd} <qty> [price]", severity="warning")
        elif cmd == "cancel" and args:
            res = self.app.controller.cancel_order(args[0])
            self.app.notify(f"Cancel requested: {res.get('id','')}")
        else:
            self.app.notify(f"Unknown command: {cmd}", severity="error")
        self.deactivate()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.active:
            self.execute_command(event.value)

class NonKYCApp(App):
    """
    Основное приложение Textual.
    """
    CSS = """
    #chart, #orderbook, #orders {border: round $secondary;}
    """

    BINDINGS = [
        Binding(":", "activate_command", "Command"),
        Binding("?", "show_help_overlay", "Help"),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_data", "Refresh"),
        Binding("+", "increase_tf", "TF+"),
        Binding("-", "decrease_tf", "TF-"),
        Binding("h", "scroll_left", "Scroll Left"),
        Binding("l", "scroll_right", "Scroll Right"),
    ]

    def __init__(self, controller: TraderController, symbol="BTC/USDT", **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.controller.subscribe(self.update_ui)
        self.controller.set_symbol(symbol)
        self.controller.run()
        self.scroll_offset = 0

    def compose(self) -> ComposeResult:
        # Основной макет: график (широкий), затем стакан+ордера, затем строка команд
        yield Vertical(
            Static(id="chart"),
            Horizontal(
                Static(id="orderbook"),
                Static(id="orders")
            ),
            CommandBar(id="cmd")
        )

    def update_ui(self, state: dict):
        """Обновление данных на экране."""
        if "error" in state:
            self.notify(f"Error: {state['error']}", severity="error")
            return
        # График свечей
        chart_w = self.size.width - 2  # учесть границы
        chart_h = max(10, self.size.height - 10)
        chart_text = candle_ascii(state.get("candles", []), width=chart_w, height=chart_h)
        self.query_one("#chart").update(chart_text)
        # Стакан (bids/asks)
        orderbook_txt = Text()
        orderbook_txt.append("BIDS", style="bold green")
        orderbook_txt.append("\n")
        for price, qty in state.get("bids", []):
            orderbook_txt.append(f"{Decimal(price):.2f}".rjust(8), style="green")
            orderbook_txt.append(f" x {Decimal(qty):.4f}\n", style="dim")
        orderbook_txt.append("\nASKS", style="bold red")
        orderbook_txt.append("\n")
        for price, qty in state.get("asks", []):
            orderbook_txt.append(f"{Decimal(price):.2f}".rjust(8), style="red")
            orderbook_txt.append(f" x {Decimal(qty):.4f}\n", style="dim")
        self.query_one("#orderbook").update(orderbook_txt)
        # Панель открытых ордеров
        orders_txt = Text()
        orders_txt.append("ID".ljust(10) + " SIDE  PRICE     QTY\n", style="underline")
        for o in state.get("orders", []):
            # представление ордера: первые 8 символов ID
            oid = o.get("id","")[:8]
            side = o.get("side","").upper().ljust(4)
            price = f"{Decimal(o.get('price',0)):.6f}"
            qty = f"{Decimal(o.get('quantity',0)):.4f}"
            color = "green" if o.get("side","").lower()=="buy" else "red"
            orders_txt.append(f"{oid.ljust(10)}{side} {price.rjust(8)} {qty.rjust(8)}\n", style=color)
        self.query_one("#orders").update(orders_txt)

    # Командные действия (связанные с привязкой клавиш)
    def action_activate_command(self):
        self.query_one(CommandBar).activate()

    def action_show_help_overlay(self):
        help_text = ("Commands:\n"
                     "  symbol <PAIR>   Set trading pair (BTC/USDT)\n"
                     "  tf <MINUTES>    Set candle timeframe\n"
                     "  buy <qty>[ price]   Place buy order (market/limit)\n"
                     "  sell <qty>[ price]  Place sell order\n"
                     "  cancel <id>     Cancel order by ID\n"
                     "  orders          Refresh open orders\n"
                     "  refresh         Restart polling\n"
                     "  stop/start      Pause/resume updates\n"
                     "  clear           Clear screen\n"
                     "  help            Show this message\n"
                     "  exit            Quit application\n"
                     "\nShortcuts: : for commands, ? for help, r refresh, q quit, +/- change TF")
        self.notify(help_text, title="Help", severity="info")

    def action_refresh_data(self):
        self.controller.stop()
        self.controller.run()
        self.notify("Data refresh started")

    def action_increase_tf(self):
        tf_list = [1,3,5,15,30,60,240,1440]
        try:
            idx = tf_list.index(self.controller.timeframe)
            new_tf = tf_list[min(idx+1, len(tf_list)-1)]
            self.controller.set_timeframe(new_tf)
            self.notify(f"Timeframe: {new_tf}m")
        except:
            pass

    def action_decrease_tf(self):
        tf_list = [1,3,5,15,30,60,240,1440]
        try:
            idx = tf_list.index(self.controller.timeframe)
            new_tf = tf_list[max(idx-1, 0)]
            self.controller.set_timeframe(new_tf)
            self.notify(f"Timeframe: {new_tf}m")
        except:
            pass

    def action_scroll_left(self):
        self.scroll_offset = max(0, self.scroll_offset - 5)

    def action_scroll_right(self):
        self.scroll_offset += 5
