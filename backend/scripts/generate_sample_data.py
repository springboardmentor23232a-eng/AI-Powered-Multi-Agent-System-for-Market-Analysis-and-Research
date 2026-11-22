"""Builds the model (sample) dataset in backend/data/sample/.

The data is synthetic. Prices come from a seeded random walk, and the profile
and financial figures are invented for testing. A handful of rows are broken on
purpose so the validation step can be tested against known defects.

Run from the backend folder:  python scripts/generate_sample_data.py
"""
import json
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data" / "sample"
DATES = pd.bdate_range("2021-11-15", "2026-11-13")

# key, name, sector, industry, country, currency, start price, drift, volatility, base volume, revenue, shares, listings
COMPANIES = [
    ("RELIANCE", "Reliance Industries Limited", "Energy", "Oil & Gas Refining & Marketing", "India", "INR", 1300, 0.10, 0.24, 6_000_000, 9.0e12, 6.76e9, [("RELIANCE.NS", "NSE"), ("RELIANCE.BO", "BSE")]),
    ("TCS", "Tata Consultancy Services Limited", "Technology", "Information Technology Services", "India", "INR", 3500, 0.08, 0.20, 2_000_000, 2.4e12, 3.6e9, [("TCS.NS", "NSE"), ("TCS.BO", "BSE")]),
    ("INFY", "Infosys Limited", "Technology", "Information Technology Services", "India", "INR", 1500, 0.07, 0.24, 5_000_000, 1.5e12, 4.1e9, [("INFY.NS", "NSE"), ("INFY.BO", "BSE")]),
    ("HDFCBANK", "HDFC Bank Limited", "Financial Services", "Banks - Regional", "India", "INR", 1600, 0.09, 0.21, 9_000_000, 2.0e12, 7.6e9, [("HDFCBANK.NS", "NSE"), ("HDFCBANK.BO", "BSE")]),
    ("ICICIBANK", "ICICI Bank Limited", "Financial Services", "Banks - Regional", "India", "INR", 1100, 0.12, 0.23, 12_000_000, 1.6e12, 7.0e9, [("ICICIBANK.NS", "NSE")]),
    ("AAPL", "Apple Inc.", "Technology", "Consumer Electronics", "United States", "USD", 180, 0.14, 0.27, 60_000_000, 3.9e11, 15.5e9, [("AAPL", "NASDAQ")]),
    ("MSFT", "Microsoft Corporation", "Technology", "Software - Infrastructure", "United States", "USD", 400, 0.15, 0.25, 25_000_000, 2.3e11, 7.4e9, [("MSFT", "NASDAQ")]),
    ("GOOGL", "Alphabet Inc.", "Communication Services", "Internet Content & Information", "United States", "USD", 160, 0.12, 0.29, 30_000_000, 3.0e11, 12.3e9, [("GOOGL", "NASDAQ")]),
    ("JPM", "JPMorgan Chase & Co.", "Financial Services", "Banks - Diversified", "United States", "USD", 200, 0.10, 0.23, 9_000_000, 1.6e11, 2.8e9, [("JPM", "NYSE")]),
    ("KO", "The Coca-Cola Company", "Consumer Defensive", "Beverages - Non-Alcoholic", "United States", "USD", 60, 0.05, 0.15, 14_000_000, 4.6e10, 4.3e9, [("KO", "NYSE")]),
    ("XOM", "Exxon Mobil Corporation", "Energy", "Oil & Gas Integrated", "United States", "USD", 110, 0.06, 0.26, 15_000_000, 3.9e11, 4.0e9, [("XOM", "NYSE")]),
]

# Known defects, as (kind, position counted back from the last row).
DEFECTS = {
    "TCS.BO": [("missing_close", -6), ("missing_close", -17), ("duplicate", -26), ("high_lt_low", -38)],
    "INFY.BO": [("missing_open", -9), ("missing_volume", -14), ("missing_volume", -29)],
    "RELIANCE.BO": [("zero_close", -11), ("close_above_high", -33)],
    "HDFCBANK.NS": [("duplicate", -10), ("duplicate", -40)],
    "AAPL": [("missing_volume", -7), ("missing_volume", -21), ("missing_volume", -35)],
}
CHECK_OF = {
    "missing_close": "missing_prices", "missing_open": "missing_prices",
    "duplicate": "duplicate_dates", "zero_close": "non_positive",
    "high_lt_low": "inconsistent_ohlc", "close_above_high": "inconsistent_ohlc",
    "missing_volume": "missing_volume",
}


def base_series(key, price0, drift, vol, base_volume):
    rng = np.random.default_rng(zlib.crc32(key.encode()))
    n = len(DATES)
    close = price0 * np.exp(np.cumsum(rng.normal(drift / 252, vol / np.sqrt(252), n)))
    prev = np.concatenate([[price0], close[:-1]])
    open_ = prev * (1 + rng.normal(0, 0.004, n))
    hi_pad = 1 + np.abs(rng.normal(0, 0.006, n))
    lo_pad = 1 - np.abs(rng.normal(0, 0.006, n))
    volume = base_volume * rng.lognormal(0, 0.35, n)
    return open_, close, hi_pad, lo_pad, volume


