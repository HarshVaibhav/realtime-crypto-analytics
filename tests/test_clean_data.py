"""Repeatable unit tests for the data-cleaning layer."""

import unittest

import pandas as pd

from clean_data import clean_data


class CleanDataTests(unittest.TestCase):
    def test_removes_invalid_prices_and_timestamps(self):
        source = pd.DataFrame({
            "coin": ["bitcoin", "ethereum", "solana", "xrp"],
            "price": [100.0, 0.0, float("inf"), 2.0],
            "chg_24h": [1.0, 2.0, 3.0, 4.0],
            "timestamp": [
                "2026-11-18T10:00:00Z",
                "2026-11-18T10:00:00Z",
                "2026-11-18T10:00:00Z",
                "not-a-date",
            ],
        })

        result = clean_data(source)

        self.assertEqual(result["coin"].tolist(), ["bitcoin"])

    def test_optional_change_can_be_missing_or_infinite(self):
        source = pd.DataFrame({
            "coin": ["bitcoin", "ethereum"],
            "price": [100.0, 200.0],
            "chg_24h": [None, float("inf")],
            "timestamp": ["2026-11-18T10:00:00Z", "2026-11-18T10:05:00Z"],
        })

        result = clean_data(source)

        self.assertEqual(len(result), 2)
        self.assertTrue(result["chg_24h"].isna().all())

    def test_normalizes_coin_and_removes_duplicate_key(self):
        source = pd.DataFrame({
            "coin": [" Bitcoin ", "bitcoin"],
            "price": [100.0, 101.0],
            "chg_24h": [1.0, 2.0],
            "timestamp": [
                "2026-11-18T10:00:00Z",
                "2026-11-18T10:00:00Z",
            ],
        })

        result = clean_data(source)

        self.assertEqual(len(result), 1)
        self.assertEqual(result.loc[0, "coin"], "bitcoin")
        self.assertEqual(result.loc[0, "price"], 101.0)

    def test_missing_required_column_raises_clear_error(self):
        source = pd.DataFrame({"coin": ["bitcoin"], "price": [100.0]})

        with self.assertRaisesRegex(ValueError, "missing required columns"):
            clean_data(source)

    def test_missing_optional_change_column_is_created_as_missing(self):
        source = pd.DataFrame({
            "coin": ["bitcoin"],
            "price": [100.0],
            "timestamp": ["2026-11-18T10:00:00Z"],
        })

        result = clean_data(source)

        self.assertEqual(len(result), 1)
        self.assertTrue(pd.isna(result.loc[0, "chg_24h"]))

    def test_none_input_raises_clear_error(self):
        with self.assertRaisesRegex(ValueError, "cannot be None"):
            clean_data(None)


if __name__ == "__main__":
    unittest.main()
