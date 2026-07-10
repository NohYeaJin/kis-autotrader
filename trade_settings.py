import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent / "trade_settings.json"

STOCKS = [
    {"code": "000660", "name": "SK하이닉스"},
    {"code": "005930", "name": "삼성전자"},
    {"code": "402340", "name": "SK스퀘어"},
    {"code": "005380", "name": "현대자동차"},
    {"code": "009150", "name": "삼성전기"},
]

DEFAULT_SETTINGS = {
    "000660": {"buy_price": 2_150_000, "sell_price": 2_220_000, "order_qty": 1},
    "005930": {"buy_price": 280_000, "sell_price": 290_000, "order_qty": 1},
    "402340": {"buy_price": 1_380_000, "sell_price": 1_430_000, "order_qty": 1},
    "005380": {"buy_price": 450_000, "sell_price": 465_000, "order_qty": 1},
    "009150": {"buy_price": 1_550_000, "sell_price": 1_610_000, "order_qty": 1},
}


def load_trade_settings() -> dict:
    if not SETTINGS_FILE.exists():
        save_trade_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)

    saved = json.loads(SETTINGS_FILE.read_text())
    merged = {**DEFAULT_SETTINGS, **saved}
    return merged


def save_trade_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False))
