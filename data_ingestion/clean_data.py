from __future__ import annotations

import pandas as pd

EXPECTED_COLUMNS = [
    "base_currency",
    "target_currency",
    "rate_date",
    "exchange_rate",
    "frequency",
    "source",
]


def clean_exchange_rates(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    cleaned = frame.copy()
    cleaned.columns = [column.strip().lower().replace(" ", "_") for column in cleaned.columns]

    missing_columns = [column for column in EXPECTED_COLUMNS if column not in cleaned.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    cleaned["base_currency"] = cleaned["base_currency"].astype(str).str.upper().str.strip()
    cleaned["target_currency"] = cleaned["target_currency"].astype(str).str.upper().str.strip()
    cleaned["rate_date"] = pd.to_datetime(cleaned["rate_date"], errors="raise").dt.strftime("%Y-%m-%d")
    cleaned["exchange_rate"] = pd.to_numeric(cleaned["exchange_rate"], errors="raise")
    cleaned["frequency"] = cleaned["frequency"].astype(str).str.upper().str.strip()
    cleaned["source"] = cleaned["source"].astype(str).str.strip()

    cleaned = cleaned.dropna(subset=["base_currency", "target_currency", "rate_date", "exchange_rate"])
    cleaned = cleaned.sort_values(["target_currency", "rate_date"]).drop_duplicates(
        subset=["base_currency", "target_currency", "rate_date", "frequency"],
        keep="last",
    )
    return cleaned[EXPECTED_COLUMNS].reset_index(drop=True)


if __name__ == "__main__":
    sample = pd.DataFrame(
        [
            {
                "base_currency": "eur",
                "target_currency": "usd",
                "rate_date": "2026-03-11",
                "exchange_rate": 1.0864,
                "frequency": "d",
                "source": "European Central Bank (ECB)",
            },
            {
                "base_currency": "eur",
                "target_currency": "usd",
                "rate_date": "2026-03-11",
                "exchange_rate": 1.0864,
                "frequency": "d",
                "source": "European Central Bank (ECB)",
            },
        ]
    )
    print(clean_exchange_rates(sample))
