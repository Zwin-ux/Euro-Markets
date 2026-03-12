from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from data_ingestion.clean_data import clean_exchange_rates

from analytics.risk_metrics import (
    calculate_annualized_volatility,
    calculate_historical_var_from_returns,
    calculate_rolling_volatility_series,
    calculate_series_returns,
)

PORTFOLIO_REQUIRED_COLUMNS = [
    "position_id",
    "position_name",
    "currency",
    "market_value_local",
]
PORTFOLIO_OPTIONAL_COLUMNS = ["asset_class", "book"]
PORTFOLIO_COLUMN_ALIASES = {
    "id": "position_id",
    "position": "position_name",
    "local_amount": "market_value_local",
    "market_value": "market_value_local",
    "notional_local": "market_value_local",
    "desk": "book",
}


def clean_portfolio_positions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("Portfolio positions are empty.")

    cleaned = frame.copy()
    cleaned.columns = [column.strip().lower().replace(" ", "_") for column in cleaned.columns]
    cleaned = cleaned.rename(columns=PORTFOLIO_COLUMN_ALIASES)

    missing_columns = [column for column in PORTFOLIO_REQUIRED_COLUMNS if column not in cleaned.columns]
    if missing_columns:
        raise ValueError(f"Missing required portfolio columns: {', '.join(missing_columns)}")

    for column in PORTFOLIO_OPTIONAL_COLUMNS:
        if column not in cleaned.columns:
            cleaned[column] = ""

    cleaned["position_id"] = cleaned["position_id"].astype(str).str.strip()
    cleaned["position_name"] = cleaned["position_name"].astype(str).str.strip()
    cleaned["currency"] = cleaned["currency"].astype(str).str.upper().str.strip()
    cleaned["market_value_local"] = pd.to_numeric(cleaned["market_value_local"], errors="raise")
    cleaned["asset_class"] = cleaned["asset_class"].astype(str).str.strip()
    cleaned["book"] = cleaned["book"].astype(str).str.strip()

    cleaned = cleaned.loc[cleaned["position_id"] != ""].copy()
    cleaned = cleaned.loc[cleaned["currency"] != ""].copy()
    cleaned["position_name"] = cleaned["position_name"].where(cleaned["position_name"] != "", cleaned["position_id"])

    if cleaned.empty:
        raise ValueError("Portfolio positions are empty after cleaning.")

    return cleaned[PORTFOLIO_REQUIRED_COLUMNS + PORTFOLIO_OPTIONAL_COLUMNS].reset_index(drop=True)


def build_portfolio_value_history(
    positions: pd.DataFrame,
    rate_history: pd.DataFrame,
    reporting_currency: str = "EUR",
) -> pd.DataFrame:
    positions_clean = clean_portfolio_positions(positions)
    history_clean = clean_exchange_rates(rate_history)
    if history_clean.empty:
        raise ValueError("Rate history is empty.")

    reporting_currency = reporting_currency.upper().strip()
    pivoted_rates = history_clean.pivot_table(
        index="rate_date",
        columns="target_currency",
        values="exchange_rate",
        aggfunc="last",
    ).sort_index()

    if reporting_currency not in pivoted_rates.columns:
        pivoted_rates[reporting_currency] = 1.0

    missing_currencies = sorted(set(positions_clean["currency"]) - set(pivoted_rates.columns))
    if missing_currencies:
        raise ValueError(f"Missing exchange-rate history for: {', '.join(missing_currencies)}")

    currency_amounts = positions_clean.groupby("currency")["market_value_local"].sum()
    contribution_history = pd.DataFrame(index=pivoted_rates.index)

    for currency, amount in currency_amounts.items():
        contribution_history[currency] = amount / pivoted_rates[currency]

    contribution_history = contribution_history.ffill().bfill()
    contribution_history["portfolio_value_eur"] = contribution_history.sum(axis=1)
    contribution_history = contribution_history.reset_index().rename(columns={"index": "rate_date"})
    contribution_history["rate_date"] = pd.to_datetime(contribution_history["rate_date"])
    return contribution_history


