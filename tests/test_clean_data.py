import pandas as pd
import pytest
from clean_data import clean_data


def frame():
    return pd.DataFrame({
        "coin": [" Bitcoin ", "ethereum", "solana"],
        "price": [100.0, 200.0, 300.0],
        "chg_24h": [1.0, None, -2.0],
        "timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T00:05:00Z", "2026-01-01T00:10:00Z"],
    })


def test_normalizes_coin_and_timestamp_to_utc():
    result = clean_data(frame())
    assert result.loc[0, "coin"] == "bitcoin"
    assert str(result["timestamp"].dt.tz) == "UTC"


def test_preserves_missing_optional_change():
    result = clean_data(frame())
    assert pd.isna(result.loc[1, "chg_24h"])


def test_removes_invalid_price_and_timestamp():
    data = frame()
    data.loc[0, "price"] = -1
    data.loc[1, "timestamp"] = "not-a-date"
    result = clean_data(data)
    assert result["coin"].tolist() == ["solana"]


def test_duplicate_coin_timestamp_keeps_last():
    data = frame()
    duplicate = data.iloc[[0]].copy()
    duplicate.loc[:, "price"] = 123
    result = clean_data(pd.concat([data, duplicate], ignore_index=True))
    bitcoin = result[result["coin"] == "bitcoin"]
    assert len(bitcoin) == 1
    assert bitcoin.iloc[0]["price"] == 123


def test_missing_required_column_raises():
    with pytest.raises(ValueError, match="Missing required columns"):
        clean_data(frame().drop(columns=["coin"]))


def test_rejects_infinite_price():
    data = frame()
    data.loc[0, "price"] = float("inf")
    result = clean_data(data)
    assert "bitcoin" not in result["coin"].tolist()
