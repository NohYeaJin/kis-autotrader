from flask import Flask, redirect, render_template, request, url_for

from config import load_settings
from kis_api import KisApi
from trade_settings import STOCKS, load_trade_settings, save_trade_settings

app = Flask(__name__)
settings = load_settings()
api = KisApi(settings)


@app.route("/", methods=["GET", "POST"])
def index():
    error = None

    if request.method == "POST":
        try:
            trade_settings = load_trade_settings()
            for stock in STOCKS:
                code = stock["code"]
                buy_price = int(request.form[f"buy_price_{code}"])
                sell_price = int(request.form[f"sell_price_{code}"])
                order_qty = int(request.form[f"order_qty_{code}"])
                if buy_price <= 0 or sell_price <= 0 or order_qty <= 0:
                    raise ValueError
                trade_settings[code] = {
                    "buy_price": buy_price,
                    "sell_price": sell_price,
                    "order_qty": order_qty,
                }
            save_trade_settings(trade_settings)
            return redirect(url_for("index", saved=1))
        except (KeyError, ValueError):
            error = "값을 올바르게 입력해주세요 (양의 정수)."

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

    return render_template(
        "index.html",
        rows=rows,
        error=error,
        saved=request.args.get("saved"),
        status_error=status_error,
    )


if __name__ == "__main__":
    app.run(port=5000, debug=False)
