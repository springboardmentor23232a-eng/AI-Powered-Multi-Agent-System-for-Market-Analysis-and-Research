from app.api.stocks import get_provider
from app.main import app
from tests.fakes import FakeProvider


def auth(client):
    t = client.post("/auth/register", json={"email": "a@b.com", "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}


def test_search_requires_auth_and_finds_by_name_or_ticker(client):
    assert client.get("/stocks/search?q=tcs").status_code == 401
    h = auth(client)
    r = client.get("/stocks/search?q=tata", headers=h).json()["results"]
    assert r[0]["ticker"] == "TCS"
    assert client.get("/stocks/search?q=hdfc", headers=h).json()["results"][0]["ticker"] == "HDFCBANK"


def test_prices_endpoint(client):
    app.dependency_overrides[get_provider] = lambda: FakeProvider()
    try:
        h = auth(client)
        r = client.get("/stocks/TCS/prices?period=1y", headers=h)
        assert r.status_code == 200
        body = r.json()
        assert body["symbol"] == "TCS.NS" and body["rows"] and body["source"]["content_hash"]
        assert client.get("/stocks/NOPE/prices", headers=h).status_code == 404
    finally:
        app.dependency_overrides.pop(get_provider, None)


def test_provider_outage_returns_502(client):
    app.dependency_overrides[get_provider] = lambda: FakeProvider(fail=True)
    try:
        assert client.get("/stocks/INFY/prices", headers=auth(client)).status_code == 502
    finally:
        app.dependency_overrides.pop(get_provider, None)
