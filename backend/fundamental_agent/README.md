# Fundamental Analysis Agent

Cleans the Kaggle "Financial Statements of Major Companies (2009-2023)" dataset, trains a KNN classifier
on it, and analyses a company: it explains revenue growth, earnings and profitability, classifies the
financial condition as Weak / Moderate / Strong, and refuses with an exact reason when the input is
missing, inconsistent, or unlike the training data.

## Set up (inside your `backend` folder)

1. Copy the `fundamental_agent` folder into `backend/` (next to `main.py`).
2. With the venv active: `pip install scikit-learn joblib`  (pandas and numpy already come with yfinance).
3. Train (also cleans the data and writes the reports): `python -m fundamental_agent.train`
4. Try it: `python -m fundamental_agent.demo`

Retrain on your own machine so the saved model matches your scikit-learn version.

## Use in code

    from fundamental_agent.agent import FundamentalAnalysisAgent
    from fundamental_agent.errors import AnalysisError

    agent = FundamentalAnalysisAgent()
    try:
        result = agent.analyze_from_yahoo(get_financials("AAPL", "annual"), company="Apple")
    except AnalysisError as e:
        notice = e.to_dict()        # {"status": "error", "reasons": [{"code", "field", "message"}, ...]}

## Files

| File | Purpose |
|---|---|
| `preprocess.py` | Cleans the dataset and records every check and fix (reports/cleaning_report.md) |
| `features.py` | Ratios used by the model, and the financial-health rubric that creates the labels |
| `train.py` | Tunes k, evaluates (hold-out, repeated CV, leave-one-company-out), saves the model |
| `agent.py` | The agent: validation gate, KNN classification, explanation |
| `explain.py` | Plain-language explanation (rules, not the KNN) |
| `yahoo_adapter.py` | Converts the app's Yahoo financial statements into the agent's inputs |
| `errors.py` | `AnalysisError` and `Reason` (the error notices) |
| `demo.py` | Good and bad inputs; doubles as a self-test |
| `config.py` | Thresholds, feature list, paths |

## Error notice codes

`missing_value`, `invalid_value`, `inconsistent_data`, `outside_training_range`, `unlike_training_data`,
`statement_unavailable`, `not_reported`, `period_mismatch`.

## Limits to state honestly

* Labels come from a documented rubric (config.py), so the KNN largely learns that rubric. It classifies
  current financial condition, it does not predict the future.
* Only 12 companies (mostly large US firms, one UK bank), 149 usable rows. Moderate is the weakest class.
* Banks and insurers are not supported (their statements lack gross profit and current assets).
* The Yahoo adapter was tested on mock data in the same shape the app collects; check it on real tickers.
