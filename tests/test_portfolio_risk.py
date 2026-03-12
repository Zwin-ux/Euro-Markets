from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analytics.portfolio_risk import analyze_portfolio, clean_portfolio_positions


class PortfolioRiskTests(unittest.TestCase):
    def test_clean_portfolio_positions_supports_alias_columns(self) -> None:
        raw = pd.DataFrame(
            [
                {
                    "id": "FX-001",
                    "position": "USD Cash",
                    "currency": "usd",
                    "local_amount": "1000",
                    "desk": "Treasury",
                }
            ]
        )

        cleaned = clean_portfolio_positions(raw)

        self.assertEqual(cleaned.loc[0, "position_id"], "FX-001")
        self.assertEqual(cleaned.loc[0, "position_name"], "USD Cash")
        self.assertEqual(cleaned.loc[0, "currency"], "USD")
        self.assertTrue(math.isclose(cleaned.loc[0, "market_value_local"], 1000.0))

    def test_analyze_portfolio_computes_summary_and_scenario_outputs(self) -> None:
        positions = pd.DataFrame(
            [
                {
                    "position_id": "USD-1",
                    "position_name": "USD Cash",
                    "currency": "USD",
                    "market_value_local": 100.0,
                    "asset_class": "Cash",
                    "book": "Treasury",
                },
                {
                    "position_id": "EUR-1",
                    "position_name": "EUR Cash",
                    "currency": "EUR",
                    "market_value_local": 50.0,
                    "asset_class": "Cash",
                    "book": "Treasury",
                },
            ]
        )
        latest_rates = pd.DataFrame(
            [
                {
                    "base_currency": "EUR",
                    "target_currency": "USD",
                    "rate_date": "2026-03-11",
                    "exchange_rate": 1.25,
                    "frequency": "D",
                    "source": "ECB",
                },
                {
                    "base_currency": "EUR",
                    "target_currency": "EUR",
                    "rate_date": "2026-03-11",
                    "exchange_rate": 1.0,
                    "frequency": "D",
                    "source": "Synthetic",
                },
            ]
        )
        history = pd.DataFrame(
            [
                {
                    "base_currency": "EUR",
                    "target_currency": "USD",
                    "rate_date": "2026-03-09",
                    "exchange_rate": 1.20,
                    "frequency": "D",
                    "source": "ECB",
                },
                {
                    "base_currency": "EUR",
                    "target_currency": "USD",
                    "rate_date": "2026-03-10",
                    "exchange_rate": 1.22,
                    "frequency": "D",
                    "source": "ECB",
                },
                {
                    "base_currency": "EUR",
                    "target_currency": "USD",
                    "rate_date": "2026-03-11",
                    "exchange_rate": 1.25,
                    "frequency": "D",
                    "source": "ECB",
                },
                {
                    "base_currency": "EUR",
                    "target_currency": "EUR",
                    "rate_date": "2026-03-09",
                    "exchange_rate": 1.0,
                    "frequency": "D",
                    "source": "Synthetic",
                },
                {
                    "base_currency": "EUR",
                    "target_currency": "EUR",
                    "rate_date": "2026-03-10",
                    "exchange_rate": 1.0,
                    "frequency": "D",
                    "source": "Synthetic",
                },
                {
                    "base_currency": "EUR",
                    "target_currency": "EUR",
                    "rate_date": "2026-03-11",
                    "exchange_rate": 1.0,
                    "frequency": "D",
                    "source": "Synthetic",
                },
            ]
        )

        result = analyze_portfolio(
            positions=positions,
            latest_rates=latest_rates,
            rate_history=history,
            confidence_level=0.95,
            rolling_window=2,
            scenario_shocks={"USD": 0.10},
        )

        self.assertTrue(math.isclose(result["summary"]["portfolio_value_eur"], 130.0))
        self.assertTrue(math.isclose(result["summary"]["fx_pnl_1d_eur"], -1.967213114754095))
        self.assertEqual(result["summary"]["position_count"], 2)
        self.assertEqual(result["summary"]["currency_count"], 2)
        self.assertEqual(result["scenario_analysis"].loc[0, "currency"], "USD")
        self.assertLess(result["scenario_analysis"].loc[0, "scenario_pnl_eur"], 0.0)


if __name__ == "__main__":
    unittest.main()
