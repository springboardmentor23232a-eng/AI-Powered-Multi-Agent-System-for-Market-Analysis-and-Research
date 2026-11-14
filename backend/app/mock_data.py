from typing import List, Dict, Optional

# Curated reference list of supported equities across US and Indian Exchanges
KNOWN_STOCKS = [
    # US NASDAQ
    {"ticker": "AAPL", "company_name": "Apple Inc.", "market": "NASDAQ", "sector": "Technology", "currency": "USD"},
    {"ticker": "MSFT", "company_name": "Microsoft Corporation", "market": "NASDAQ", "sector": "Technology", "currency": "USD"},
    {"ticker": "NVDA", "company_name": "NVIDIA Corporation", "market": "NASDAQ", "sector": "Semiconductors", "currency": "USD"},
    {"ticker": "GOOGL", "company_name": "Alphabet Inc. (Class A)", "market": "NASDAQ", "sector": "Communication Services", "currency": "USD"},
    {"ticker": "AMZN", "company_name": "Amazon.com Inc.", "market": "NASDAQ", "sector": "Consumer Discretionary", "currency": "USD"},
    {"ticker": "TSLA", "company_name": "Tesla, Inc.", "market": "NASDAQ", "sector": "Automotive & Energy", "currency": "USD"},
    {"ticker": "META", "company_name": "Meta Platforms, Inc.", "market": "NASDAQ", "sector": "Communication Services", "currency": "USD"},
    
    # US NYSE
    {"ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "market": "NYSE", "sector": "Financial Services", "currency": "USD"},
    {"ticker": "V", "company_name": "Visa Inc.", "market": "NYSE", "sector": "Financial Services", "currency": "USD"},
    {"ticker": "WMT", "company_name": "Walmart Inc.", "market": "NYSE", "sector": "Consumer Staples", "currency": "USD"},
    {"ticker": "DIS", "company_name": "The Walt Disney Company", "market": "NYSE", "sector": "Entertainment", "currency": "USD"},
    
    # India NSE
    {"ticker": "RELIANCE", "company_name": "Reliance Industries Ltd.", "market": "NSE", "sector": "Conglomerate & Energy", "currency": "INR"},
    {"ticker": "TCS", "company_name": "Tata Consultancy Services Ltd.", "market": "NSE", "sector": "Information Technology", "currency": "INR"},
    {"ticker": "INFY", "company_name": "Infosys Ltd.", "market": "NSE", "sector": "Information Technology", "currency": "INR"},
    {"ticker": "HDFCBANK", "company_name": "HDFC Bank Ltd.", "market": "NSE", "sector": "Banking & Financial Services", "currency": "INR"},
    {"ticker": "ICICIBANK", "company_name": "ICICI Bank Ltd.", "market": "NSE", "sector": "Banking & Financial Services", "currency": "INR"},
    {"ticker": "TATAMOTORS", "company_name": "Tata Motors Ltd.", "market": "NSE", "sector": "Automotive", "currency": "INR"},
    {"ticker": "BHARTIARTL", "company_name": "Bharti Airtel Ltd.", "market": "NSE", "sector": "Telecommunications", "currency": "INR"},
    
    # India BSE
    {"ticker": "ITC", "company_name": "ITC Ltd.", "market": "BSE", "sector": "Consumer Goods & Conglomerate", "currency": "INR"},
    {"ticker": "SBIN", "company_name": "State Bank of India", "market": "BSE", "sector": "Banking", "currency": "INR"},
    {"ticker": "LT", "company_name": "Larsen & Toubro Ltd.", "market": "BSE", "sector": "Engineering & Construction", "currency": "INR"},
]

def search_stocks(query: str, market: Optional[str] = None) -> List[Dict]:
    """Search known stocks by ticker symbol or company name."""
    q = query.strip().upper()
    results = []
    for stock in KNOWN_STOCKS:
        if market and stock["market"].upper() != market.upper():
            continue
        if q in stock["ticker"].upper() or q in stock["company_name"].upper():
            results.append(stock)
    return results

def resolve_stock_info(ticker: str, preferred_market: str = "NASDAQ") -> Dict[str, str]:
    """Resolve metadata for a ticker, falling back to default formats."""
    clean_ticker = ticker.strip().upper()
    for s in KNOWN_STOCKS:
        if s["ticker"].upper() == clean_ticker:
            return {
                "ticker": s["ticker"],
                "company_name": s["company_name"],
                "market": s["market"],
                "sector": s.get("sector", "General")
            }
    
    # Custom / unlisted symbol fallback
    return {
        "ticker": clean_ticker,
        "company_name": f"{clean_ticker} Corporation",
        "market": preferred_market,
        "sector": "Market Equities"
    }
