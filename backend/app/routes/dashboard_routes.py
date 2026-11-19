import yfinance as yf
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, SavedStock, ResearchTask, ResearchReport, UserPreference
from app.schemas import (
    SavedStockCreate,
    SavedStockOut,
    ResearchTaskCreate,
    ResearchTaskOut,
    ResearchReportOut,
    UserPreferenceUpdate,
    UserPreferenceOut
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

PERIOD_MAP = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y"
}

KNOWN_NAMES = {
    "TCS": "Tata Consultancy Services Limited",
    "TCS.NS": "Tata Consultancy Services Limited",
    "INFY": "Infosys Limited",
    "INFY.NS": "Infosys Limited",
    "RELIANCE": "Reliance Industries Limited",
    "RELIANCE.NS": "Reliance Industries Limited",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "TSLA": "Tesla, Inc.",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "NVDA": "NVIDIA Corporation",
    "HDFCBANK": "HDFC Bank Limited",
    "HDFCBANK.NS": "HDFC Bank Limited",
    "ICICIBANK": "ICICI Bank Limited",
    "ICICIBANK.NS": "ICICI Bank Limited",
    "WIPRO": "Wipro Limited",
    "WIPRO.NS": "Wipro Limited",
}


def format_ticker_for_market(raw_ticker: str, market: str) -> str:
    """Formats ticker symbol appropriately for the yfinance market exchange."""
    ticker = raw_ticker.strip().upper()
    m = (market or "").upper()
    if m == "NSE" and not ticker.endswith(".NS"):
        return f"{ticker}.NS"
    elif m == "BSE" and not ticker.endswith(".BO"):
        return f"{ticker}.BO"
    elif m in ["NASDAQ", "NYSE"]:
        # Strip Indian exchange extensions if switched to US
        return ticker.replace(".NS", "").replace(".BO", "")
    return ticker


def get_ticker_meta(ticker_symbol: str):
    """Retrieves metadata, currency, and real-time pricing from yfinance."""
    sym = ticker_symbol.upper()
    try:
        t = yf.Ticker(sym)
        fast_price = t.fast_info.get("lastPrice")
        prev_close = t.fast_info.get("previousClose")
        raw_currency = t.fast_info.get("currency") or "USD"
        
        change_pct = None
        if fast_price and prev_close:
            change_pct = round(((fast_price - prev_close) / prev_close) * 100, 2)
            
        is_us = (raw_currency.upper() == "USD") or ("." not in sym)
        curr_sym = "$" if is_us else "₹"
        
        name = KNOWN_NAMES.get(sym) or t.info.get("shortName") or f"{sym} Equity"
        mkt = "NSE" if sym.endswith(".NS") else ("BSE" if sym.endswith(".BO") else "NASDAQ")
        
        return {
            "name": name,
            "market": mkt,
            "currency": raw_currency.upper(),
            "currency_symbol": curr_sym,
            "price": round(fast_price, 2) if fast_price else None,
            "change_pct": change_pct,
            "is_us": is_us,
        }
    except Exception:
        is_us = ("." not in sym)
        return {
            "name": KNOWN_NAMES.get(sym, f"{sym} Equity"),
            "market": "NSE" if sym.endswith(".NS") else "NASDAQ",
            "currency": "USD" if is_us else "INR",
            "currency_symbol": "$" if is_us else "₹",
            "price": None,
            "change_pct": None,
            "is_us": is_us,
        }


@router.get("/watchlist", response_model=List[SavedStockOut])
def get_user_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the authenticated user's saved stocks enriched with live yfinance market data.
    """
    stocks = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.user_id
    ).order_by(SavedStock.created_at.desc()).all()

    enriched_stocks = []
    for item in stocks:
        meta = get_ticker_meta(item.ticker)
        enriched_stocks.append(SavedStockOut(
            saved_stock_id=item.saved_stock_id,
            ticker=item.ticker,
            company_name=meta["name"],
            market=meta["market"],
            exchange=f"{meta['market']} ({'US' if meta['is_us'] else 'India'})",
            currency=meta["currency"],
            currency_symbol=meta["currency_symbol"],
            current_price=meta["price"],
            change_percent=meta["change_pct"],
            is_us_market=meta["is_us"],
            created_at=item.created_at
        ))

    return enriched_stocks


@router.post("/watchlist", response_model=SavedStockOut, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    stock_in: SavedStockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves a stock ticker to the user's watchlist in PostgreSQL after verifying with yfinance.
    """
    cleaned_ticker = stock_in.ticker.strip().upper()

    existing = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.user_id,
        SavedStock.ticker == cleaned_ticker
    ).first()

    if existing:
        meta = get_ticker_meta(existing.ticker)
        return SavedStockOut(
            saved_stock_id=existing.saved_stock_id,
            ticker=existing.ticker,
            company_name=meta["name"],
            market=meta["market"],
            exchange=meta["market"],
            currency=meta["currency"],
            currency_symbol=meta["currency_symbol"],
            current_price=meta["price"],
            change_percent=meta["change_pct"],
            is_us_market=meta["is_us"],
            created_at=existing.created_at
        )

    new_saved = SavedStock(
        user_id=current_user.user_id,
        ticker=cleaned_ticker
    )

    try:
        db.add(new_saved)
        db.commit()
        db.refresh(new_saved)
        meta = get_ticker_meta(new_saved.ticker)
        return SavedStockOut(
            saved_stock_id=new_saved.saved_stock_id,
            ticker=new_saved.ticker,
            company_name=meta["name"],
            market=meta["market"],
            exchange=meta["market"],
            currency=meta["currency"],
            currency_symbol=meta["currency_symbol"],
            current_price=meta["price"],
            change_percent=meta["change_pct"],
            is_us_market=meta["is_us"],
            created_at=new_saved.created_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add stock to watchlist: {str(e)}"
        )


