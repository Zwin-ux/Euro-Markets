from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database.load_data import resolve_database_url


class ResolveDatabaseUrlTests(unittest.TestCase):
    def test_defaults_to_sqlite_when_missing(self) -> None:
        self.assertEqual(resolve_database_url(None), "sqlite:///capital_risk.db")

    def test_rewrites_postgres_scheme_for_sqlalchemy_driver(self) -> None:
        self.assertEqual(
            resolve_database_url("postgres://user:pass@host:5432/dbname"),
            "postgresql+psycopg2://user:pass@host:5432/dbname",
        )

    def test_rewrites_plain_postgresql_scheme_to_psycopg2(self) -> None:
        self.assertEqual(
            resolve_database_url("postgresql://user:pass@host:5432/dbname"),
            "postgresql+psycopg2://user:pass@host:5432/dbname",
        )

    def test_preserves_explicit_driver(self) -> None:
        self.assertEqual(
            resolve_database_url("postgresql+psycopg2://user:pass@host:5432/dbname"),
            "postgresql+psycopg2://user:pass@host:5432/dbname",
        )


if __name__ == "__main__":
    unittest.main()