def listing_frame(symbol, key, series, primary):
    open_, close, hi_pad, lo_pad, volume = series
    rng = np.random.default_rng(zlib.crc32(symbol.encode()))
    f = np.ones(len(DATES)) if primary else 1 + rng.normal(0, 0.0006, len(DATES))
    o, c = np.round(open_ * f, 2), np.round(close * f, 2)
    h = np.round(np.maximum(o, c) * hi_pad, 2)
    lo = np.round(np.minimum(o, c) * lo_pad, 2)
    vol = np.round(volume * (1 if primary else 0.15)).astype("int64")
    return pd.DataFrame({"symbol": symbol, "date": DATES.strftime("%Y-%m-%d"), "open": o, "high": h, "low": lo, "close": c, "volume": pd.array(vol, dtype="Int64")})


def inject(df, symbol):
    expected, extra = {}, []
    for kind, pos in DEFECTS.get(symbol, []):
        i = len(df) + pos
        row = df.iloc[i]
        if kind == "missing_close":
            df.iloc[i, df.columns.get_loc("close")] = np.nan
        elif kind == "missing_open":
            df.iloc[i, df.columns.get_loc("open")] = np.nan
        elif kind == "missing_volume":
            df.iloc[i, df.columns.get_loc("volume")] = pd.NA
        elif kind == "zero_close":
            df.iloc[i, df.columns.get_loc("close")] = 0.0
        elif kind == "high_lt_low":
            assert row["high"] > row["low"]
            df.iloc[i, df.columns.get_loc("high")] = row["low"]
            df.iloc[i, df.columns.get_loc("low")] = row["high"]
        elif kind == "close_above_high":
            df.iloc[i, df.columns.get_loc("close")] = round(row["high"] * 1.05, 2)
        elif kind == "duplicate":
            extra.append(row.copy())
        expected[CHECK_OF[kind]] = expected.get(CHECK_OF[kind], 0) + 1
    if extra:
        df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True).sort_values("date", kind="stable", ignore_index=True)
    return df, expected


def statements(co, rng):
    key, name, sector, industry, country, currency, p0, drift, vol, bv, revenue, shares, listings = co
    india = country == "India"
    years = [f"{y}-03-31" if india else f"{y}-12-31" for y in (2022, 2023, 2024, 2025)]
    growth = 0.09 if sector != "Consumer Defensive" else 0.04
    cogs_r = {"Technology": 0.58, "Energy": 0.78, "Consumer Defensive": 0.42}.get(sector, 0.45)
    opex_r = {"Technology": 0.17, "Energy": 0.08, "Consumer Defensive": 0.28}.get(sector, 0.22)
    out = {"income_statement": {}, "balance_sheet": {}, "cash_flow": {}}
    for i, fy in enumerate(years):
        rev = revenue / (1 + growth) ** (3 - i) * (1 + rng.normal(0, 0.015))
        cogs = rev * cogs_r * (1 + rng.normal(0, 0.01))
        gross = rev - cogs
        opex = rev * opex_r * (1 + rng.normal(0, 0.02))
        op = gross - opex
        interest = rev * 0.012
        pretax = op - interest
        tax = max(pretax, 0) * 0.24
        net = pretax - tax
        assets = rev * 1.35 * (1 + rng.normal(0, 0.02))
        liab = assets * 0.58
        out["income_statement"][fy] = {
            "Total Revenue": round(rev), "Cost Of Revenue": round(cogs), "Gross Profit": round(gross),
            "Operating Expense": round(opex), "Operating Income": round(op), "Interest Expense": round(interest),
            "Pretax Income": round(pretax), "Tax Provision": round(tax), "Net Income": round(net),
            "Basic EPS": round(net / shares, 2),
        }
        out["balance_sheet"][fy] = {
            "Total Assets": round(assets), "Total Liabilities": round(liab), "Stockholders Equity": round(assets - liab),
            "Cash And Cash Equivalents": round(assets * 0.09), "Total Debt": round(liab * 0.35),
        }
        ocf = net * (1.18 + rng.normal(0, 0.03))
        capex = -rev * 0.055
        inv = capex * 1.25
        out["cash_flow"][fy] = {
            "Operating Cash Flow": round(ocf), "Investing Cash Flow": round(inv), "Financing Cash Flow": round(-(ocf + inv) * 0.5),
            "Capital Expenditure": round(capex), "Free Cash Flow": round(ocf + capex),
        }
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames, profiles, financials, manifest = [], {}, {}, {}
    for co in COMPANIES:
        key, name, sector, industry, country, currency, p0, drift, vol, bv, revenue, shares, listings = co
        series = base_series(key, p0, drift, vol, bv)
        stm = statements(co, np.random.default_rng(zlib.crc32(("fin" + key).encode())))
        for n, (symbol, market) in enumerate(listings):
            df, expected = inject(listing_frame(symbol, key, series, primary=(n == 0)), symbol)
            frames.append(df)
            if expected:
                manifest[symbol] = expected
            profiles[symbol] = {"name": name, "exchange": market, "market": market, "currency": currency, "country": country, "sector": sector, "industry": industry}
            financials[symbol] = stm
    prices = pd.concat(frames, ignore_index=True)
    prices.to_csv(OUT / "prices.csv", index=False, float_format="%.2f")
    (OUT / "profiles.json").write_text(json.dumps(profiles, indent=1))
    (OUT / "financials.json").write_text(json.dumps(financials, indent=1))
    (OUT / "defects.json").write_text(json.dumps(manifest, indent=1))
    print(f"{len(profiles)} symbols, {len(prices)} price rows, defects in: {', '.join(manifest)}")


if __name__ == "__main__":
    main()
