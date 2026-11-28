# KNN results (financial health: Weak / Moderate / Strong)

Rows used: 149 from 12 companies. Class counts: {'Strong': 93, 'Moderate': 28, 'Weak': 28}. Always guessing the biggest class would score 62.4%.

Chosen settings (tuned on the training part only): k = 7, weights = distance, features scaled with StandardScaler.

| Test | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) |
|---|---|---|---|---|
| Hold-out 20% (30 rows) | 90.0% | 84.9% | 90.9% | 87.4% |
| Repeated 5-fold CV x5 (mean) | 83.6% | 78.1% | 76.5% | 76.1% |
| Leave-one-company-out | 79.2% | 71.9% | 64.8% | 66.3% |

Hold-out per class:

| Class | Precision | Recall | F1 | Rows |
|---|---|---|---|---|
| Weak | 83.3% | 100.0% | 90.9% | 5 |
| Moderate | 71.4% | 83.3% | 76.9% | 6 |
| Strong | 100.0% | 89.5% | 94.4% | 19 |

Hold-out confusion matrix (rows = true, columns = predicted, order ['Weak', 'Moderate', 'Strong']): [[5, 0, 0], [1, 5, 0], [0, 2, 17]]

Leave-one-company-out confusion matrix: [[20, 4, 4], [5, 7, 16], [0, 2, 91]]

Leave-one-company-out accuracy per company: AAPL 100.0%, AIG 46.2%, AMZN 46.2%, BCS 61.5%, GOOG 100.0%, INTC 100.0%, MCD 100.0%, MSFT 100.0%, NVDA 100.0%, PCG 15.4%, PYPL 87.5%, SHLDQ 100.0%

Distance gate (rejects input unlike the training data): limit = 99th percentile of training distances. It would reject 1.3% of training rows and 6.0% of rows from a company the model had not seen.
