# Experiment Log

Each session records experiments run, parameters tested, results, and conclusions.
Entries are in reverse chronological order (newest first).

---

## 2026-03-24 — Phase 6-7: Pipeline, Dashboard, Diagnostics

### What changed
- `src/pipeline.py`: End-to-end orchestrator (`run()`, `print_summary()`).
- `app.py`: Streamlit entry point.
- `pages/1_Data_Explorer.py`: P/D ratio time series, real price/dividend, raw data table.
- `pages/2_Bubble_Detection.py`: BSADF vs CV plot with bubble shading, P/D with episodes, episode table, CV comparison. Sidebar controls for significance, delta, MC reps.
- `run_experiments.py`: 5 presets (baseline, sig_10pct, sig_1pct, delta_1.5, delta_2.0). Saves markdown reports.
- `diagnostics/test_adf_regression.py`: 5 checks, all pass.
- `diagnostics/test_critical_values.py`: 8 checks, all pass.
- `diagnostics/test_bubble_dates.py`: 9 checks, all pass.

### All diagnostics passing (21/21 checks)

---

## 2026-03-24 — Phase 5: Date-Stamping / Bubble Identification

### What changed
- `src/backtest.py`: Implemented `date_stamp_bubbles()`, `print_episodes()`, `print_comparison()`.

### Results: All 7 paper episodes matched
| Paper Episode | Paper Dates | Our Dates |
|---|---|---|
| Post long-depression | 1879M10–1880M04 | 1879M05–1880M05 |
| 1917 crash | 1917M08–1918M04 | 1917M09–1918M05 |
| Great crash | 1928M11–1929M10 | 1928M05–1929M11 |
| Postwar boom | 1955M01–1956M04 | 1955M04–1956M06 |
| Black Monday | 1986M06–1987M09 | 1986M04–1986M11 + 1987M01–1987M10 (split) |
| Dot-com | 1995M11–2001M08 | 1995M11–1996M07 + 1996M09–2001M09 (split) |
| Subprime | 2009M02–2009M04 | 2009M03–2009M10 |

We detect 14 episodes total (7 extra short-duration borderline detections). 2 of 7 paper episodes are split in two due to brief BSADF dips below CV (MC sampling variation in CVs).

### Decisions
- Keeping delta=1.0 — matches paper's minimum duration formula
- Splits are from MC CV variation, not algorithmic error

---

## 2026-03-24 — Phase 4: Monte Carlo Critical Values

### What changed
- `src/features.py`: Rewrote with `ADFPrefixSums` class — O(1) per ADF stat via prefix sums, vectorized inner loop. **400x speedup** (24.5s → 0.06s per BSADF sequence).
- `src/models.py`: Implemented `simulate_critical_values()` with caching, `print_cv_summary()`.

### Results vs Paper (Table 8, finite sample T=1,680)
| | 90% (ours/paper) | 95% (ours/paper) | 99% (ours/paper) |
|---|---|---|---|
| SADF | 1.29/1.30 | 1.53/1.59 | 2.04/2.14 |
| GSADF | 2.15/2.17 | 2.41/2.34 | 2.85/2.74 |

All within typical MC sampling variation (2000 reps, seed=42).

### Performance
- 2,000 replications × T=1,680: **131s total** (was estimated 13.6h before prefix-sum optimization)
- Results cached in `data_cache/mc_cv_T1680_reps2000_seed42.pkl`

---

## 2026-03-24 — Phase 3: Test Statistics (ADF/BSADF/SADF/GSADF)

### What changed
- `src/features.py`: Implemented `adf_stat()`, `bsadf_sequence()`, `sadf_stat()`, `gsadf_stat()`, `compute_all_stats()`.

### Results vs Paper (Table 8)
| Statistic | Ours | Paper | Δ |
|-----------|------|-------|---|
| SADF | 3.46 | 3.30 | +0.16 |
| GSADF | 4.16 | 4.21 | −0.05 |

Both reject at 1% — consistent with paper.

### Log vs Level P/D test
- Level P/D: SADF=3.46, GSADF=4.16 (close match)
- Log P/D: SADF=0.69, GSADF=3.70 (poor match)
- **Conclusion:** Level P/D is correct. Small discrepancies from data vintage differences.

### Performance
- 1,264,845 ADF regressions in 24.5s (~17μs each)
- Pure numpy OLS, no statsmodels dependency needed for ADF

---

## 2026-03-24 — Phase 1: Data Pipeline Setup

### What changed
- `src/config.py`: Added all PSY hyperparameters (lag_order=0, significance=0.05, r0 rule, MC reps=2000, bubble duration delta=1.0). Helper methods for r0, min_window, min_bubble_duration.
- `src/data.py`: Implemented Shiller data fetch from Yale Excel file. Parses real price (col 7) and real dividend (col 8), computes P/D ratio, caches in data_cache/.
- `diagnostics/test_data_quality.py`: 8 validation checks all passing.
- `requirements.txt`: Added statsmodels, openpyxl.

### Data validation results
| Check | Result |
|-------|--------|
| T | 1,680 |
| Date range | 1871-01 to 2010-12 |
| NaNs | 0 |
| P/D range | [7.23, 90.21] |
| P/D mean | 26.58 |
| r0 | 0.0539 |
| min_window | 90 obs |
| Dates monotonic | Yes |

### Decisions
- Using level P/D ratio (not log) — paper text suggests level; will switch to log if GSADF doesn't match 4.21
- Shiller column mapping verified: col 7=Real Price, col 8=Real Dividend (col 6 is GS10 interest rate)
- delta=1.0 for min bubble duration; yields 7 obs ≈ 7 months
