from nonkyc.controller import TraderController
from nonkyc.ui import NonKYCApp

if __name__ == "__main__":
    controller = TraderController()
    app = NonKYCApp(controller, symbol="BTC/USDT")
    app.run()
