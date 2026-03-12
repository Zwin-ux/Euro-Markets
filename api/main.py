from __future__ import annotations

from datetime import date

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

import services.market_service as market_service
from api.schemas import PortfolioAnalysisRequest
from data_ingestion.clean_data import clean_exchange_rates
from data_ingestion.fetch_data import fetch_historical_rates

app = FastAPI(
    title="Capital Risk Intelligence API",
    version="1.0.0",
    description="ECB-backed FX market intelligence and portfolio risk analytics.",
)


def _serialize_frame(frame: pd.DataFrame) -> list[dict]:
    serializable = frame.copy()
    for column in serializable.columns:
        if pd.api.types.is_datetime64_any_dtype(serializable[column]):
            serializable[column] = serializable[column].dt.strftime("%Y-%m-%d")
    return serializable.to_dict(orient="records")


def _serialize_analysis_result(result: dict) -> dict:
    serialized = {}
    for key, value in result.items():
        if isinstance(value, pd.DataFrame):
            if key == "correlation_matrix":
                serialized[key] = value.round(6).to_dict()
            else:
                serialized[key] = _serialize_frame(value)
        else:
            serialized[key] = value
    return serialized


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "source": "European Central Bank (ECB) via Euro Rates API",
        "date": date.today().isoformat(),
    }


@app.get("/currencies")
def list_supported_currencies() -> dict[str, list[dict]]:
    return {"currencies": _serialize_frame(market_service.get_supported_currency_catalog())}


@app.get("/portfolio/template")
def get_portfolio_template() -> dict[str, list[dict] | list[str]]:
    template = market_service.load_sample_portfolio()
    return {
        "columns": template.columns.tolist(),
        "sample": _serialize_frame(template),
    }


@app.get("/rates/latest")
def get_latest_rates(
    currencies: str = Query("USD,GBP,CHF,JPY", description="Comma-separated currency symbols"),
) -> dict[str, list[dict]]:
    try:
        currency_list = [currency.strip().upper() for currency in currencies.split(",") if currency.strip()]
        snapshot = market_service.get_latest_snapshot(currency_list)
        return {"data": _serialize_frame(snapshot)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/rates/history")
def get_rate_history(
    currency: str = Query(..., description="Target currency symbol"),
    start: str = Query(..., description="Start date in YYYY-MM-DD"),
    end: str = Query(..., description="End date in YYYY-MM-DD"),
    frequency: str = Query("D", pattern="^(D|M|Q|A)$"),
) -> dict[str, list[dict]]:
    try:
        history = clean_exchange_rates(fetch_historical_rates(currency, start, end, frequency))
        return {"data": _serialize_frame(history)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/market-monitor")
def get_market_monitor(
    focus_currency: str = Query("USD"),
    currencies: str = Query("USD,GBP,CHF,JPY,AUD,CAD"),
    lookback_days: int = Query(180, ge=30, le=730),
    frequency: str = Query("D", pattern="^(D|M|Q|A)$"),
) -> dict:
    try:
        currency_list = [currency.strip().upper() for currency in currencies.split(",") if currency.strip()]
        result = market_service.build_market_monitor(
            focus_currency=focus_currency,
            currencies=currency_list,
            lookback_days=lookback_days,
            frequency=frequency,
        )
        return _serialize_analysis_result(result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/portfolio/analyze")
def analyze_portfolio(request: PortfolioAnalysisRequest) -> dict:
    try:
        positions = pd.DataFrame([position.model_dump() for position in request.positions])
        result = market_service.build_portfolio_analysis(
            positions=positions,
            lookback_days=request.lookback_days,
            confidence_level=request.confidence_level,
            rolling_window=request.rolling_window,
            frequency=request.frequency,
            scenario_shocks=request.scenario_shocks,
        )
        return _serialize_analysis_result(result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
