from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data_ingestion.clean_data import clean_exchange_rates
from data_ingestion.fetch_data import fetch_multi_currency_history
from database.load_data import load_exchange_rates
from services.market_service import get_default_target_currencies


def main() -> None:
    load_dotenv()
    lookback_days = int(os.getenv("DATA_REFRESH_LOOKBACK_DAYS", "365"))
    end = date.today()
    start = end - timedelta(days=lookback_days)
    currencies = get_default_target_currencies()

    history = clean_exchange_rates(
        fetch_multi_currency_history(
            target_currencies=currencies,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            frequency="D",
        )
    )
    load_exchange_rates(history)
    print(f"Refreshed {len(history)} exchange-rate rows for {len(currencies)} currencies.")


if __name__ == "__main__":
    main()
