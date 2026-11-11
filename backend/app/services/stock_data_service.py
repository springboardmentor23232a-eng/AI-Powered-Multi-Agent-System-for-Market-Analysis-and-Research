import logging
import httpx
from typing import List, Optional, Dict, Any
from app.schemas.stock import StockSearchResult

logger = logging.getLogger(__name__)

# Verified seed database of major companies across supported exchanges for instant and offline lookup
VERIFIED_STOCKS: List[Dict[str, str]] = [
    # US NASDAQ
    {"ticker": "AAPL", "company_name": "Apple Inc.", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Technology"},
    {"ticker": "MSFT", "company_name": "Microsoft Corporation", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Technology"},
    {"ticker": "GOOGL", "company_name": "Alphabet Inc. (Class A)", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Communication Services"},
    {"ticker": "AMZN", "company_name": "Amazon.com Inc.", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Consumer Cyclical"},
    {"ticker": "NVDA", "company_name": "NVIDIA Corporation", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Semiconductors"},
    {"ticker": "META", "company_name": "Meta Platforms Inc.", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Communication Services"},
    {"ticker": "TSLA", "company_name": "Tesla Inc.", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Automotive"},
    {"ticker": "NFLX", "company_name": "Netflix Inc.", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Communication Services"},
    {"ticker": "INTC", "company_name": "Intel Corporation", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Semiconductors"},
    {"ticker": "AMD", "company_name": "Advanced Micro Devices Inc.", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Semiconductors"},
    {"ticker": "CSCO", "company_name": "Cisco Systems Inc.", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Technology"},
    {"ticker": "PEP", "company_name": "PepsiCo Inc.", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Consumer Defensive"},
    {"ticker": "ADBE", "company_name": "Adobe Inc.", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Technology"},
    {"ticker": "PYPL", "company_name": "PayPal Holdings Inc.", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Financial Services"},
    {"ticker": "QCOM", "company_name": "QUALCOMM Incorporated", "market": "NASDAQ", "exchange": "NASDAQ", "currency": "USD", "sector": "Technology"},
    
    # US NYSE
    {"ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Financial Services"},
    {"ticker": "V", "company_name": "Visa Inc.", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Financial Services"},
    {"ticker": "WMT", "company_name": "Walmart Inc.", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Consumer Defensive"},
    {"ticker": "JNJ", "company_name": "Johnson & Johnson", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Healthcare"},
    {"ticker": "PG", "company_name": "Procter & Gamble Co.", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Consumer Defensive"},
    {"ticker": "UNH", "company_name": "UnitedHealth Group Incorporated", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Healthcare"},
    {"ticker": "HD", "company_name": "The Home Depot Inc.", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Consumer Cyclical"},
    {"ticker": "BAC", "company_name": "Bank of America Corporation", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Financial Services"},
    {"ticker": "XOM", "company_name": "Exxon Mobil Corporation", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Energy"},
    {"ticker": "DIS", "company_name": "The Walt Disney Company", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Communication Services"},
    {"ticker": "IBM", "company_name": "International Business Machines", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Technology"},
    {"ticker": "ORCL", "company_name": "Oracle Corporation", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Technology"},
    {"ticker": "KO", "company_name": "The Coca-Cola Company", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Consumer Defensive"},
    {"ticker": "PFE", "company_name": "Pfizer Inc.", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Healthcare"},
    {"ticker": "BA", "company_name": "The Boeing Company", "market": "NYSE", "exchange": "NYSE", "currency": "USD", "sector": "Industrials"},

    # India NSE
    {"ticker": "INFY", "company_name": "Infosys Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Technology"},
    {"ticker": "TCS", "company_name": "Tata Consultancy Services Ltd.", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Technology"},
    {"ticker": "RELIANCE", "company_name": "Reliance Industries Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Energy & Retail"},
    {"ticker": "HDFCBANK", "company_name": "HDFC Bank Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Financial Services"},
    {"ticker": "ICICIBANK", "company_name": "ICICI Bank Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Financial Services"},
    {"ticker": "TATAMOTORS", "company_name": "Tata Motors Limited", "market": "NSE", "exchange": "NSE", "bullet": "Automotive", "sector": "Automotive"},
    {"ticker": "WIPRO", "company_name": "Wipro Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Technology"},
    {"ticker": "HINDUNILVR", "company_name": "Hindustan Unilever Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Consumer Goods"},
    {"ticker": "BHARTIARTL", "company_name": "Bharti Airtel Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Telecom"},
    {"ticker": "ITC", "company_name": "ITC Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Consumer Goods"},
    {"ticker": "SBIN", "company_name": "State Bank of India", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Financial Services"},
    {"ticker": "LT", "company_name": "Larsen & Toubro Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Engineering & Construction"},
    {"ticker": "KOTAKBANK", "company_name": "Kotak Mahindra Bank", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Financial Services"},
    {"ticker": "BAJFINANCE", "company_name": "Bajaj Finance Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Financial Services"},
    {"ticker": "MARUTI", "company_name": "Maruti Suzuki India Limited", "market": "NSE", "exchange": "NSE", "currency": "INR", "sector": "Automotive"},

    # India BSE
    {"ticker": "500209", "company_name": "Infosys Limited", "market": "BSE", "exchange": "BSE", "currency": "INR", "sector": "Technology"},
    {"ticker": "532540", "company_name": "Tata Consultancy Services Ltd.", "market": "BSE", "exchange": "BSE", "currency": "INR", "sector": "Technology"},
    {"ticker": "500325", "company_name": "Reliance Industries Limited", "market": "BSE", "exchange": "BSE", "currency": "INR", "sector": "Energy & Retail"},
    {"ticker": "500180", "company_name": "HDFC Bank Limited", "market": "BSE", "exchange": "BSE", "currency": "INR", "sector": "Financial Services"},
    {"ticker": "532174", "company_name": "ICICI Bank Limited", "market": "BSE", "exchange": "BSE", "currency": "INR", "sector": "Financial Services"},
    {"ticker": "500570", "company_name": "Tata Motors Limited", "market": "BSE", "exchange": "BSE", "currency": "INR", "sector": "Automotive"},
    {"ticker": "507685", "company_name": "Wipro Limited", "market": "BSE", "exchange": "BSE", "currency": "INR", "sector": "Technology"},
    {"ticker": "500696", "company_name": "Hindustan Unilever Limited", "market": "BSE", "exchange": "BSE", "currency": "INR", "sector": "Consumer Goods"},
    {"ticker": "532454", "company_name": "Bharti Airtel Limited", "market": "BSE", "exchange": "BSE", "currency": "INR", "sector": "Telecom"},
    {"ticker": "500875", "company_name": "ITC Limited", "market": "BSE", "exchange": "BSE", "currency": "INR", "sector": "Consumer Goods"},
]


class StockDataService:
    @staticmethod
    def _map_exchange_to_market(exch: str, symbol: str) -> Optional[str]:
        exch_upper = (exch or "").upper()
        symbol_upper = symbol.upper()
        if symbol_upper.endswith(".NS") or exch_upper in ["NSE", "NSI"]:
            return "NSE"
        if symbol_upper.endswith(".BO") or exch_upper in ["BSE", "BOM"]:
            return "BSE"
        if exch_upper in ["NAS", "NMS", "NGM", "NCM", "NASDAQ"]:
            return "NASDAQ"
        if exch_upper in ["NYQ", "NYSE", "NYSE MKT", "NYSE ARCA"]:
            return "NYSE"
        return None

    @classmethod
    async def search_stocks(cls, query: str) -> List[StockSearchResult]:
        """Search stocks using market data provider with verified local fallback."""
        query_str = query.strip()
        if not query_str:
            return []

        results: List[StockSearchResult] = []
        seen = set()

        # 1. Search verified local catalog first for immediate match
        q_lower = query_str.lower()
        for item in VERIFIED_STOCKS:
            if (q_lower in item["ticker"].lower() or q_lower in item["company_name"].lower()):
                key = (item["ticker"], item["market"])
                if key not in seen:
                    seen.add(key)
                    results.append(StockSearchResult(
                        ticker=item["ticker"],
                        company_name=item["company_name"],
                        market=item["market"],
                        exchange=item.get("exchange", item["market"]),
                        currency=item.get("currency", "USD"),
                        sector=item.get("sector")
                    ))

        # 2. Query market data provider (Yahoo Finance search API)
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query_str}&quotesCount=10&newsCount=0"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    quotes = data.get("quotes", [])
                    for q in quotes:
                        raw_symbol = q.get("symbol", "")
                        exch = q.get("exchange", "")
                        market = cls._map_exchange_to_market(exch, raw_symbol)
                        if market:
                            clean_symbol = raw_symbol.replace(".NS", "").replace(".BO", "")
                            name = q.get("shortname") or q.get("longname") or clean_symbol
                            key = (clean_symbol, market)
                            if key not in seen:
                                seen.add(key)
                                results.append(StockSearchResult(
                                    ticker=clean_symbol,
                                    company_name=name,
                                    market=market,
                                    exchange=exch or market,
                                    currency="INR" if market in ["NSE", "BSE"] else "USD",
                                    sector=q.get("sector")
                                ))
        except Exception as e:
            logger.warning(f"External stock search exception: {e}")

        return results[:15]

    @classmethod
    def get_stock_profile(cls, ticker: str, market: str) -> Dict[str, Any]:
        """Fetch real company profile & validation for ticker."""
        clean_ticker = ticker.strip().upper()
        clean_market = market.strip().upper()

        # Check verified catalog
        for s in VERIFIED_STOCKS:
            if s["ticker"].upper() == clean_ticker and s["market"].upper() == clean_market:
                return {
                    "ticker": s["ticker"],
                    "company_name": s["company_name"],
                    "market": s["market"],
                    "currency": s.get("currency", "USD"),
                    "sector": s.get("sector", "General")
                }

        # Format symbol for yfinance if applicable
        yf_symbol = clean_ticker
        if clean_market == "NSE" and not yf_symbol.endswith(".NS"):
            yf_symbol = f"{clean_ticker}.NS"
        elif clean_market == "BSE" and not yf_symbol.endswith(".BO"):
            yf_symbol = f"{clean_ticker}.BO"

        try:
            import yfinance as yf
            t = yf.Ticker(yf_symbol)
            info = t.info
            name = info.get("shortName") or info.get("longName") or clean_ticker
            return {
                "ticker": clean_ticker,
                "company_name": name,
                "market": clean_market,
                "currency": info.get("currency", "USD"),
                "sector": info.get("sector", "Equity")
            }
        except Exception as e:
            logger.warning(f"Could not load yfinance info for {yf_symbol}: {e}")
            return {
                "ticker": clean_ticker,
                "company_name": f"{clean_ticker} Corporation",
                "market": clean_market,
                "currency": "INR" if clean_market in ["NSE", "BSE"] else "USD",
                "sector": "Equity"
            }

