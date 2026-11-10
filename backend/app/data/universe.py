"""Fixed research universe: 20 liquid NSE large caps."""

UNIVERSE: dict[str, str] = {
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Services",
    "HDFCBANK": "HDFC Bank",
    "INFY": "Infosys",
    "ICICIBANK": "ICICI Bank",
    "HINDUNILVR": "Hindustan Unilever",
    "ITC": "ITC Limited",
    "SBIN": "State Bank of India",
    "BHARTIARTL": "Bharti Airtel",
    "KOTAKBANK": "Kotak Mahindra Bank",
    "LT": "Larsen & Toubro",
    "AXISBANK": "Axis Bank",
    "ASIANPAINT": "Asian Paints",
    "MARUTI": "Maruti Suzuki India",
    "SUNPHARMA": "Sun Pharmaceutical Industries",
    "TITAN": "Titan Company",
    "BAJFINANCE": "Bajaj Finance",
    "NESTLEIND": "Nestle India",
    "WIPRO": "Wipro",
    "ULTRACEMCO": "UltraTech Cement",
}


def search_universe(query: str, limit: int = 10) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    hits = [
        {"ticker": t, "name": n, "market": "NSE"}
        for t, n in UNIVERSE.items()
        if q in t.lower() or q in n.lower()
    ]
    hits.sort(key=lambda h: (not h["ticker"].lower().startswith(q), h["ticker"]))
    return hits[:limit]
