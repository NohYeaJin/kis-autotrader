from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

import requests

from config import Settings

logger = logging.getLogger(__name__)

PRICE_TR_ID = "FHKST01010100"
BUY_TR_ID = {"real": "TTTC0012U", "mock": "VTTC0012U"}
SELL_TR_ID = {"real": "TTTC0011U", "mock": "VTTC0011U"}
BALANCE_TR_ID = {"real": "TTTC8434R", "mock": "VTTC8434R"}


class KisApi:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._access_token = None
        self._token_expires_at = None

    def _mode(self) -> str:
        return "mock" if self.settings.is_mock else "real"

    def get_access_token(self) -> str:
        if (
            self._access_token
            and self._token_expires_at
            and datetime.now() < self._token_expires_at
        ):
            return self._access_token

        url = f"{self.settings.base_url}/oauth2/tokenP"
        body = {
            "grant_type": "client_credentials",
            "appkey": self.settings.app_key,
            "appsecret": self.settings.app_secret,
        }
        res = requests.post(url, json=body, timeout=10)
        res.raise_for_status()
        data = res.json()

        self._access_token = data["access_token"]
        self._token_expires_at = datetime.now() + timedelta(hours=23)
        logger.info("접근토큰 발급 완료")
        return self._access_token

    def _headers(self, tr_id: str) -> dict:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.get_access_token()}",
            "appkey": self.settings.app_key,
            "appsecret": self.settings.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def get_current_price(self, stock_code: str) -> int:
        url = f"{self.settings.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
        }
        res = requests.get(url, headers=self._headers(PRICE_TR_ID), params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data.get("rt_cd") != "0":
            raise RuntimeError(f"현재가 조회 실패: {data.get('msg1')}")
        return int(data["output"]["stck_prpr"])

    def _find_holding(self, stock_code: str) -> dict | None:
        tr_id = BALANCE_TR_ID[self._mode()]
        url = f"{self.settings.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        params = {
            "CANO": self.settings.cano,
            "ACNT_PRDT_CD": self.settings.acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        last_error = None
        for attempt in range(2):
            try:
                res = requests.get(url, headers=self._headers(tr_id), params=params, timeout=10)
                res.raise_for_status()
                data = res.json()
                if data.get("rt_cd") != "0":
                    raise RuntimeError(f"잔고 조회 실패: {data.get('msg1')}")
                break
            except (requests.exceptions.HTTPError, RuntimeError) as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(1)
        else:
            raise last_error

        for item in data.get("output1", []):
            if item.get("pdno") == stock_code:
                return item
        return None

    def get_holding_quantity(self, stock_code: str) -> int:
        item = self._find_holding(stock_code)
        return int(item["hldg_qty"]) if item else 0

    def get_holding_info(self, stock_code: str) -> dict:
        item = self._find_holding(stock_code)
        if not item or int(item["hldg_qty"]) == 0:
            return {"qty": 0, "avg_price": 0}
        return {"qty": int(item["hldg_qty"]), "avg_price": int(float(item["pchs_avg_pric"]))}

    def _place_order(self, tr_id: str, stock_code: str, qty: int) -> dict:
        url = f"{self.settings.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        body = {
            "CANO": self.settings.cano,
            "ACNT_PRDT_CD": self.settings.acnt_prdt_cd,
            "PDNO": stock_code,
            "ORD_DVSN": "01",   # 시장가
            "ORD_QTY": str(qty),
            "ORD_UNPR": "0",    # 시장가 주문은 0
            "EXCG_ID_DVSN_CD": "KRX",
        }
        res = requests.post(url, headers=self._headers(tr_id), json=body, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data.get("rt_cd") != "0":
            raise RuntimeError(f"주문 실패: {data.get('msg1')}")
        return data

    def buy_market_order(self, stock_code: str, qty: int) -> dict:
        return self._place_order(BUY_TR_ID[self._mode()], stock_code, qty)

    def sell_market_order(self, stock_code: str, qty: int) -> dict:
        return self._place_order(SELL_TR_ID[self._mode()], stock_code, qty)
