from __future__ import annotations

import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def calculate_series_returns(series: pd.Series) -> pd.Series:
    return series.astype(float).pct_change().dropna()


def calculate_returns(frame: pd.DataFrame, rate_column: str = "exchange_rate") -> pd.Series:
    return calculate_series_returns(frame[rate_column])


def calculate_volatility(frame: pd.DataFrame, rate_column: str = "exchange_rate") -> float:
    returns = calculate_returns(frame, rate_column=rate_column)
    return float(returns.std()) if not returns.empty else 0.0


def calculate_annualized_volatility(
    frame: pd.DataFrame,
    rate_column: str = "exchange_rate",
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    return calculate_volatility(frame, rate_column=rate_column) * (periods_per_year**0.5)


def calculate_rolling_volatility_series(
    series: pd.Series,
    window: int = 20,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> pd.Series:
    if window < 2:
        raise ValueError("Rolling window must be at least 2.")
    returns = calculate_series_returns(series)
    if returns.empty:
        return pd.Series(dtype="float64", name="rolling_volatility")
    rolling = returns.rolling(window=window, min_periods=min(window, 5)).std()
    return rolling * (periods_per_year**0.5)


def calculate_historical_var_from_returns(
    returns: pd.Series,
    confidence_level: float = 0.95,
    portfolio_value: float = 1.0,
    holding_period_days: int = 1,
) -> float:
    if not 0 < confidence_level < 1:
        raise ValueError("Confidence level must be between 0 and 1.")
    if holding_period_days < 1:
        raise ValueError("Holding period must be at least 1 day.")
    if returns.empty:
        return 0.0

    loss_fraction = max(0.0, -float(returns.quantile(1.0 - confidence_level)))
    return loss_fraction * portfolio_value * (holding_period_days**0.5)


def calculate_max_drawdown(frame: pd.DataFrame, rate_column: str = "exchange_rate") -> float:
    series = frame[rate_column].astype(float)
    if series.empty:
        return 0.0
    running_max = series.cummax()
    drawdown = (series / running_max) - 1.0
    return float(drawdown.min())


def summarize_exchange_rate_history(frame: pd.DataFrame, rate_column: str = "exchange_rate") -> dict[str, float | str]:
    ordered = frame.sort_values("rate_date").reset_index(drop=True)
    if ordered.empty:
        raise ValueError("Exchange-rate history is empty.")

    start_rate = float(ordered.iloc[0][rate_column])
    latest_rate = float(ordered.iloc[-1][rate_column])
    period_return = ((latest_rate / start_rate) - 1.0) if start_rate else 0.0

    return {
        "start_date": str(ordered.iloc[0]["rate_date"]),
        "end_date": str(ordered.iloc[-1]["rate_date"]),
        "start_rate": start_rate,
        "latest_rate": latest_rate,
        "period_return": period_return,
        "daily_volatility": calculate_volatility(ordered, rate_column=rate_column),
        "annualized_volatility": calculate_annualized_volatility(ordered, rate_column=rate_column),
        "max_drawdown": calculate_max_drawdown(ordered, rate_column=rate_column),
    }
