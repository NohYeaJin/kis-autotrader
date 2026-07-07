import json
import logging
import time
from datetime import date, datetime
from pathlib import Path

from config import load_settings
from kis_api import KisApi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

STATE_FILE = Path(__file__).parent / "state.json"


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state))


def bought_today(state: dict) -> bool:
    return state.get("last_buy_date") == date.today().isoformat()


def mark_bought_today(state: dict) -> None:
    state["last_buy_date"] = date.today().isoformat()
    save_state(state)


def parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":")
    return int(hour), int(minute)


def wait_until_market_open(open_hhmm: str) -> None:
    hour, minute = parse_hhmm(open_hhmm)
    while True:
        now = datetime.now()
        open_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now >= open_time:
            return
        remaining = (open_time - now).total_seconds()
        logger.info("장 시작 전입니다. %.0f초 후 다시 확인합니다.", min(remaining, 60))
        time.sleep(min(remaining, 60))


def is_market_open(now: datetime, open_hhmm: str, close_hhmm: str) -> bool:
    open_h, open_m = parse_hhmm(open_hhmm)
    close_h, close_m = parse_hhmm(close_hhmm)
    open_time = now.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
    close_time = now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
    return open_time <= now <= close_time


def run() -> None:
    settings = load_settings()
    api = KisApi(settings)
    state = load_state()

    mode = "모의투자" if settings.is_mock else "실전투자"
    logger.info(
        "자동매매 시작 (%s) | 종목: %s | 매수기준: %s원 이하 | 매도기준: %s원 이상 | 수량: %s주",
        mode,
        settings.stock_code,
        f"{settings.buy_price_threshold:,}",
        f"{settings.sell_price_threshold:,}",
        settings.order_qty,
    )

    wait_until_market_open(settings.market_open)

    while True:
        now = datetime.now()
        if not is_market_open(now, settings.market_open, settings.market_close):
            logger.info("장 마감 시간이 되어 프로그램을 종료합니다.")
            break

        try:
            price = api.get_current_price(settings.stock_code)
            holding_qty = api.get_holding_quantity(settings.stock_code)
            logger.info("현재가: %s원 | 보유수량: %s주", f"{price:,}", holding_qty)

            if holding_qty == 0:
                if not bought_today(state) and price <= settings.buy_price_threshold:
                    api.buy_market_order(settings.stock_code, settings.order_qty)
                    mark_bought_today(state)
                    logger.info(
                        "[매수 체결] %s주 (기준: %s원 이하, 현재가: %s원)",
                        settings.order_qty,
                        f"{settings.buy_price_threshold:,}",
                        f"{price:,}",
                    )
            else:
                if price >= settings.sell_price_threshold:
                    api.sell_market_order(settings.stock_code, holding_qty)
                    logger.info(
                        "[매도 체결] %s주 (기준: %s원 이상, 현재가: %s원)",
                        holding_qty,
                        f"{settings.sell_price_threshold:,}",
                        f"{price:,}",
                    )

        except Exception:
            logger.exception("루프 처리 중 오류가 발생했습니다. 다음 주기에 재시도합니다.")

        time.sleep(settings.poll_interval_sec)


if __name__ == "__main__":
    run()
