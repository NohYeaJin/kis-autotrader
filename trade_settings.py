import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent / "trade_settings.json"

DEFAULT_SETTINGS = {
    "buy_price": 210_000,
    "sell_price": 220_000,
    "order_qty": 1,
}


def load_trade_settings() -> dict:
    if not SETTINGS_FILE.exists():
        save_trade_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    return json.loads(SETTINGS_FILE.read_text())


def save_trade_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))
