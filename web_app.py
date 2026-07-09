from flask import Flask, redirect, render_template, request, url_for

from trade_settings import load_trade_settings, save_trade_settings

app = Flask(__name__)


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

    return render_template(
        "index.html",
        settings=load_trade_settings(),
        error=error,
        saved=request.args.get("saved"),
    )


if __name__ == "__main__":
    app.run(port=5000, debug=False)
