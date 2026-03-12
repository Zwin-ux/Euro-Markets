from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dashboard.app import build_heatmap_frame


class DashboardAppTests(unittest.TestCase):
    def test_build_heatmap_frame_handles_unnamed_index(self) -> None:
        correlation_matrix = pd.DataFrame(
            [[1.0, 0.25], [0.25, 1.0]],
            columns=["USD", "GBP"],
            index=["USD", "GBP"],
        )

        melted = build_heatmap_frame(correlation_matrix)

        self.assertEqual(list(melted.columns), ["row", "column", "value"])
        self.assertEqual(len(melted), 4)
        self.assertAlmostEqual(
            float(
                melted.loc[
                    (melted["row"] == "USD") & (melted["column"] == "GBP"),
                    "value",
                ].iloc[0]
            ),
            0.25,
        )

    def test_build_heatmap_frame_returns_empty_schema_for_empty_input(self) -> None:
        melted = build_heatmap_frame(pd.DataFrame())

        self.assertEqual(list(melted.columns), ["row", "column", "value"])
        self.assertTrue(melted.empty)


if __name__ == "__main__":
    unittest.main()