def calculate_currency_correlation(rate_history: pd.DataFrame, reporting_currency: str = "EUR") -> pd.DataFrame:
    history_clean = clean_exchange_rates(rate_history)
    if history_clean.empty:
        return pd.DataFrame()

    pivoted_rates = history_clean.pivot_table(
        index="rate_date",
        columns="target_currency",
        values="exchange_rate",
        aggfunc="last",
    ).sort_index()

    if reporting_currency in pivoted_rates.columns:
        pivoted_rates = pivoted_rates.drop(columns=[reporting_currency])

    returns = pivoted_rates.pct_change().dropna(how="all")
    if returns.empty:
        return pd.DataFrame()
    return returns.corr().fillna(0.0)


def _build_rate_maps(
    latest_rates: pd.DataFrame,
    rate_history: pd.DataFrame,
    reporting_currency: str,
) -> tuple[dict[str, float], dict[str, float], str]:
    latest_clean = clean_exchange_rates(latest_rates) if not latest_rates.empty else pd.DataFrame()
    history_clean = clean_exchange_rates(rate_history)

    current_rates: dict[str, float] = {reporting_currency: 1.0}
    previous_rates: dict[str, float] = {reporting_currency: 1.0}
    latest_date = ""

    if not history_clean.empty:
        ordered_history = history_clean.sort_values(["target_currency", "rate_date"])
        latest_date = str(ordered_history["rate_date"].max())

        for currency, group in ordered_history.groupby("target_currency"):
            current_rates.setdefault(currency, float(group["exchange_rate"].iloc[-1]))
            previous_rates[currency] = float(group["exchange_rate"].iloc[-2] if len(group) > 1 else group["exchange_rate"].iloc[-1])

    if not latest_clean.empty:
        latest_date = str(latest_clean["rate_date"].max())
        for _, row in latest_clean.iterrows():
            current_rates[row["target_currency"]] = float(row["exchange_rate"])
            previous_rates.setdefault(row["target_currency"], float(row["exchange_rate"]))

    return current_rates, previous_rates, latest_date