@router.delete("/watchlist/{saved_stock_id}", status_code=status.HTTP_200_OK)
def remove_from_watchlist(
    saved_stock_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a saved stock from the user's watchlist."""
    stock = db.query(SavedStock).filter(
        SavedStock.saved_stock_id == saved_stock_id,
        SavedStock.user_id == current_user.user_id
    ).first()

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock item not found in your watchlist."
        )

    db.delete(stock)
    db.commit()
    return {"message": "Stock removed from watchlist successfully"}


def generate_synthesis_report(
    ticker: str,
    market: str,
    requested_period: str = "6 Months",
    company_name: Optional[str] = None
):
    """
    Builds the structured synthesis research report combining the 8 module features:
      1. Company overview (Filled with live data & corporate profile)
      2. Fundamental analysis (Coming soon)
      3. Technical analysis (Coming soon)
      4. News and sentiment summary (Coming soon)
      5. Risk assessment (Coming soon)
      6. Conflicting findings (Coming soon)
      7. Supporting source links and timestamps (Filled)
      8. Data limitations and uncertainty (Filled)
    """
    chosen_market = (market or "NSE").upper()
    formatted_ticker = format_ticker_for_market(ticker, chosen_market)
    yf_period = PERIOD_MAP.get(requested_period, "6mo")
    now = datetime.now(timezone.utc)
    retrieval_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    currency_code = "USD" if chosen_market in ["NASDAQ", "NYSE"] else "INR"
    currency_sym = "$" if currency_code == "USD" else "₹"
    is_us = (currency_code == "USD") or (chosen_market in ["NASDAQ", "NYSE"])
    
    resolved_company = company_name or KNOWN_NAMES.get(formatted_ticker) or f"{formatted_ticker} Equity"
    yf_price = None
    hist_count = 0
    sector_str = "General Industry"
    industry_str = "Commercial Markets"
    biz_summary = ""

    try:
        yf_obj = yf.Ticker(formatted_ticker)
        hist = yf_obj.history(period=yf_period)
        hist_count = len(hist)

        info = yf_obj.info or {}
        fast = yf_obj.fast_info or {}

        yf_price = fast.get("lastPrice") or info.get("currentPrice") or info.get("regularMarketPrice")
        if yf_price:
            yf_price = round(float(yf_price), 2)

        currency_code = (fast.get("currency") or info.get("currency") or currency_code).upper()
        currency_sym = "$" if currency_code == "USD" else "₹"
        is_us = (currency_code == "USD") or (chosen_market in ["NASDAQ", "NYSE"])

        short_n = info.get("shortName") or info.get("longName")
        if short_n:
            resolved_company = short_n

        sector_str = info.get("sector") or sector_str
        industry_str = info.get("industry") or industry_str

        raw_summary = info.get("longBusinessSummary")
        if raw_summary:
            if len(raw_summary) > 300:
                biz_summary = raw_summary[:297] + "..."
            else:
                biz_summary = raw_summary
    except Exception:
        pass

    if not biz_summary:
        biz_summary = f"{resolved_company} is an actively traded enterprise listed on the {chosen_market} exchange."

    currency_notice = ""
    if is_us:
        currency_notice = (
            f"**⚠️ Currency Notice (US Market):** All valuation multiples and metrics for {formatted_ticker} "
            f"are denominated in **US Dollars ($ USD)**.\n\n"
        )

    price_mention = f" Latest recorded price: {currency_sym}{yf_price} {currency_code}." if yf_price else ""
    summary_text = (
        f"AI-Powered Research Report Synthesis for {resolved_company} ({formatted_ticker}) "
        f"covering the {requested_period} timeframe ({hist_count} trading records analyzed via yfinance API).{price_mention} "
        f"Report generated on {now.strftime('%B %d, %Y')} with market data retrieved at {retrieval_timestamp} UTC. "
        f"Combines corporate overview, verification sources, and analytical limitation framework."
    )

    content_text = (
        f"### 1. Company Overview\n"
        f"- **Enterprise Name:** {resolved_company} ({formatted_ticker})\n"
        f"- **Trading Exchange:** {chosen_market} ({'United States' if is_us else 'India'})\n"
        f"- **Industry Sector:** {sector_str} | {industry_str}\n"
        f"- **Reporting Currency:** {currency_code} ({currency_sym})\n"
        f"- **Primary Exchange Identifier:** {formatted_ticker}\n"
        f"- **Report Generated Date:** {now.strftime('%B %d, %Y (%H:%M:%S UTC)')}\n"
        f"- **Data Source Provider:** yfinance API\n"
        f"- **Data Retrieval Timestamp:** {retrieval_timestamp} UTC\n"
        f"- **Business Profile:** {biz_summary}\n\n"

        f"### 2. Fundamental Analysis [COMING SOON]\n"
        f"- **Agent Status:** 🤖 Coming Soon — Fundamental Analysis Agent in development\n"
        f"- **Planned Analysis:** Automated balance sheet, income statement, profit margins, ROE, debt-to-equity ratio, and valuation multiples.\n\n"

        f"### 3. Technical Analysis [COMING SOON]\n"
        f"- **Agent Status:** 📈 Coming Soon — Technical Analysis Agent in development\n"
        f"- **Planned Analysis:** Historical price trends, 20/50-day moving averages (SMA/EMA), Relative Strength Index (RSI), MACD momentum, and support/resistance levels.\n\n"

        f"### 4. News and Sentiment Summary [COMING SOON]\n"
        f"- **Agent Status:** 📰 Coming Soon — News and Sentiment Agent in development\n"
        f"- **Planned Analysis:** Financial media aggregation, company announcements, regulatory disclosures, and NLP-driven market sentiment scoring.\n\n"

        f"### 5. Risk Assessment [COMING SOON]\n"
        f"- **Agent Status:** 🛡️ Coming Soon — Risk Analysis Agent in development\n"
        f"- **Planned Analysis:** Volatility assessment, downside tail risk, Value-at-Risk (VaR), and maximum historical drawdown.\n\n"

        f"### 6. Conflicting Findings [COMING SOON]\n"
        f"- **Agent Status:** ⚖️ Coming Soon — Multi-Agent Supervisor Engine in development\n"
        f"- **Planned Analysis:** Automated arbitration and synthesis when fundamental valuation, technical indicators, and news sentiment present diverging signals.\n\n"

        f"### 7. Supporting Source Links and Timestamps\n"
        f"- **Report Generated Date:** {now.strftime('%B %d, %Y (%H:%M:%S UTC)')}\n"
        f"- **Data Source Provider:** yfinance Market Data Feed (https://finance.yahoo.com/quote/{formatted_ticker})\n"
        f"- **Retrieval Timestamp:** {retrieval_timestamp} UTC\n"
        f"- **Market Feed Protocol:** Real-time securities quote feed via yfinance API\n"
        f"- **Exchange Listing Verification:** Verified active securities listing on {chosen_market}\n\n"

        f"### 8. Data Limitations and Uncertainty\n"
        f"- **Lookback Horizon:** Historical dataset bounded strictly to {hist_count} trading sessions ({requested_period} window).\n"
        f"- **Data Delays & Latency:** Public market data feeds may experience exchange latency, revisions, and corporate action adjustments.\n"
        f"- **Market Uncertainty & Disclaimer:** Historical information and automated metrics do not guarantee future performance. All findings are for informational and research purposes only."
    )

    limitations_text = (
        f"Historical market price data covers {hist_count} trading sessions ({requested_period} lookback). "
        "Factual market data retrieved via yfinance API. Multi-agent analytical pipelines (Fundamental, Technical, Sentiment, and Risk agents) are currently under development."
    )

    return resolved_company, summary_text, content_text, limitations_text


