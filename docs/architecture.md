# Architecture

## Overview

The platform is organized as a reusable FX risk stack:

1. `data_ingestion/fetch_data.py` calls the Euro Rates API for latest rates, currency catalogs, and historical ECB exchange-rate series.
2. `data_ingestion/clean_data.py` normalizes the upstream payload into a consistent exchange-rate table.
3. `services/market_service.py` orchestrates market fetches, synthetic EUR baseline rows, and portfolio analysis requests.
4. `analytics/risk_metrics.py` handles generic return and risk calculations.
5. `analytics/portfolio_risk.py` computes portfolio EUR value, exposure, FX P&L, historical VaR, rolling volatility, and scenario analysis.
6. `api/main.py` exposes the service layer through FastAPI.
7. `dashboard/app.py` presents the same analytics in Streamlit for interactive use.
8. `database/` and `scripts/refresh_exchange_rates.py` support local persistence and repeatable refreshes.

## Data Flow

`ECB -> Euro Rates API -> fetch_data.py -> clean_data.py -> services/market_service.py -> analytics -> API / dashboard / database`

## Portfolio Model

The portfolio upload contract is intentionally simple:

- `position_id`
- `position_name`
- `currency`
- `market_value_local`
- optional: `asset_class`
- optional: `book`

This keeps the project easy to demo while still enabling meaningful FX analytics over multi-currency holdings.

## Risk Metrics

The current portfolio layer computes:

- current EUR portfolio value
- currency-level EUR exposure
- 1-day FX P&L based on the latest and previous rates
- historical 1-day VaR from portfolio return history
- rolling annualized volatility
- simple scenario analysis from user-defined shocks
- currency return correlation matrix

## Technical Notes

- The reporting currency is currently fixed to `EUR`, which fits the ECB reference-rate model.
- Synthetic `EUR/EUR = 1.0` rows are injected for portfolio and history alignment.
- Latest snapshots are fetched one currency at a time because the multi-currency `/api/rates` response was inconsistent during live validation on 2026-03-11.
- SQLite is used for local persistence; the loader performs upserts on the `exchange_rates` primary key.
- Docker and GitHub Actions are included so the project can be run and validated outside a local workstation.
