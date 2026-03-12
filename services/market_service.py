from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from analytics.portfolio_risk import analyze_portfolio, clean_portfolio_positions
from analytics.risk_metrics import calculate_rolling_volatility_series, summarize_exchange_rate_history
from data_ingestion.clean_data import EXPECTED_COLUMNS, clean_exchange_rates
from data_ingestion.fetch_data import (
    fetch_historical_rates,
    fetch_latest_rates,
    fetch_multi_currency_history,
    fetch_supported_currencies,
)

DEFAULT_MARKET_CURRENCIES = ["USD", "GBP", "CHF", "JPY", "AUD", "CAD"]
SAMPLE_PORTFOLIO_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_portfolio.csv"


def get_default_target_currencies() -> list[str]:
    load_dotenv()
    configured = os.getenv("DEFAULT_TARGET_CURRENCIES", "")
    if configured:
        return [currency.strip().upper() for currency in configured.split(",") if currency.strip()]
    return DEFAULT_MARKET_CURRENCIES.copy()


def get_supported_currency_catalog() -> pd.DataFrame:
    return fetch_supported_currencies().sort_values("symbol").reset_index(drop=True)


def load_sample_portfolio() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_PORTFOLIO_PATH)


def _empty_rates_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=EXPECTED_COLUMNS)


def _ensure_supported_currencies(currencies: list[str], reporting_currency: str = "EUR") -> None:
    supported = set(get_supported_currency_catalog()["symbol"])
    unsupported = sorted(
        currency for currency in set(currencies) if currency != reporting_currency and currency not in supported
    )
    if unsupported:
        raise ValueError(f"Unsupported currencies in portfolio: {', '.join(unsupported)}")


def _build_synthetic_reporting_history(
    reporting_currency: str,
    start_date: str,
    end_date: str,
    frequency: str,
) -> pd.DataFrame:
    frequency_map = {"D": "B", "M": "ME", "Q": "QE", "A": "YE"}
    date_index = pd.date_range(start=start_date, end=end_date, freq=frequency_map.get(frequency, "B"))
    if date_index.empty:
        date_index = pd.DatetimeIndex([pd.to_datetime(start_date), pd.to_datetime(end_date)]).unique()

    return pd.DataFrame(
        {
            "base_currency": "EUR",
            "target_currency": reporting_currency,
            "rate_date": date_index.strftime("%Y-%m-%d"),
            "exchange_rate": 1.0,
            "frequency": frequency,
            "source": "Synthetic reporting currency baseline",
        }
    )


def _append_reporting_currency_history(
    history: pd.DataFrame,
    reporting_currency: str,
    start_date: str,
    end_date: str,
    frequency: str,
) -> pd.DataFrame:
    synthetic_history = _build_synthetic_reporting_history(reporting_currency, start_date, end_date, frequency)
    return clean_exchange_rates(pd.concat([history, synthetic_history], ignore_index=True))


def _append_reporting_currency_latest(latest_rates: pd.DataFrame, reporting_currency: str, as_of_date: str) -> pd.DataFrame:
    synthetic_latest = pd.DataFrame(
        [
            {
                "base_currency": "EUR",
                "target_currency": reporting_currency,
                "rate_date": as_of_date,
                "exchange_rate": 1.0,
                "frequency": "D",
                "source": "Synthetic reporting currency baseline",
            }
        ]
    )
    return clean_exchange_rates(pd.concat([latest_rates, synthetic_latest], ignore_index=True))


def get_latest_snapshot(currencies: list[str] | tuple[str, ...]) -> pd.DataFrame:
    filtered_currencies = [currency.upper() for currency in currencies if currency.upper() != "EUR"]
    if not filtered_currencies:
        return _empty_rates_frame()
    return clean_exchange_rates(fetch_latest_rates(filtered_currencies))


def build_market_monitor(
    focus_currency: str,
    currencies: list[str] | tuple[str, ...] | None = None,
    lookback_days: int = 180,
    frequency: str = "D",
) -> dict[str, pd.DataFrame | dict[str, float | str]]:
    focus_currency = focus_currency.upper().strip()
    selected_currencies = list(currencies) if currencies else get_default_target_currencies()
    _ensure_supported_currencies(selected_currencies + [focus_currency])

    end = date.today()
    start = end - timedelta(days=lookback_days)
    latest_snapshot = get_latest_snapshot(selected_currencies)
    history = clean_exchange_rates(
        fetch_historical_rates(
            target_currency=focus_currency,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            frequency=frequency,
        )
    )
    summary = summarize_exchange_rate_history(history)
    history_series = history.assign(rate_date=pd.to_datetime(history["rate_date"])).set_index("rate_date")["exchange_rate"]
    rolling_volatility = calculate_rolling_volatility_series(history_series, window=min(20, max(5, len(history) // 4)))
    rolling_volatility_frame = rolling_volatility.rename("rolling_volatility").reset_index()
    rolling_volatility_frame["rate_date"] = pd.to_datetime(rolling_volatility_frame["rate_date"]).dt.strftime("%Y-%m-%d")

    return {
        "summary": summary,
        "history": history,
        "latest_snapshot": latest_snapshot,
        "rolling_volatility": rolling_volatility_frame,
    }


def build_portfolio_analysis(
    positions: pd.DataFrame,
    lookback_days: int = 252,
    confidence_level: float = 0.95,
    rolling_window: int = 20,
    frequency: str = "D",
    scenario_shocks: dict[str, float] | None = None,
    reporting_currency: str = "EUR",
) -> dict[str, pd.DataFrame | dict[str, float | int | str]]:
    reporting_currency = reporting_currency.upper().strip()
    cleaned_positions = clean_portfolio_positions(positions)
    portfolio_currencies = sorted(cleaned_positions["currency"].unique().tolist())
    _ensure_supported_currencies(portfolio_currencies, reporting_currency=reporting_currency)

    end = date.today()
    start = end - timedelta(days=lookback_days)
    non_reporting_currencies = [currency for currency in portfolio_currencies if currency != reporting_currency]

    latest_rates = get_latest_snapshot(non_reporting_currencies)
    rate_history = (
        clean_exchange_rates(
            fetch_multi_currency_history(
                target_currencies=non_reporting_currencies,
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                frequency=frequency,
            )
        )
        if non_reporting_currencies
        else _empty_rates_frame()
    )

    rate_history = _append_reporting_currency_history(
        history=rate_history,
        reporting_currency=reporting_currency,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        frequency=frequency,
    )
    latest_snapshot = _append_reporting_currency_latest(
        latest_rates=latest_rates,
        reporting_currency=reporting_currency,
        as_of_date=end.isoformat(),
    )

    analysis = analyze_portfolio(
        positions=cleaned_positions,
        latest_rates=latest_snapshot,
        rate_history=rate_history,
        reporting_currency=reporting_currency,
        confidence_level=confidence_level,
        rolling_window=rolling_window,
        scenario_shocks=scenario_shocks,
    )
    analysis["market_snapshot"] = latest_snapshot.sort_values("target_currency").reset_index(drop=True)
    analysis["rate_history"] = rate_history
    return analysis
