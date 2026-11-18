from unittest.mock import Mock, patch
import requests
import fetch as fetch_module


def api_response(payload):
    mock = Mock()
    mock.status_code = 200
    mock.json.return_value = payload
    mock.raise_for_status.return_value = None
    return mock


@patch("fetch.requests.get")
def test_fetch_parses_valid_records(mock_get):
    mock_get.return_value = api_response({
        "bitcoin": {"usd": 65000, "usd_24h_change": 1.2},
        "ethereum": {"usd": 3000, "usd_24h_change": None},
    })
    result = fetch_module.fetch()
    assert set(result["coin"]) == {"bitcoin", "ethereum"}
    assert result["timestamp"].notna().all()


@patch("fetch.requests.get")
def test_fetch_returns_none_for_empty_payload(mock_get):
    mock_get.return_value = api_response({})
    assert fetch_module.fetch() is None


@patch("fetch.requests.get")
def test_fetch_skips_malformed_coin(mock_get):
    mock_get.return_value = api_response({
        "bitcoin": {"usd": "bad"},
        "ethereum": {"usd": 3000},
    })
    result = fetch_module.fetch()
    assert result["coin"].tolist() == ["ethereum"]


@patch("fetch.time.sleep")
@patch("fetch.requests.get")
def test_fetch_retries_server_error(mock_get, mock_sleep):
    failed = Mock()
    failed.status_code = 503
    failed.raise_for_status.side_effect = requests.HTTPError(response=failed)
    mock_get.side_effect = [failed, api_response({"bitcoin": {"usd": 1}})]
    result = fetch_module.fetch()
    assert result is not None
    assert mock_get.call_count == 2
