from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data_ingestion.clean_data import clean_exchange_rates
from data_ingestion.fetch_data import fetch_multi_currency_history

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def apply_schema(engine) -> None:
    statements = [statement.strip() for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";") if statement.strip()]
    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)


def load_exchange_rates(frame: pd.DataFrame, table_name: str = "exchange_rates") -> None:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "sqlite:///capital_risk.db")
    engine = create_engine(database_url)
    cleaned = clean_exchange_rates(frame)
    if cleaned.empty:
        return
    apply_schema(engine)

    upsert_statement = text(
        f"""
        INSERT INTO {table_name} (
            base_currency,
            target_currency,
            rate_date,
            exchange_rate,
            frequency,
            source
        ) VALUES (
            :base_currency,
            :target_currency,
            :rate_date,
            :exchange_rate,
            :frequency,
            :source
        )
        ON CONFLICT (base_currency, target_currency, rate_date, frequency)
        DO UPDATE SET
            exchange_rate = excluded.exchange_rate,
            source = excluded.source,
            loaded_at = CURRENT_TIMESTAMP
        """
    )

    with engine.begin() as connection:
        connection.execute(upsert_statement, cleaned.to_dict(orient="records"))


if __name__ == "__main__":
    load_dotenv()
    end = date.today()
    start = end - timedelta(days=90)
    currencies = [
        currency.strip().upper()
        for currency in os.getenv("DEFAULT_TARGET_CURRENCIES", "USD,GBP,CHF,JPY").split(",")
        if currency.strip()
    ]
    history = fetch_multi_currency_history(
        target_currencies=currencies,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        frequency="D",
    )
    load_exchange_rates(history)
    print(f"Loaded {len(history)} ECB exchange-rate rows.")
