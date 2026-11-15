"""API tests for user preferences."""

import pytest

from tests.conftest import API, auth_headers_for

URL = f"{API}/users/me/preferences"


def test_default_preferences(client, auth_headers):
    response = client.get(URL, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["default_market"] == "NSE"
    assert body["analysis_period"] == "1Y"


def test_update_both_preferences(client, auth_headers):
    response = client.put(
        URL, headers=auth_headers, json={"default_market": "NASDAQ", "analysis_period": "5Y"}
    )
    assert response.status_code == 200
    assert response.json()["default_market"] == "NASDAQ"
    # The change is persisted, not just echoed back.
    saved = client.get(URL, headers=auth_headers).json()
    assert saved["default_market"] == "NASDAQ"
    assert saved["analysis_period"] == "5Y"


def test_partial_update_keeps_other_field(client, auth_headers):
    client.put(URL, headers=auth_headers, json={"analysis_period": "3M"})
    body = client.get(URL, headers=auth_headers).json()
    assert body["analysis_period"] == "3M"
    assert body["default_market"] == "NSE"


def test_empty_update_changes_nothing(client, auth_headers):
    response = client.put(URL, headers=auth_headers, json={})
    assert response.status_code == 200
    assert response.json()["default_market"] == "NSE"


@pytest.mark.parametrize(
    "payload",
    [
        {"default_market": "LSE"},
        {"default_market": "nse"},
        {"analysis_period": "10Y"},
        {"analysis_period": 12},
        {"unknown_field": "x"},
    ],
)
def test_invalid_preferences_are_rejected(client, auth_headers, payload):
    assert client.put(URL, headers=auth_headers, json=payload).status_code == 422


def test_preferences_are_private_to_each_user(client, auth_headers):
    bob = auth_headers_for(client, email="bob@example.com")
    client.put(URL, headers=bob, json={"default_market": "NYSE"})
    assert client.get(URL, headers=auth_headers).json()["default_market"] == "NSE"
    assert client.get(URL, headers=bob).json()["default_market"] == "NYSE"
