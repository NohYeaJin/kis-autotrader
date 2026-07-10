from flask import Flask, redirect, render_template, request, url_for

from config import load_settings
from kis_api import KisApi
from trade_history import load_history
from trade_settings import STOCKS, load_trade_settings, save_trade_settings

app = Flask(__name__)
settings = load_settings()
api = KisApi(settings)

STOCK_NAMES = {s["code"]: s["name"] for s in STOCKS}


@app.route("/update/<code>", methods=["POST"])
def update(code):
    if code not in STOCK_NAMES:
        return "알 수 없는 종목", 404

    try:
        buy_price = int(request.form["buy_price"])
        sell_price = int(request.form["sell_price"])
        order_qty = int(request.form["order_qty"])
        if buy_price <= 0 or sell_price <= 0 or order_qty <= 0:
            raise ValueError

        trade_settings = load_trade_settings()
        trade_settings[code] = {
            "buy_price": buy_price,
            "sell_price": sell_price,
            "order_qty": order_qty,
            "enabled": "enabled" in request.form,
        }
        save_trade_settings(trade_settings)
        return redirect(url_for("index", saved=code))
    except (KeyError, ValueError):
        return redirect(url_for("index", error=code))


@app.route("/", methods=["GET"])
def index():
    trade_settings = load_trade_settings()
    rows = []
    status_errors = []

    for stock in STOCKS:
        code, name = stock["code"], stock["name"]

        try:
            current_price = api.get_current_price(code)
        except Exception as exc:
            current_price = None
            status_errors.append(f"[{name}] 현재가 조회 실패: {exc}")

        try:
            holding = api.get_holding_info(code)
        except Exception as exc:
            holding = {"qty": 0, "avg_price": 0}
            status_errors.append(f"[{name}] 잔고 조회 실패: {exc}")

        rows.append(
            {
                "code": code,
                "name": name,
                "current_price": current_price,
                "holding": holding,
                "settings": trade_settings[code],
            }
        )

    status_error = " / ".join(status_errors) if status_errors else None
    saved_code = request.args.get("saved")
    error_code = request.args.get("error")
    recent_trades = list(reversed(load_history()))[:10]

    return render_template(
        "index.html",
        rows=rows,
        status_error=status_error,
        saved_name=STOCK_NAMES.get(saved_code),
        error_name=STOCK_NAMES.get(error_code),
        recent_trades=recent_trades,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
