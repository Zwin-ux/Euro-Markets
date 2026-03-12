# Capital Risk Intelligence

Capital Risk Intelligence is an ECB-backed FX risk platform for market monitoring and portfolio analysis. It pulls euro foreign exchange reference rates through the free Euro Rates API, normalizes the data, exposes a FastAPI backend, and delivers a Streamlit dashboard with portfolio upload, EUR exposure breakdowns, rolling volatility, historical VaR, and scenario analysis.

## Why This Project Exists

The goal is to show end-to-end engineering ownership instead of a single notebook or chart:

- ingest external market data reliably
- normalize and store it for reuse
- compute portfolio-aware risk metrics
- expose the analysis through an API
- ship a dashboard for non-technical users
- package the whole thing with tests, Docker, and CI

## Features

- ECB-backed EUR exchange-rate history and latest snapshots
- portfolio CSV upload with input cleaning and validation
- EUR exposure analysis by currency, book, and asset class filters
- 1-day FX P&L, historical VaR, and annualized volatility
- scenario analysis with custom currency shocks
- FastAPI endpoints for market and portfolio analytics
- SQLite persistence and refresh script for local rate storage

## Project Structure

- `analytics/`: FX and portfolio risk calculations
- `api/`: FastAPI application and request models
- `dashboard/`: Streamlit dashboard
- `data/`: sample portfolio input
- `data_ingestion/`: Euro Rates API fetchers and data cleaning
- `database/`: schema and load logic
- `docs/`: architecture notes
- `scripts/`: utility scripts
- `services/`: shared market and portfolio service layer
- `tests/`: unit and API tests

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python -m streamlit run dashboard\app.py
```

PowerShell activation is optional. If you want the API as well:

```powershell
.\.venv\Scripts\python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Deployment

GitHub Pages is not a fit for the app itself. GitHub Pages is a static hosting service for HTML, CSS, and JavaScript, while this project needs Python processes for Streamlit and FastAPI.

Use GitHub Pages only if you want a static landing page or documentation site that links to the live app.

For the actual product, the repo now includes `render.yaml` so you can deploy:

- a public FastAPI service
- a public Streamlit dashboard
- a scheduled refresh job
- a managed Postgres database

Render setup:

1. Push this repo to GitHub.
2. In Render, create a new Blueprint from the repository.
3. Render will read `render.yaml` and provision the services and database.
4. Add custom domains in Render after the first deploy if you want branded URLs.

## Docker

```powershell
docker compose up --build
```

- Dashboard: `http://localhost:8501`
- API docs: `http://localhost:8000/docs`

## Environment

- `DATABASE_URL`: local database connection string
- `EURO_RATES_API_BASE_URL`: defaults to `https://api.euroratesapi.dev`
- `DEFAULT_TARGET_CURRENCIES`: default currencies for dashboard snapshots and refresh jobs, for example `USD,GBP,CHF,JPY,AUD,CAD`
- `DATA_REFRESH_LOOKBACK_DAYS`: history window used by `scripts/refresh_exchange_rates.py`
- `REQUEST_TIMEOUT_SECONDS`: HTTP timeout for upstream API requests

## API Endpoints

- `GET /health`
- `GET /currencies`
- `GET /rates/latest`
- `GET /rates/history`
- `GET /market-monitor`
- `GET /portfolio/template`
- `POST /portfolio/analyze`

## Portfolio CSV Contract

Required columns:

- `position_id`
- `position_name`
- `currency`
- `market_value_local`

Optional columns:

- `asset_class`
- `book`

Sample data is available in `data/sample_portfolio.csv`.

## Data Refresh

Refresh the local SQLite store with default currencies:

```powershell
.\.venv\Scripts\python scripts\refresh_exchange_rates.py
```

## Testing

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

The GitHub Actions workflow in `.github/workflows/ci.yml` runs compilation checks and the test suite on push and pull request.

## Notes On The Upstream API

- Source documentation: `https://euroratesapi.dev/documentation`
- OpenAPI spec: `https://api.euroratesapi.dev/docs?api-docs.json`
- Source market data: ECB euro foreign exchange reference rates

During live validation on 2026-03-11, the multi-currency `/api/rates?from=EUR&to=...` response returned mismatched values for some requested currency pairs. For correctness, latest snapshots in this project are fetched one currency at a time.
