from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analytics.risk_metrics import calculate_max_drawdown, summarize_exchange_rate_history


class RiskMetricsTests(unittest.TestCase):
    def test_summarize_exchange_rate_history_returns_expected_metrics(self) -> None:
        frame = pd.DataFrame(
            [
                {"rate_date": "2026-03-07", "exchange_rate": 1.00},
                {"rate_date": "2026-03-08", "exchange_rate": 1.10},
                {"rate_date": "2026-03-09", "exchange_rate": 1.05},
                {"rate_date": "2026-03-10", "exchange_rate": 1.15},
            ]
        )

        summary = summarize_exchange_rate_history(frame)

        self.assertEqual(summary["start_date"], "2026-03-07")
        self.assertEqual(summary["end_date"], "2026-03-10")
        self.assertTrue(math.isclose(summary["latest_rate"], 1.15))
        self.assertTrue(math.isclose(summary["period_return"], 0.15))

    def test_calculate_max_drawdown_detects_peak_to_trough_drop(self) -> None:
        frame = pd.DataFrame(
            [
                {"exchange_rate": 1.00},
                {"exchange_rate": 1.12},
                {"exchange_rate": 1.01},
                {"exchange_rate": 1.18},
            ]
        )

        max_drawdown = calculate_max_drawdown(frame)

        self.assertTrue(math.isclose(max_drawdown, -0.0982142857142857))


if __name__ == "__main__":
    unittest.main()
