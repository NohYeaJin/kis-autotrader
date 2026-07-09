import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"
MOCK_BASE_URL = "https://openapivts.koreainvestment.com:29443"

STOCK_CODE = "000660"  # SK하이닉스
MARKET_OPEN = "09:00"
MARKET_CLOSE = "15:30"
POLL_INTERVAL_SEC = 30


@dataclass
class Settings:
    app_key: str
    app_secret: str
    cano: str
    acnt_prdt_cd: str
    is_mock: bool
    base_url: str
    order_qty: int

    buy_price_threshold: int
    sell_price_threshold: int

    stock_code: str = STOCK_CODE
    market_open: str = MARKET_OPEN
    market_close: str = MARKET_CLOSE
    poll_interval_sec: int = POLL_INTERVAL_SEC


def load_settings() -> Settings:
    app_key = os.environ["APP_KEY"]
    app_secret = os.environ["APP_SECRET"]
    account_no = os.environ["ACCOUNT_NO"]  # 형식: "12345678-01"
    is_mock = os.environ.get("IS_MOCK", "true").strip().lower() == "true"
    order_qty = int(os.environ.get("ORDER_QTY", "1"))
    buy_price_threshold = int(os.environ["BUY_PRICE"])
    sell_price_threshold = int(os.environ["SELL_PRICE"])

    cano, acnt_prdt_cd = account_no.split("-")

    return Settings(
        app_key=app_key,
        app_secret=app_secret,
        cano=cano,
        acnt_prdt_cd=acnt_prdt_cd,
        is_mock=is_mock,
        base_url=MOCK_BASE_URL if is_mock else REAL_BASE_URL,
        order_qty=order_qty,
        buy_price_threshold=buy_price_threshold,
        sell_price_threshold=sell_price_threshold,
    )
