# Strategy Replication - Session Memory

## Quick Reference
- **Paper:** PSY (2015) "Testing for Multiple Bubbles" — Phillips, Shi, Yu
- **Target:** Replicate GSADF=4.21, SADF=3.30, and 7 date-stamped bubble episodes
- **Our Best:** SADF=3.46, GSADF=4.16; all 7 paper episodes matched
- **Status:** ALL PHASES COMPLETE. 21/21 diagnostics passing.

## Core Architecture Decisions
- P/D ratio: LEVEL (not log) — confirmed; log gives wrong results
- ADF: prefix-sum O(1) optimization → 400x speedup (0.06s per BSADF sequence)
- MC: 2000 reps in 131s, cached in data_cache/
- CVs: SADF 95%=1.53 (paper 1.59), GSADF 95%=2.41 (paper 2.34)

## Completion Status
- Phase 1 (data): DONE — Shiller fetch, P/D ratio, caching
- Phase 2 (config): DONE — All hyperparameters
- Phase 3 (test stats): DONE — SADF=3.46, GSADF=4.16
- Phase 4 (MC CVs): DONE — Validated vs Table 8
- Phase 5 (date-stamping): DONE — 7/7 paper episodes matched
- Phase 6 (pipeline + dashboard): DONE — 2 Streamlit pages, 5 experiment presets
- Phase 7 (diagnostics): DONE — 4 scripts, 21 checks, all passing

## Potential Improvements
- Merge split episodes (Black Monday, Dot-com) for cleaner output
- Add SADF and Sequential PWY date-stamping (Figures 8-9)
- Add CUSUM comparison (Figure 10)
- Simulation DGPs: Evans collapsing bubble, mildly explosive (refcard Eqs 9-26)
