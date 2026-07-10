import json
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "trade_history.json"
MAX_RECORDS = 200


def load_history() -> list:
    if not HISTORY_FILE.exists():
        return []
    return json.loads(HISTORY_FILE.read_text())


def record_trade(code: str, name: str, action: str, qty: int, price: int) -> None:
    history = load_history()
    history.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "code": code,
            "name": name,
            "action": action,
            "qty": qty,
            "price": price,
        }
    )
    history = history[-MAX_RECORDS:]
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2))
