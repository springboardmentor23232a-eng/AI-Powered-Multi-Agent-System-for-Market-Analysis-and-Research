import re
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from fastapi import HTTPException, status


def validate_ticker_symbol(ticker: str) -> str:
    """
    Validates stock ticker formatting.
    Accepts US tickers (e.g. AAPL, MSFT, BRK-B) and Indian tickers (e.g. INFY.NS, TCS.BO).
    Returns normalized uppercase ticker string.
    """
    if not ticker or not isinstance(ticker, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock ticker cannot be empty."
        )

    clean_ticker = ticker.strip().upper()
    pattern = r"^[A-Z0-9]{1,10}(\.[A-Z]{2,4}|-[A-Z]{1,2})?$"
    if not re.match(pattern, clean_ticker):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stock ticker symbol format: '{ticker}'. Expected formats: 'AAPL', 'INFY.NS', 'TCS.BO'."
        )

    return clean_ticker


def check_empty_response(df: pd.DataFrame, ticker: str) -> None:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No market data found for ticker '{ticker}'. Please verify the symbol."
        )


def check_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    required_cols = [col for col in ["Open", "High", "Low", "Close", "Volume"] if col in df.columns]
    df = df.replace([np.inf, -np.inf], np.nan)
    initial_count = len(df)
    cleaned_df = df.dropna(subset=required_cols)
    dropped_count = initial_count - len(cleaned_df)
    return cleaned_df, dropped_count


def check_duplicate_dates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    initial_count = len(df)
    if isinstance(df.index, pd.DatetimeIndex):
        cleaned_df = df[~df.index.duplicated(keep="last")]
    elif "Date" in df.columns:
        cleaned_df = df.drop_duplicates(subset=["Date"], keep="last")
    else:
        cleaned_df = df
    duplicates_removed = initial_count - len(cleaned_df)
    return cleaned_df, duplicates_removed


def check_invalid_prices(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    initial_count = len(df)
    price_cols = [c for c in ["Open", "High", "Low", "Close"] if c in df.columns]
    
    valid_mask = pd.Series(True, index=df.index)
    for col in price_cols:
        valid_mask = valid_mask & (df[col] > 0)

    if "High" in df.columns and "Low" in df.columns:
        valid_mask = valid_mask & (df["High"] >= df["Low"] - 1e-4)
    if "High" in df.columns and "Open" in df.columns:
        valid_mask = valid_mask & (df["High"] >= df["Open"] - 1e-4)
    if "High" in df.columns and "Close" in df.columns:
        valid_mask = valid_mask & (df["High"] >= df["Close"] - 1e-4)
    if "Low" in df.columns and "Open" in df.columns:
        valid_mask = valid_mask & (df["Low"] <= df["Open"] + 1e-4)
    if "Low" in df.columns and "Close" in df.columns:
        valid_mask = valid_mask & (df["Low"] <= df["Close"] + 1e-4)
        
    if "Volume" in df.columns:
        valid_mask = valid_mask & (df["Volume"] >= 0)

    cleaned_df = df[valid_mask].copy()
    invalid_rows_removed = initial_count - len(cleaned_df)
    return cleaned_df, invalid_rows_removed


def check_chronological_order(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    if df.empty:
        return df, True

    if isinstance(df.index, pd.DatetimeIndex):
        is_ordered = df.index.is_monotonic_increasing
        if not is_ordered:
            df = df.sort_index(ascending=True)
    elif "Date" in df.columns:
        is_ordered = df["Date"].is_monotonic_increasing
        if not is_ordered:
            df = df.sort_values(by="Date", ascending=True)
    else:
        is_ordered = True

    return df, is_ordered


def validate_and_clean_market_data(raw_df: pd.DataFrame, ticker: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    check_empty_response(raw_df, ticker)
    total_raw = len(raw_df)
    
    df_missing_cleaned, missing_dropped = check_missing_values(raw_df)
    df_deduped, duplicates_removed = check_duplicate_dates(df_missing_cleaned)
    df_price_validated, invalid_prices_removed = check_invalid_prices(df_deduped)
    df_final, is_chronological = check_chronological_order(df_price_validated)
    
    if df_final.empty:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"All historical records for {ticker} failed data validation integrity checks."
        )

    telemetry = {
        "total_raw_records": total_raw,
        "cleaned_records": len(df_final),
        "missing_values_handled": missing_dropped,
        "duplicates_removed": duplicates_removed,
        "invalid_rows_removed": invalid_prices_removed,
        "is_chronological": bool(is_chronological),
    }

    return df_final, telemetry