def build_scenario_table(
    exposure_by_currency: pd.DataFrame,
    scenario_shocks: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    shocks = {currency.upper(): float(shock) for currency, shock in (scenario_shocks or {}).items()}
    scenario_rows = []

    for _, row in exposure_by_currency.iterrows():
        shock = shocks.get(row["currency"], 0.0)
        if shock <= -1.0:
            raise ValueError(f"Scenario shock for {row['currency']} must be greater than -100%.")

        stressed_rate = row["current_rate"] * (1.0 + shock)
        stressed_value_eur = row["market_value_local"] / stressed_rate
        scenario_rows.append(
            {
                "currency": row["currency"],
                "shock_pct": shock,
                "current_rate": row["current_rate"],
                "stressed_rate": stressed_rate,
                "current_value_eur": row["value_eur"],
                "stressed_value_eur": stressed_value_eur,
                "scenario_pnl_eur": stressed_value_eur - row["value_eur"],
            }
        )

    return pd.DataFrame(scenario_rows).sort_values("scenario_pnl_eur").reset_index(drop=True)


def analyze_portfolio(
    positions: pd.DataFrame,
    latest_rates: pd.DataFrame,
    rate_history: pd.DataFrame,
    reporting_currency: str = "EUR",
    confidence_level: float = 0.95,
    rolling_window: int = 20,
    holding_period_days: int = 1,
    scenario_shocks: Mapping[str, float] | None = None,
) -> dict[str, pd.DataFrame | dict[str, float | int | str]]:
    reporting_currency = reporting_currency.upper().strip()
    positions_clean = clean_portfolio_positions(positions)
    history_clean = clean_exchange_rates(rate_history)
    current_rates, previous_rates, latest_rate_date = _build_rate_maps(latest_rates, history_clean, reporting_currency)

    missing_currencies = sorted(set(positions_clean["currency"]) - set(current_rates))
    if missing_currencies:
        raise ValueError(f"Missing current exchange-rate data for: {', '.join(missing_currencies)}")

    position_analysis = positions_clean.copy()
    position_analysis["current_rate"] = position_analysis["currency"].map(current_rates)
    position_analysis["previous_rate"] = position_analysis["currency"].map(previous_rates)
    position_analysis["value_eur"] = position_analysis["market_value_local"] / position_analysis["current_rate"]
    position_analysis["previous_value_eur"] = position_analysis["market_value_local"] / position_analysis["previous_rate"]
    position_analysis["fx_pnl_1d_eur"] = position_analysis["value_eur"] - position_analysis["previous_value_eur"]

    portfolio_value_eur = float(position_analysis["value_eur"].sum())
    total_non_eur_value = float(
        position_analysis.loc[position_analysis["currency"] != reporting_currency, "value_eur"].sum()
    )
    position_analysis["portfolio_weight"] = (
        position_analysis["value_eur"] / portfolio_value_eur if portfolio_value_eur else 0.0
    )

    exposure_by_currency = (
        position_analysis.groupby("currency", as_index=False)
        .agg(
            position_count=("position_id", "count"),
            market_value_local=("market_value_local", "sum"),
            value_eur=("value_eur", "sum"),
            fx_pnl_1d_eur=("fx_pnl_1d_eur", "sum"),
            current_rate=("current_rate", "mean"),
        )
        .sort_values("value_eur", ascending=False)
        .reset_index(drop=True)
    )
    exposure_by_currency["portfolio_weight"] = (
        exposure_by_currency["value_eur"] / portfolio_value_eur if portfolio_value_eur else 0.0
    )

    portfolio_value_history = build_portfolio_value_history(
        positions=positions_clean,
        rate_history=history_clean,
        reporting_currency=reporting_currency,
    )
    history_series = portfolio_value_history.set_index("rate_date")["portfolio_value_eur"]
    portfolio_returns = calculate_series_returns(history_series)
    rolling_volatility = calculate_rolling_volatility_series(history_series, window=rolling_window)
    correlation_matrix = calculate_currency_correlation(history_clean, reporting_currency=reporting_currency)
    scenario_analysis = build_scenario_table(exposure_by_currency, scenario_shocks=scenario_shocks)

    summary = {
        "portfolio_value_eur": portfolio_value_eur,
        "fx_pnl_1d_eur": float(position_analysis["fx_pnl_1d_eur"].sum()),
        "historical_var_1d_eur": calculate_historical_var_from_returns(
            portfolio_returns,
            confidence_level=confidence_level,
            portfolio_value=portfolio_value_eur,
            holding_period_days=holding_period_days,
        ),
        "historical_var_1d_pct": (
            calculate_historical_var_from_returns(
                portfolio_returns,
                confidence_level=confidence_level,
                portfolio_value=1.0,
                holding_period_days=holding_period_days,
            )
            if portfolio_value_eur
            else 0.0
        ),
        "annualized_portfolio_volatility": calculate_annualized_volatility(
            portfolio_value_history,
            rate_column="portfolio_value_eur",
        ),
        "non_eur_share": total_non_eur_value / portfolio_value_eur if portfolio_value_eur else 0.0,
        "position_count": int(len(position_analysis)),
        "currency_count": int(position_analysis["currency"].nunique()),
        "latest_rate_date": latest_rate_date,
        "scenario_total_pnl_eur": float(scenario_analysis["scenario_pnl_eur"].sum()) if not scenario_analysis.empty else 0.0,
        "rolling_window": int(rolling_window),
        "confidence_level": float(confidence_level),
    }

    portfolio_value_history["rate_date"] = portfolio_value_history["rate_date"].dt.strftime("%Y-%m-%d")
    rolling_volatility_frame = rolling_volatility.rename("rolling_volatility").reset_index()
    rolling_volatility_frame["rate_date"] = pd.to_datetime(rolling_volatility_frame["rate_date"]).dt.strftime("%Y-%m-%d")

    return {
        "summary": summary,
        "positions": position_analysis.sort_values("value_eur", ascending=False).reset_index(drop=True),
        "currency_exposure": exposure_by_currency,
        "portfolio_value_history": portfolio_value_history,
        "rolling_volatility": rolling_volatility_frame,
        "scenario_analysis": scenario_analysis,
        "correlation_matrix": correlation_matrix,
    }
