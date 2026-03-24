# Diagnostic & Test Registry
*Register all standalone tests, data audits, and ML health scripts located in this folder here.*

| Script | Description |
|--------|-------------|
| `test_data_quality.py` | Validates Shiller data: T=1680, date range, no NaNs, P/D ratio sanity, r0/min_window match paper |
| `test_adf_regression.py` | Unit tests ADF on known series (random walk, explosive, stationary), verifies prefix-sum matches naive OLS |
| `test_critical_values.py` | Compares MC critical values to paper Table 8 (SADF/GSADF at 90/95/99%) |
| `test_bubble_dates.py` | Compares detected bubble episodes to paper Figure 7's 7 episodes |
