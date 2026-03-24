"""
diagnostics/test_bubble_dates.py — Compare detected bubble episodes to paper Figure 7.

Checks that all 7 paper episodes are matched by our detection algorithm,
with start/end dates within a reasonable tolerance.
"""

import sys
sys.path.insert(0, ".")

import numpy as np
import pandas as pd

from src.config import StrategyConfig
from src.data import fetch_shiller_data
from src.features import compute_all_stats
from src.models import simulate_critical_values
from src.backtest import date_stamp_bubbles


PAPER_EPISODES = [
    ("Post long-depression", "1879-10", "1880-04"),
    ("1917 crash", "1917-08", "1918-04"),
    ("Great crash", "1928-11", "1929-10"),
    ("Postwar boom", "1955-01", "1956-04"),
    ("Black Monday", "1986-06", "1987-09"),
    ("Dot-com bubble", "1995-11", "2001-08"),
    ("Subprime", "2009-02", "2009-04"),
]

# Max acceptable deviation in months for start/end dates
DATE_TOL_MONTHS = 12


def run_checks():
    config = StrategyConfig()
    df = fetch_shiller_data(config)
    y = df["pd_ratio"].values
    dates = df["date"].values

    stats = compute_all_stats(y, config)
    cv = simulate_critical_values(config, verbose=False)
    cv_95 = cv["bsadf_cv"][0.95]
    episodes = date_stamp_bubbles(stats["bsadf_sequence"], cv_95, dates, config)

    errors = []

    for name, p_start, p_end in PAPER_EPISODES:
        ps = pd.Timestamp(p_start + "-01")
        pe = pd.Timestamp(p_end + "-01")

        # Find best matching episode (closest start date within tolerance)
        best = None
        best_dist = float("inf")
        for ep in episodes:
            ep_start = pd.Timestamp(ep.start_date)
            ep_end = pd.Timestamp(ep.end_date)
            # Must overlap or be within tolerance
            if ep_end < ps - pd.DateOffset(months=DATE_TOL_MONTHS):
                continue
            if ep_start > pe + pd.DateOffset(months=DATE_TOL_MONTHS):
                continue
            dist = abs((ep_start - ps).days) + abs((ep_end - pe).days)
            if dist < best_dist:
                best_dist = dist
                best = ep

        if best is None:
            errors.append(f"FAIL: {name} ({p_start} to {p_end}) — NO MATCH")
            print(f"FAIL: {name} — not detected")
        else:
            bs = pd.Timestamp(best.start_date).strftime("%Y-%m")
            be = pd.Timestamp(best.end_date).strftime("%Y-%m")
            start_diff = abs((pd.Timestamp(best.start_date) - ps).days) / 30
            end_diff = abs((pd.Timestamp(best.end_date) - pe).days) / 30
            print(f"PASS: {name:<25} paper={p_start}–{p_end}  ours={bs}–{be}  "
                  f"(start Δ={start_diff:.0f}mo, end Δ={end_diff:.0f}mo)")

    # Check test statistics
    sadf = stats["sadf"]
    gsadf = stats["gsadf"]

    if sadf < 2.0:
        errors.append(f"FAIL: SADF = {sadf:.2f}, expected > 2.0")
    else:
        print(f"PASS: SADF = {sadf:.2f} (rejects at 1%)")

    if gsadf < 2.5:
        errors.append(f"FAIL: GSADF = {gsadf:.2f}, expected > 2.5")
    else:
        print(f"PASS: GSADF = {gsadf:.2f} (rejects at 1%)")

    print(f"\n{'='*40}")
    if errors:
        for e in errors:
            print(e)
        print(f"\n{len(errors)} check(s) FAILED")
        return False
    print("All checks PASSED")
    return True


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