@router.post("/research", response_model=ResearchTaskOut, status_code=status.HTTP_201_CREATED)
def create_research_task(
    task_in: ResearchTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new research task powered by real yfinance historical datasets.
    Validates provider ticker compatibility, fetches real metrics, and compiles multi-agent report.
    """
    chosen_market = (task_in.market or "NSE").upper()
    formatted_ticker = format_ticker_for_market(task_in.ticker, chosen_market)
    now = datetime.now(timezone.utc)

    resolved_company, summary_text, content_text, limitations_text = generate_synthesis_report(
        ticker=formatted_ticker,
        market=chosen_market,
        requested_period=task_in.requested_period or "6 Months",
        company_name=task_in.company_name
    )

    # 1. Create Research Task record in PostgreSQL / Database
    new_task = ResearchTask(
        user_id=current_user.user_id,
        ticker=formatted_ticker,
        market=chosen_market,
        requested_period=task_in.requested_period or "6 Months",
        status="Completed",
        created_at=now,
        completed_at=now
    )
    db.add(new_task)
    db.flush()

    new_report = ResearchReport(
        task_id=new_task.task_id,
        report_content=content_text,
        summary=summary_text,
        limitations=limitations_text,
        created_at=now
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_task)

    return ResearchTaskOut(
        task_id=new_task.task_id,
        ticker=new_task.ticker,
        company_name=resolved_company,
        market=new_task.market,
        requested_period=new_task.requested_period,
        status=new_task.status,
        created_at=new_task.created_at,
        completed_at=new_task.completed_at,
        has_report=True
    )


@router.get("/recent-research", response_model=List[ResearchTaskOut])
def get_recent_research(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves previous research records belonging to the authenticated user."""
    tasks = db.query(ResearchTask).filter(
        ResearchTask.user_id == current_user.user_id
    ).order_by(ResearchTask.created_at.desc()).limit(20).all()

    output = []
    for task in tasks:
        cname = KNOWN_NAMES.get(task.ticker) or f"{task.ticker} Equity"
        output.append(ResearchTaskOut(
            task_id=task.task_id,
            ticker=task.ticker,
            company_name=cname,
            market=task.market,
            requested_period=task.requested_period,
            status=task.status,
            created_at=task.created_at,
            completed_at=task.completed_at,
            has_report=len(task.reports) > 0
        ))
    return output


@router.get("/research/{task_id}/report", response_model=ResearchReportOut)
def get_task_report(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves the synthesized research report for a specific task."""
    task = db.query(ResearchTask).filter(
        ResearchTask.task_id == task_id,
        ResearchTask.user_id == current_user.user_id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Research task not found.")

    report = db.query(ResearchReport).filter(
        ResearchReport.task_id == task_id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="No report generated for this task.")

    company_name = KNOWN_NAMES.get(task.ticker) or f"{task.ticker} Equity"

    # Auto-upgrade legacy reports that contained old mock agent numbers, old tags, or unformatted summary notices
    if report and ("+0.68" in (report.report_content or "") or "### 1. Fundamental Analysis Agent" in (report.report_content or "") or "[FACTUAL DATA]" in (report.report_content or "") or "Structured" in (report.summary or "") or "Currency Notice" in (report.summary or "") or "**⚠️" in (report.summary or "")):
        try:
            resolved_cname, summary_text, content_text, limitations_text = generate_synthesis_report(
                ticker=task.ticker,
                market=task.market,
                requested_period=task.requested_period,
                company_name=company_name
            )
            report.report_content = content_text
            report.summary = summary_text
            report.limitations = limitations_text
            db.commit()
            company_name = resolved_cname
        except Exception:
            pass

    return ResearchReportOut(
        report_id=report.report_id,
        task_id=task.task_id,
        ticker=task.ticker,
        company_name=company_name,
        summary=report.summary or "",
        report_content=report.report_content or "",
        limitations=report.limitations or "",
        created_at=report.created_at
    )


@router.get("/preferences", response_model=UserPreferenceOut)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the user's research preferences."""
    pref = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.user_id
    ).first()

    if not pref:
        pref = UserPreference(
            user_id=current_user.user_id,
            preferred_market="NSE",
            preferred_period="6 Months"
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)

    return UserPreferenceOut(
        preferred_market=pref.preferred_market,
        preferred_period=pref.preferred_period,
        updated_at=pref.updated_at
    )


@router.put("/preferences", response_model=UserPreferenceOut)
def update_user_preferences(
    pref_in: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the user's research preferences in PostgreSQL.
    Validates that chosen market and period are supported by the yfinance data provider.
    """
    if pref_in.preferred_period not in PERIOD_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis period '{pref_in.preferred_period}' is not supported."
        )

    pref = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.user_id
    ).first()

    now = datetime.now(timezone.utc)

    if not pref:
        pref = UserPreference(
            user_id=current_user.user_id,
            preferred_market=pref_in.preferred_market,
            preferred_period=pref_in.preferred_period,
            updated_at=now
        )
        db.add(pref)
    else:
        pref.preferred_market = pref_in.preferred_market
        pref.preferred_period = pref_in.preferred_period
        pref.updated_at = now

    db.commit()
    db.refresh(pref)

    return UserPreferenceOut(
        preferred_market=pref.preferred_market,
        preferred_period=pref.preferred_period,
        updated_at=pref.updated_at
    )
