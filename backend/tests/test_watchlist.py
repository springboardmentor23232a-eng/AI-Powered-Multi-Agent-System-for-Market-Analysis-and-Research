"""API tests for saved stocks (watchlist)."""

import pytest

from app.services import watchlist_service
from tests.conftest import API, auth_headers_for

URL = f"{API}/watchlist"


def add(client, headers, ticker="RELIANCE", market="NSE"):
    return client.post(URL, headers=headers, json={"ticker": ticker, "market": market})


def test_watchlist_starts_empty(client, auth_headers):
    response = client.get(URL, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_add_stock(client, auth_headers):
    response = add(client, auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["ticker"] == "RELIANCE"
    assert body["market"] == "NSE"
    assert isinstance(body["saved_stock_id"], int)


def test_ticker_is_trimmed_and_uppercased(client, auth_headers):
    assert add(client, auth_headers, ticker="  tcs ").json()["ticker"] == "TCS"


@pytest.mark.parametrize("ticker", ["BRK.B", "BAJAJ-AUTO", "M&M", "500325"])
def test_real_world_ticker_formats_are_accepted(client, auth_headers, ticker):
    assert add(client, auth_headers, ticker=ticker).status_code == 201


@pytest.mark.parametrize("ticker", ["", "   ", "AB CD", "DROP;TABLE", "X" * 21, ".ABC", "<b>"])
def test_invalid_tickers_are_rejected(client, auth_headers, ticker):
    assert add(client, auth_headers, ticker=ticker).status_code == 422


def test_invalid_market_is_rejected(client, auth_headers):
    assert add(client, auth_headers, market="LSE").status_code == 422


def test_duplicate_stock_is_rejected(client, auth_headers):
    add(client, auth_headers)
    response = add(client, auth_headers, ticker="reliance")
    assert response.status_code == 409


def test_same_ticker_on_different_market_is_allowed(client, auth_headers):
    assert add(client, auth_headers, market="NSE").status_code == 201
    assert add(client, auth_headers, market="BSE").status_code == 201


def test_list_is_newest_first(client, auth_headers):
    for ticker in ["INFY", "TCS", "HDFCBANK"]:
        add(client, auth_headers, ticker=ticker)
    tickers = [s["ticker"] for s in client.get(URL, headers=auth_headers).json()]
    assert tickers == ["HDFCBANK", "TCS", "INFY"]


def test_remove_stock(client, auth_headers):
    stock_id = add(client, auth_headers).json()["saved_stock_id"]
    assert client.delete(f"{URL}/{stock_id}", headers=auth_headers).status_code == 204
    assert client.get(URL, headers=auth_headers).json() == []


def test_remove_missing_stock_returns_404(client, auth_headers):
    assert client.delete(f"{URL}/99999", headers=auth_headers).status_code == 404


def test_users_cannot_see_or_delete_each_others_stocks(client, auth_headers):
    bob = auth_headers_for(client, email="bob@example.com")
    alice_stock = add(client, auth_headers, ticker="INFY").json()["saved_stock_id"]
    add(client, bob, ticker="AAPL", market="NASDAQ")

    assert [s["ticker"] for s in client.get(URL, headers=bob).json()] == ["AAPL"]
    # Bob tries to delete Alice's stock: looks like "not found" to him, and it survives.
    assert client.delete(f"{URL}/{alice_stock}", headers=bob).status_code == 404
    assert [s["ticker"] for s in client.get(URL, headers=auth_headers).json()] == ["INFY"]


def test_both_users_can_save_the_same_stock(client, auth_headers):
    bob = auth_headers_for(client, email="bob@example.com")
    assert add(client, auth_headers).status_code == 201
    assert add(client, bob).status_code == 201


def test_watchlist_limit(client, auth_headers, monkeypatch):
    monkeypatch.setattr(watchlist_service, "MAX_SAVED_STOCKS_PER_USER", 2)
    assert add(client, auth_headers, ticker="A").status_code == 201
    assert add(client, auth_headers, ticker="B").status_code == 201
    response = add(client, auth_headers, ticker="C")
    assert response.status_code == 422
    assert "at most 2" in response.json()["detail"]
