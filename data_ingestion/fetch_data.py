from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Iterable

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_BASE_URL = "https://api.euroratesapi.dev"
DEFAULT_TIMEOUT_SECONDS = 60.0


def _build_session() -> requests.Session:
    retry_strategy = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = _build_session()


def _get_base_url() -> str:
    load_dotenv()
    return os.getenv("EURO_RATES_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _get_timeout_seconds() -> float:
    load_dotenv()
    return float(os.getenv("REQUEST_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))


def _request_json(path: str, params: dict[str, str] | None = None) -> dict | list:
    response = SESSION.get(f"{_get_base_url()}{path}", params=params, timeout=_get_timeout_seconds())
    response.raise_for_status()
    return response.json()


def _normalize_currency_list(target_currencies: Iterable[str]) -> list[str]:
    normalized = [currency.strip().upper() for currency in target_currencies if currency.strip()]
    if not normalized:
        raise ValueError("At least one target currency is required.")
    return normalized


def fetch_supported_currencies() -> pd.DataFrame:
    payload = _request_json("/api/all-currencies")
    return pd.DataFrame(payload)


def fetch_latest_rates(target_currencies: Iterable[str], base_currency: str = "EUR") -> pd.DataFrame:
    base_currency = base_currency.upper()
    if base_currency != "EUR":
        raise ValueError("The Euro Rates API currently supports EUR as the base currency for /api/rates.")

    currencies = _normalize_currency_list(target_currencies)

    records = []
    # The documented multi-currency response currently returns swapped values for some pairs,
    # so latest rates are fetched one currency at a time for correctness.
    for target_currency in currencies:
        payload = _request_json(
            "/api/rates",
            params={"from": base_currency, "to": target_currency},
        )
        records.append(
            {
                "base_currency": payload["from"],
                "target_currency": payload["to"],
                "rate_date": payload["date"],
                "exchange_rate": payload["rate"],
                "frequency": "D",
                "source": payload.get("source", "European Central Bank (ECB)"),
            }
        )

    return pd.DataFrame(records)


def fetch_historical_rates(
    target_currency: str,
    start_date: str,
    end_date: str,
    frequency: str = "D",
    base_currency: str = "EUR",
) -> pd.DataFrame:
    base_currency = base_currency.upper()
    target_currency = target_currency.upper().strip()
    frequency = frequency.upper().strip()

    if base_currency != "EUR":
        raise ValueError("The Euro Rates API currently supports EUR as the base currency for /api/history.")
    if frequency not in {"D", "M", "Q", "A"}:
        raise ValueError("Frequency must be one of: D, M, Q, A.")

    payload = _request_json(
        "/api/history",
        params={
            "from": base_currency,
            "to": target_currency,
            "start": start_date,
            "end": end_date,
            "frequency": frequency,
        },
    )

    records = [
        {
            "base_currency": base_currency,
            "target_currency": target_currency,
            "rate_date": entry["date"],
            "exchange_rate": entry["rate"],
            "frequency": frequency,
            "source": "European Central Bank (ECB)",
        }
        for entry in payload
    ]
    return pd.DataFrame(records)


def fetch_multi_currency_history(
    target_currencies: Iterable[str],
    start_date: str,
    end_date: str,
    frequency: str = "D",
    base_currency: str = "EUR",
) -> pd.DataFrame:
    frames = [
        fetch_historical_rates(
            target_currency=currency,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            base_currency=base_currency,
        )
        for currency in _normalize_currency_list(target_currencies)
    ]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


if __name__ == "__main__":
    end = date.today()
    start = end - timedelta(days=30)
    print(fetch_supported_currencies().head())
    print(fetch_latest_rates(["USD", "GBP", "CHF"]))
    print(fetch_multi_currency_history(["USD", "GBP"], start.isoformat(), end.isoformat()).head())
