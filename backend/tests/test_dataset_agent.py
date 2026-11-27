import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from app.schemas.dataset import (
    DatasetCollectionRequest,
    DatasetValidationReportResponse,
)
from app.services.dataset_providers.base import BaseMarketDataProvider, DatasetCollectionResult
from app.services.dataset_providers.yfinance_provider import YFinanceProvider
from app.services.dataset_providers.stooq_provider import StooqProvider
from app.services.dataset_providers.registry import ProviderRegistry
from app.services.data_validation_agent import (
    normalize_dataset_columns,
    calculate_data_quality_score,
    determine_validation_status,
    compute_fifty_two_week_metrics,
    validate_and_process_dataset,
)
from app.services.dataset_ai_agent import synthesize_validation_narrative


def _register_and_login_user(client, email: str = "dataset_tester@example.com"):
    reg_payload = {
        "fullName": "Dataset Agent Tester",
        "email": email,
        "password": "Password123!",
        "confirmPassword": "Password123!",
    }
    client.post("/api/auth/register", json=reg_payload)

    login_payload = {
        "email": email,
        "password": "Password123!",
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200
    return res.json()["data"]


def _make_mock_ohlcv_df(rows_count: int = 10, start_date: str = "2024-01-01"):
    dates = pd.date_range(start=start_date, periods=rows_count, freq="B")
    data = {
        "Open": [100.0 + i for i in range(rows_count)],
        "High": [105.0 + i for i in range(rows_count)],
        "Low": [95.0 + i for i in range(rows_count)],
        "Close": [102.0 + i for i in range(rows_count)],
        "Volume": [1000000 + i * 10000 for i in range(rows_count)],
    }
    return pd.DataFrame(data, index=dates)


# ── 1. Provider Layer Tests ───────────────────────────────────────────────────

def test_yfinance_provider_market_support():
    provider = YFinanceProvider()
    assert provider.supports_market("NSE") is True
    assert provider.supports_market("BSE") is True
    assert provider.supports_market("NASDAQ") is True
    assert provider.supports_market("NYSE") is True


def test_stooq_provider_rejects_indian_markets():
    provider = StooqProvider()
    assert provider.supports_market("NSE") is False
    assert provider.supports_market("BSE") is False
    assert provider.supports_market("NASDAQ") is True

    res = provider.fetch_ohlcv("INFY.NS", "1mo", "NSE")
    assert res.success is False
    assert res.status_code == 400
    assert "does not support Indian market symbols" in res.error_message


def test_provider_registry_fallback_on_primary_failure():
    registry = ProviderRegistry()

    # Mock primary provider failure, secondary success
    mock_df = _make_mock_ohlcv_df(5)
    with patch.object(
        YFinanceProvider,
        "fetch_ohlcv",
        return_value=DatasetCollectionResult(
            provider_name="yfinance",
            ticker="AAPL",
            market="NASDAQ",
            period="1mo",
            success=False,
            status_code=502,
            latency_ms=10.0,
            raw_df=None,
            records_count=0,
            error_message="Connection timeout",
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )
    ), patch.object(
        StooqProvider,
        "fetch_ohlcv",
        return_value=DatasetCollectionResult(
            provider_name="stooq",
            ticker="AAPL",
            market="NASDAQ",
            period="1mo",
            success=True,
            status_code=200,
            latency_ms=15.0,
            raw_df=mock_df,
            records_count=5,
            error_message=None,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )
    ):
        raw_df, prov, lat, logs, ts = registry.collect_dataset("AAPL", "1mo", "NASDAQ")
        assert raw_df is not None
        assert prov == "stooq"
        assert len(logs) == 2
        assert logs[0].provider == "yfinance" and logs[0].status == "FAILED"
        assert logs[1].provider == "stooq" and logs[1].status == "SUCCESS"


# ── 2. Deterministic Validation Engine Tests ───────────────────────────────────

def test_validation_engine_pristine_dataset_passed():
    df = _make_mock_ohlcv_df(20)
    raw_snap, val_sum, quality, issues = validate_and_process_dataset(
        raw_input_df=df,
        ticker="TEST.NS",
        data_source="yfinance",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    assert quality.validation_status == "PASSED"
    assert quality.data_quality_score == 100.0
    assert quality.valid_records == 20
    assert quality.excluded_records == 0
    assert quality.duplicate_dates_count == 0
    assert len(issues) == 0
    assert val_sum.valid_records_count == 20


def test_validation_engine_duplicate_dates_classified_warning():
    df = _make_mock_ohlcv_df(10)
    # Inject duplicate date at row index 4 (duplicate of row 3)
    df.index = [
        "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-04",
        "2024-01-05", "2024-01-08", "2024-01-09", "2024-01-10", "2024-01-11"
    ]

    raw_snap, val_sum, quality, issues = validate_and_process_dataset(
        raw_input_df=df,
        ticker="TEST.NS",
        data_source="yfinance",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Policy 1 & 2: A dataset with duplicate dates CANNOT receive PASSED; it must receive WARNING
    assert quality.validation_status == "WARNING"
    assert quality.duplicate_dates_count == 2  # 2 rows share 2024-01-04
    assert quality.valid_records == 9
    assert quality.excluded_records == 1

    # Policy 1: Never silently discard; both rows logged with raw values and action taken
    dup_issues = [i for i in issues if i.issue_type == "DUPLICATE_DATE"]
    assert len(dup_issues) == 2
    assert dup_issues[0].action_taken == "DUPLICATE_SUPERSEDED_EXCLUDED"
    assert dup_issues[1].action_taken == "DUPLICATE_CANONICAL_RETAINED"
    assert "Open" in dup_issues[0].raw_values


def test_validation_engine_missing_values_and_positivity_violations():
    # 20 rows with 2 defects -> 10% fatal defect penalty -> Score = 88.0 -> WARNING
    df = _make_mock_ohlcv_df(20)
    # Row 0: NaN in Open
    df.iloc[0, df.columns.get_loc("Open")] = np.nan
    # Row 1: Negative Price in Close
    df.iloc[1, df.columns.get_loc("Close")] = -50.0

    raw_snap, val_sum, quality, issues = validate_and_process_dataset(
        raw_input_df=df,
        ticker="TEST.NS",
        data_source="yfinance",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    assert quality.validation_status == "WARNING"
    assert quality.valid_records == 18
    assert quality.excluded_records == 2
    assert quality.missing_values_count >= 1
    assert quality.negative_prices_count >= 1
    assert quality.data_quality_score == 88.0

    # Now verify severe defects (>30% defect rate -> Score < 70 -> FAILED)
    df_severe = _make_mock_ohlcv_df(10)
    df_severe.iloc[0, df_severe.columns.get_loc("Open")] = np.nan
    df_severe.iloc[1, df_severe.columns.get_loc("Close")] = -50.0
    df_severe.iloc[2, df_severe.columns.get_loc("Volume")] = -5000

    _, _, quality_severe, _ = validate_and_process_dataset(
        raw_input_df=df_severe,
        ticker="SEVERE.NS",
        data_source="yfinance",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
    )
    assert quality_severe.validation_status == "FAILED"
    assert quality_severe.data_quality_score == 64.0


def test_validation_engine_geometric_inconsistencies():
    df = _make_mock_ohlcv_df(5)
    # Row 0: High < Low (Inverted)
    df.iloc[0, df.columns.get_loc("High")] = 90.0
    df.iloc[0, df.columns.get_loc("Low")] = 110.0
    # Row 1: Open > High
    df.iloc[1, df.columns.get_loc("Open")] = 120.0
    df.iloc[1, df.columns.get_loc("High")] = 105.0

    raw_snap, val_sum, quality, issues = validate_and_process_dataset(
        raw_input_df=df,
        ticker="TEST.NS",
        data_source="yfinance",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    assert quality.valid_records == 3
    assert quality.excluded_records == 2
    assert any(i.issue_type == "HIGH_LESS_THAN_LOW" for i in issues)
    assert any(i.issue_type == "OHLC_INCONSISTENCY" for i in issues)


def test_validation_engine_empty_dataset_failed():
    raw_snap, val_sum, quality, issues = validate_and_process_dataset(
        raw_input_df=pd.DataFrame(),
        ticker="EMPTY.NS",
        data_source="yfinance",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    assert quality.validation_status == "FAILED"
    assert quality.data_quality_score == 0.0
    assert quality.valid_records == 0
    assert any(i.issue_type == "EMPTY_DATASET" for i in issues)


def test_validation_engine_chronology_reordering_warning():
    df = _make_mock_ohlcv_df(5)
    # Invert index order (newest first)
    df = df.iloc[::-1]

    raw_snap, val_sum, quality, issues = validate_and_process_dataset(
        raw_input_df=df,
        ticker="REORDER.NS",
        data_source="yfinance",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    assert quality.reordered_chronology is True
    assert quality.validation_status == "WARNING"  # Reordered data receives WARNING
    assert any(i.issue_type == "CHRONOLOGY_REORDERED" for i in issues)


# ── 3. 52-Week Metric Coverage Policy Tests ────────────────────────────────────

def test_fifty_two_week_coverage_under_250_days_unavailable():
    # Only 50 days (e.g. 1mo/3mo)
    df = _make_mock_ohlcv_df(50)
    raw_snap, val_sum, quality, issues = validate_and_process_dataset(
        raw_input_df=df,
        ticker="SHORT.NS",
        data_source="yfinance",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    m = val_sum.fifty_two_week_metrics
    assert m.status == "unavailable"
    assert m.high is None
    assert m.low is None
    assert m.range_pct is None
    assert "requires >= 250 valid trading days" in m.notes


def test_fifty_two_week_coverage_over_250_days_verified():
    # 260 days (>= 250)
    df = _make_mock_ohlcv_df(260)
    raw_snap, val_sum, quality, issues = validate_and_process_dataset(
        raw_input_df=df,
        ticker="LONG.NS",
        data_source="yfinance",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    m = val_sum.fifty_two_week_metrics
    assert m.status == "verified"
    assert m.high is not None
    assert m.low is not None
    assert m.range_pct is not None
    assert m.valid_trading_days == 260


# ── 4. AI Narrative Synthesis Guardrail Tests ─────────────────────────────────

def test_ai_narrative_synthesis_no_speculative_attribution():
    df = _make_mock_ohlcv_df(10)
    # Inject large volume outlier
    df.iloc[5, df.columns.get_loc("Volume")] = 50000000

    raw_snap, val_sum, quality, issues = validate_and_process_dataset(
        raw_input_df=df,
        ticker="SPIKE.NS",
        data_source="yfinance",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    narrative = synthesize_validation_narrative(
        ticker="SPIKE.NS",
        company_name="Spike Technologies",
        market="NSE",
        active_provider="yfinance",
        quality=quality,
        val_summary=val_sum,
        raw_snap=raw_snap,
        issues=issues,
    )

    # Must NOT state corporate events as established facts
    assert "rather than established facts" in narrative.market_anomaly_interpretation
    assert "possible market events" in narrative.market_anomaly_interpretation
    assert "APPROVED FOR ALL RESEARCH MODULES" in narrative.research_readiness_assessment


# ── 5. API Route & Access Control Tests ───────────────────────────────────────

def test_api_collect_and_validate_authenticated(client, monkeypatch):
    _register_and_login_user(client, "dataset_user@example.com")

    mock_df = _make_mock_ohlcv_df(20)
    with patch.object(
        ProviderRegistry,
        "collect_dataset",
        return_value=(mock_df, "yfinance", 42.5, [], datetime.now(timezone.utc).isoformat())
    ):
        res = client.post(
            "/api/dataset/collect-and-validate",
            json={"ticker": "INFY.NS", "period": "1mo", "market": "NSE"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["ticker"] == "INFY.NS"
        assert data["active_provider"] == "yfinance"
        assert data["validation_status"] == "PASSED"
        assert data["quality_metrics"]["data_quality_score"] == 100.0
        assert data["quality_metrics"]["valid_records"] == 20
        assert data["report_id"] is not None
        assert "download_url_json" in data
        assert "download_url_csv" in data


def test_api_collect_and_validate_unauthenticated_rejected(client):
    unauth_client = TestClient(client.app)
    res = unauth_client.post(
        "/api/dataset/collect-and-validate",
        json={"ticker": "AAPL", "period": "1mo", "market": "NASDAQ"},
    )
    assert res.status_code == 401


def test_api_list_and_get_dataset_reports(client, monkeypatch):
    user_data = _register_and_login_user(client, "reports_user@example.com")

    mock_df = _make_mock_ohlcv_df(15)
    with patch.object(
        ProviderRegistry,
        "collect_dataset",
        return_value=(mock_df, "yfinance", 35.0, [], datetime.now(timezone.utc).isoformat())
    ):
        create_res = client.post(
            "/api/dataset/collect-and-validate",
            json={"ticker": "TCS.NS", "period": "1mo", "market": "NSE"},
        )
        assert create_res.status_code == 201
        report_id = create_res.json()["report_id"]

        # List user reports
        list_res = client.get("/api/dataset/reports")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["count"] >= 1
        assert any(r["report_id"] == report_id for r in list_data["data"])

        # Get specific report detail
        detail_res = client.get(f"/api/dataset/reports/{report_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["report_id"] == report_id
        assert detail["ticker"] == "TCS.NS"
        assert detail["quality_metrics"]["valid_records"] == 15


def test_api_dataset_report_user_isolation_forbidden(client, monkeypatch):
    # User 1 creates report
    _register_and_login_user(client, "user_alpha@example.com")
    mock_df = _make_mock_ohlcv_df(10)
    with patch.object(
        ProviderRegistry,
        "collect_dataset",
        return_value=(mock_df, "yfinance", 25.0, [], datetime.now(timezone.utc).isoformat())
    ):
        create_res = client.post(
            "/api/dataset/collect-and-validate",
            json={"ticker": "AAPL", "period": "1mo", "market": "NASDAQ"},
        )
        assert create_res.status_code == 201
        report_id = create_res.json()["report_id"]

    # User 2 logs in and attempts to access User 1's report
    _register_and_login_user(client, "user_beta@example.com")
    get_res = client.get(f"/api/dataset/reports/{report_id}")
    assert get_res.status_code == 403
    assert "Access forbidden" in get_res.json()["detail"]


def test_api_download_dataset_report_json_and_csv(client, monkeypatch):
    _register_and_login_user(client, "download_user@example.com")
    mock_df = _make_mock_ohlcv_df(12)
    with patch.object(
        ProviderRegistry,
        "collect_dataset",
        return_value=(mock_df, "yfinance", 30.0, [], datetime.now(timezone.utc).isoformat())
    ):
        create_res = client.post(
            "/api/dataset/collect-and-validate",
            json={"ticker": "IBM", "period": "1mo", "market": "NYSE"},
        )
        report_id = create_res.json()["report_id"]

        # Download JSON
        json_res = client.get(f"/api/dataset/reports/{report_id}/download?format=json")
        assert json_res.status_code == 200
        assert "application/json" in json_res.headers["content-type"]
        assert "attachment" in json_res.headers["content-disposition"]
        json_data = json_res.json()
        assert json_data["ticker"] == "IBM"

        # Download CSV
        csv_res = client.get(f"/api/dataset/reports/{report_id}/download?format=csv")
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers["content-type"]
        assert "attachment" in csv_res.headers["content-disposition"]
        assert "Open,High,Low,Close,Volume" in csv_res.text or "Date" in csv_res.text
