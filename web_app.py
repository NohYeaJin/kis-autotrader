from flask import Flask, redirect, render_template, request, url_for

from config import load_settings
from kis_api import KisApi
from trade_settings import load_trade_settings, save_trade_settings

app = Flask(__name__)
settings = load_settings()
api = KisApi(settings)


@app.route("/", methods=["GET", "POST"])
def index():
    error = None

    if request.method == "POST":
        try:
            buy_price = int(request.form["buy_price"])
            sell_price = int(request.form["sell_price"])
            order_qty = int(request.form["order_qty"])
            if buy_price <= 0 or sell_price <= 0 or order_qty <= 0:
                raise ValueError

            save_trade_settings(
                {"buy_price": buy_price, "sell_price": sell_price, "order_qty": order_qty}
            )
            return redirect(url_for("index", saved=1))
        except (KeyError, ValueError):
            error = "값을 올바르게 입력해주세요 (양의 정수)."

    status_errors = []

    try:
        current_price = api.get_current_price(settings.stock_code)
    except Exception as exc:
        current_price = None
        status_errors.append(f"현재가 조회 실패: {exc}")

    try:
        holding = api.get_holding_info(settings.stock_code)
    except Exception as exc:
        holding = {"qty": 0, "avg_price": 0}
        status_errors.append(f"잔고 조회 실패: {exc}")

    status_error = " / ".join(status_errors) if status_errors else None

    return render_template(
        "index.html",
        settings=load_trade_settings(),
        error=error,
        saved=request.args.get("saved"),
        current_price=current_price,
        holding=holding,
        status_error=status_error,
    )


if __name__ == "__main__":
    app.run(port=5000, debug=False)
