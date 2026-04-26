from nonkyc.ui import NonKYCApp
from nonkyc.controller import TraderController

if __name__ == "__main__":
    controller = TraderController()
    app = NonKYCApp(controller, symbol="BTC/USDT")
    app.run()
