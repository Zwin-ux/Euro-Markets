from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data_ingestion.clean_data import clean_exchange_rates
from data_ingestion.fetch_data import fetch_multi_currency_history
from database.load_data import load_exchange_rates, resolve_database_url
from services.market_service import get_default_target_currencies


def describe_database_target(database_url: str) -> str:
    parsed = urlparse(database_url)
    if parsed.scheme.startswith("sqlite"):
        return f"{parsed.scheme} local file"

    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    database = parsed.path.lstrip("/") or "unknown-db"
    return f"{parsed.scheme} {host}{port}/{database}"


def main() -> None:
    load_dotenv()
    lookback_days = int(os.getenv("DATA_REFRESH_LOOKBACK_DAYS", "365"))
    end = date.today()
    start = end - timedelta(days=lookback_days)
    currencies = get_default_target_currencies()
    database_url = resolve_database_url(os.getenv("DATABASE_URL"))

    print(
        f"Starting ECB refresh for {len(currencies)} currencies "
        f"from {start.isoformat()} to {end.isoformat()} "
        f"using {describe_database_target(database_url)}.",
        flush=True,
    )

    history = clean_exchange_rates(
        fetch_multi_currency_history(
            target_currencies=currencies,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            frequency="D",
        )
    )
    load_exchange_rates(history)
    print(f"Refreshed {len(history)} exchange-rate rows for {len(currencies)} currencies.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Refresh job failed: {exc}", flush=True)
        raise
