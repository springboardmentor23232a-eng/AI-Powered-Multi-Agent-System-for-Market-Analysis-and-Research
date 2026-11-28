# Data cleaning report (Financial_Statements.csv)

Rows before cleaning: 161. Rows after cleaning: 161.

| Check | What was found | Action taken |
|---|---|---|
| Column names | 1 name(s) with stray spaces: ['Company '] | Stripped the spaces |
| Category spelling | 9 labels, 'BANK' and 'Bank' are the same sector | Merged into 'Bank' (8 categories left) |
| Missing values | Market Cap(in B USD): PYPL 2014 | Kept as missing. This column is in USD and is not used by the model |
| Duplicate company-year rows | 0 | - |
| Missing years inside a company's history | none | - |
| Impossible values (revenue <= 0, gross profit > revenue, EPS sign differs from net income, market cap <= 0) | 0 row(s) | - |
| Stated net margin differs from Net Income / Revenue by more than 1 point | 5: BCS 2022, BCS 2020, BCS 2019, BCS 2017, BCS 2016 | Kept and flagged. The model recomputes net margin itself |
| Stated ROE differs from Net Income / Equity by more than 5 points | 5: AIG 2010, AIG 2009, SHLDQ 2015, SHLDQ 2014, BCS 2009 | Kept and flagged. ROE is not used as a model feature |
| Negative shareholder equity (ROE and debt-to-equity become misleading) | 11: SHLDQ 2018, SHLDQ 2017, SHLDQ 2016, SHLDQ 2015, MCD 2022, MCD 2021, MCD 2020, MCD 2019, MCD 2018, MCD 2017, MCD 2016 | Kept. Debt-to-equity is set to the cap of 10 for these rows |
| Extreme ROE / ROI / return on tangible equity (above 100 percent in size) | 13 row(s) | Kept. These three columns are not used as model features |
