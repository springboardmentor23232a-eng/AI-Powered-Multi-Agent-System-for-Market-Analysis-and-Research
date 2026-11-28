
from datetime import date

import yfinance as yf

from market_data import (
    get_stock_info,
    get_financials,
    search_stocks_live,
)
from historical_analysis import analyze_historical_performance
from financial_ratios import calculate_financial_ratios


def market_group(market):
    if market in ("NSE", "BSE"):
        return "India"

    if market in ("NYSE", "NASDAQ"):
        return "US"

    return market


def normalize(value):
    return str(value or "").strip().lower()


def company_identity(ticker):
    return ticker.upper().removesuffix(".NS").removesuffix(".BO")


def discover_candidates(ticker, info, market):
    candidates = []

    # Discover companies through Yahoo Finance industry data
    industry_key = info.get("industryKey")

    if industry_key:
        try:
            companies = yf.Industry(industry_key).top_companies

            if companies is not None and not companies.empty:
                candidates.extend(companies.index.tolist())

        except Exception:
            pass

    # Additional discovery through existing stock search
    industry = info.get("industry")

    if industry:
        try:
            results = search_stocks_live(
                industry, market=market, limit=15
            )

            candidates.extend(
                stock["ticker"] for stock in results
            )

        except Exception:
            pass

    # Convert Indian listings to the selected exchange
    suffix = {
        "NSE": ".NS",
        "BSE": ".BO",
    }.get(market)

    normalized = []

    for candidate in candidates:
        candidate = str(candidate).strip().upper()

        if suffix and candidate.endswith((".NS", ".BO")):
            candidate = company_identity(candidate) + suffix

        if company_identity(candidate) == company_identity(ticker):
            continue

        if candidate not in normalized:
            normalized.append(candidate)

    return normalized


def build_company_record(stock, info, financials):
    historical = analyze_historical_performance(financials)

    records = [
        row for row in historical.get("records", [])
        if row.get("revenue") is not None
        and row["revenue"] > 0
    ]

    if not records:
        return None

    latest = max(records, key=lambda row: row["period"])

    ratio_data = calculate_financial_ratios(
        stock["ticker"], financials
    )

    ratios = ratio_data["ratios"]

    return {
        "ticker": stock["ticker"],
        "name": stock["name"],
        "market": stock["market"],
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "period": latest["period"],
        "currency": financials.get("currency"),

        "metrics": {
            "revenue_growth": latest.get("revenue_growth"),
            "gross_margin": latest.get("gross_margin"),
            "net_margin": latest.get("net_margin"),
            "ebitda_margin": latest.get("ebitda_margin"),
            "debt_equity": latest.get("debt_equity"),
            "roe": latest.get("roe"),
            "pe_ratio": ratios.get("pe_ratio"),
            "pb_ratio": ratios.get("pb_ratio"),
        },

        "ratio_reasons": ratio_data["ratio_reasons"],
    }


def comparable_period(first, second):
    try:
        first_date = date.fromisoformat(first)
        second_date = date.fromisoformat(second)

        return abs((first_date - second_date).days) <= 183

    except (ValueError, TypeError):
        return False


def generate_comparison(target, peers):
    explanations = {}

    labels = {
        "revenue_growth": "Revenue growth",
        "gross_margin": "Gross margin",
        "net_margin": "Net profit margin",
        "ebitda_margin": "EBITDA margin",
        "debt_equity": "Debt-to-equity",
        "roe": "Return on equity",
        "pe_ratio": "Price-to-earnings",
        "pb_ratio": "Price-to-book",
    }

    for key, label in labels.items():
        value = target["metrics"].get(key)

        peer_values = [
            peer["metrics"][key]
            for peer in peers
            if peer["metrics"].get(key) is not None
        ]

        if value is None or not peer_values:
            explanations[key] = {
                "message": f"Insufficient comparable data for {label}.",
                "peer_average": None,
                "peer_count": len(peer_values),
            }
            continue

        average = sum(peer_values) / len(peer_values)

        if value > average:
            position = "above"
        elif value < average:
            position = "below"
        else:
            position = "equal to"

        explanations[key] = {
            "company_value": value,
            "peer_average": round(average, 2),
            "peer_count": len(peer_values),
            "message": (
                f"{label} is {value:.2f}, which is "
                f"{position} the selected peer average "
                f"of {average:.2f}."
            ),
        }

    return explanations


def analyze_peers(ticker, max_peers=3):

    stock = get_stock_info(ticker)

    if not stock:
        return {
            "status": "unavailable",
            "message": "Unknown or unverifiable ticker.",
            "peers": [],
        }

    try:
        info = yf.Ticker(ticker).info or {}

    except Exception:
        return {
            "status": "unavailable",
            "message": "Company industry information could not be retrieved.",
            "peers": [],
        }

    industry = normalize(info.get("industry"))

    if not industry:
        return {
            "status": "unavailable",
            "message": "Company industry information is missing.",
            "peers": [],
        }

    financials = get_financials(ticker, "annual")

    target = build_company_record(
        stock, info, financials
    )

    if target is None:
        return {
            "status": "unavailable",
            "message": "The selected company has insufficient financial data.",
            "peers": [],
        }

    candidates = discover_candidates(
        ticker, info, stock["market"]
    )

    peers = []
    excluded = []

    # Limit requests to avoid excessive Yahoo Finance calls
    for candidate in candidates[:15]:

        if len(peers) >= max_peers:
            break

        try:
            peer_stock = get_stock_info(candidate)

            if not peer_stock:
                continue

            if market_group(peer_stock["market"]) != market_group(stock["market"]):
                continue

            peer_info = yf.Ticker(candidate).info or {}

            # Verify industry and country before comparison
            if normalize(peer_info.get("industry")) != industry:
                continue

            if not info.get("country"):
                continue

            if normalize(peer_info.get("country")) != normalize(info.get("country")):
                continue

            peer_financials = get_financials(
                candidate, "annual"
            )

            peer = build_company_record(
                peer_stock,
                peer_info,
                peer_financials
            )

            if peer is None:
                excluded.append({
                    "ticker": candidate,
                    "reason": "Insufficient financial data.",
                })
                continue

            if not comparable_period(
                target["period"], peer["period"]
            ):
                excluded.append({
                    "ticker": candidate,
                    "reason": "Financial reporting periods are not comparable.",
                })
                continue

            shared_metrics = [
                key for key, value in target["metrics"].items()
                if value is not None
                and peer["metrics"].get(key) is not None
            ]

            if not shared_metrics:
                excluded.append({
                    "ticker": candidate,
                    "reason": "No comparable financial metrics.",
                })
                continue

            peers.append(peer)

        except Exception:
            excluded.append({
                "ticker": candidate,
                "reason": "Peer financial data could not be processed.",
            })

    if not peers:
        return {
            "status": "unavailable",
            "message": "No suitable industry peers with comparable financial data were found.",
            "company": target,
            "peers": [],
            "excluded": excluded,
        }

    return {
        "status": "ok",
        "company": target,
        "industry": info.get("industry"),
        "sector": info.get("sector"),
        "peer_count": len(peers),
        "peers": peers,
        "comparison": generate_comparison(target, peers),
        "excluded": excluded,
        "note": (
            "Comparison is based on available industry peers. "
            "The selected peer average is not an industry-wide average. "
            "Differences in financial ratios do not automatically "
            "indicate better or worse investment opportunities."
        ),
    }
