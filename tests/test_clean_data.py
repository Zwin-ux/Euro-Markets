from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data_ingestion.clean_data import clean_exchange_rates


class CleanExchangeRatesTests(unittest.TestCase):
    def test_clean_exchange_rates_normalizes_and_deduplicates(self) -> None:
        raw = pd.DataFrame(
            [
                {
                    "base_currency": "eur",
                    "target_currency": "usd",
                    "rate_date": "2026-03-11",
                    "exchange_rate": "1.0863",
                    "frequency": "d",
                    "source": "ECB",
                },
                {
                    "base_currency": "eur",
                    "target_currency": "usd",
                    "rate_date": "2026-03-11",
                    "exchange_rate": "1.0863",
                    "frequency": "d",
                    "source": "ECB",
                },
            ]
        )

        cleaned = clean_exchange_rates(raw)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.loc[0, "base_currency"], "EUR")
        self.assertEqual(cleaned.loc[0, "target_currency"], "USD")
        self.assertEqual(cleaned.loc[0, "frequency"], "D")


if __name__ == "__main__":
    unittest.main()
