from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.main import app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint_returns_ok(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_health_endpoint_includes_cors_headers(self) -> None:
        response = self.client.get("/health", headers={"Origin": "https://capital-risk-dashboard-production.up.railway.app"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "*")

    def test_portfolio_template_returns_sample_data(self) -> None:
        response = self.client.get("/portfolio/template")

        self.assertEqual(response.status_code, 200)
        self.assertIn("columns", response.json())
        self.assertTrue(len(response.json()["sample"]) > 0)

    def test_portfolio_analyze_serializes_analysis_result(self) -> None:
        mocked_result = {
            "summary": {"portfolio_value_eur": 100.0},
            "positions": pd.DataFrame([{"position_id": "A", "value_eur": 100.0}]),
            "currency_exposure": pd.DataFrame([{"currency": "USD", "value_eur": 100.0}]),
            "portfolio_value_history": pd.DataFrame([{"rate_date": "2026-03-11", "portfolio_value_eur": 100.0}]),
            "rolling_volatility": pd.DataFrame([{"rate_date": "2026-03-11", "rolling_volatility": 0.1}]),
            "scenario_analysis": pd.DataFrame([{"currency": "USD", "scenario_pnl_eur": -5.0}]),
            "correlation_matrix": pd.DataFrame([[1.0]], columns=["USD"], index=["USD"]),
            "market_snapshot": pd.DataFrame([{"target_currency": "USD", "exchange_rate": 1.2}]),
            "rate_history": pd.DataFrame([{"target_currency": "USD", "exchange_rate": 1.2}]),
        }

        with patch("api.main.market_service.build_portfolio_analysis", return_value=mocked_result):
            response = self.client.post(
                "/portfolio/analyze",
                json={
                    "positions": [
                        {
                            "position_id": "A",
                            "position_name": "USD Cash",
                            "currency": "USD",
                            "market_value_local": 100.0,
                        }
                    ]
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["summary"]["portfolio_value_eur"], 100.0)
        self.assertEqual(payload["positions"][0]["position_id"], "A")
        self.assertEqual(payload["correlation_matrix"]["USD"]["USD"], 1.0)


if __name__ == "__main__":
    unittest.main()
