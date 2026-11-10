# Veritas Evaluation Report

Provider: yfinance · News: google-news-rss · Tickers: 20 · Generated: 2026-11-05T08:20:22 UTC · Wall time: 82.1s

## Summary

| Metric | Result | Target | Status |
|---|---|---|---|
| Calculation accuracy (vs independent reference, tol 1e-06) | 100.0% of 325 | 100% | PASS |
| Citation coverage (FACT claims with a stored source) | 100.0% of 167 | ≥95% | PASS |
| Citation correctness, automated (quote found in source) | 100.0% | ≥95% | PASS |
| Citation correctness, manual audit | see `citation_audit_sample.csv` (40 rows) | label then score | pending |
| Claims verified by the Verifier | 100.0% (620/620) | 100% | PASS |
| Task completion rate (all four agents) | 100.0% | report only | n/a |
| Usable report rate (completed + partial) | 100.0% | report only | n/a |
| Report completeness (all required sections) | 100.0% | 100% | PASS |
| Failure drills passed | 5/5 | all | PASS |
| Latency p50 / p95 | 1804 ms / 2703 ms | report only | n/a |
| Cost per report | 0.0 tokens, est. $0.0 at $0.0/Mtok | report only | n/a |

## Calculation accuracy

| Function | Agreed | Total |
|---|---|---|
| book_value_per_share | 19 | 19 |
| debt_to_equity | 19 | 19 |
| eps | 19 | 19 |
| growth_rate | 19 | 19 |
| historical_volatility | 40 | 40 |
| macd | 20 | 20 |
| margin | 52 | 52 |
| max_drawdown | 20 | 20 |
| pb_ratio | 19 | 19 |
| pe_ratio | 19 | 19 |
| roe | 19 | 19 |
| rsi | 20 | 20 |
| sma | 40 | 40 |

Max absolute error: 1.22e-15. Unreferenced functions: 0.

## Claim ledger

| Type | Verified | Total |
|---|---|---|
| FACT | 167 | 167 |
| CALCULATED | 325 | 325 |
| INTERPRETATION | 128 | 128 |

## Agent reliability

Status counts: {'completed': 20}. Retries used: 0.

| Agent | Success | p50 latency (ms) |
|---|---|---|
| fundamental | 100.0% | 20 |
| news | 100.0% | 582 |
| risk | 100.0% | 12 |
| technical | 100.0% | 44 |

## Failure drills

| Drill | Result | Detail |
|---|---|---|
| News API down for the whole run | PASS | task=partial, news=unavailable after 3 attempts, news claims=0 |
| News API fails once, then recovers | PASS | news=success, attempts=2 |
| Market data down, stale snapshot available | PASS | task=completed, stale-cache warning in report=True |
| Total outage with no cache | PASS | task=failed, report produced=False |
| Dirty price data (duplicates, null price) | PASS | technical=success, issues reported in limitations=True |

## Replay calibration (technical signal)

Horizon 30 days. Windows: 60, directional calls: 23, hits: 10, hit rate: 43.5% (95% CI (25.6, 63.2)), base rate of up-moves: 41.7%.

A hit rate is only informative relative to the base rate and its confidence interval. Fundamental signal not scored: financial statements are not point-in-time.

## Limitations

- Small sample (one universe, one time window); replay windows overlap and are not independent.
- Manual citation audit is required to measure whether sources truly support claims; the automated check only confirms the quoted text exists.
- Cost uses the assumed per-million-token rate; the offline template LLM uses zero tokens.
- News sentiment labels are AI-classified from headlines and snippets and are not scored here.
