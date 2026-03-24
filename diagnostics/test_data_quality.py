"""
diagnostics/test_data_quality.py — Validate Shiller data against refcard expectations.

Checks:
  - T = 1,680 observations
  - Date range: Jan 1871 – Dec 2010
  - No NaN values
  - P/D ratio in sensible range (level, not log)
  - r0 and minimum window size match paper
"""

import sys
sys.path.insert(0, ".")

from src.config import StrategyConfig
from src.data import fetch_shiller_data


def run_checks():
    config = StrategyConfig()
    df = fetch_shiller_data(config)
    T = len(df)
    errors = []

    # 1. Observation count
    if T != 1680:
        errors.append(f"FAIL: T = {T}, expected 1680")
    else:
        print(f"PASS: T = {T}")

    # 2. Date range
    first = df["date"].min()
    last = df["date"].max()
    if first.year != 1871 or first.month != 1:
        errors.append(f"FAIL: Start date = {first}, expected 1871-01")
    else:
        print(f"PASS: Start date = {first.strftime('%Y-%m')}")

    if last.year != 2010 or last.month != 12:
        errors.append(f"FAIL: End date = {last}, expected 2010-12")
    else:
        print(f"PASS: End date = {last.strftime('%Y-%m')}")

    # 3. No NaNs
    nan_count = df.isna().sum().sum()
    if nan_count > 0:
        errors.append(f"FAIL: {nan_count} NaN values found")
    else:
        print("PASS: No NaN values")

    # 4. P/D ratio sanity (level, should be roughly 5-100)
    pd_min = df["pd_ratio"].min()
    pd_max = df["pd_ratio"].max()
    pd_mean = df["pd_ratio"].mean()
    if pd_min < 1 or pd_max > 200:
        errors.append(f"FAIL: P/D ratio range [{pd_min:.2f}, {pd_max:.2f}] looks wrong")
    else:
        print(f"PASS: P/D ratio range [{pd_min:.2f}, {pd_max:.2f}], mean={pd_mean:.2f}")

    # 5. r0 and minimum window
    r0 = config.compute_r0(T)
    min_win = config.compute_min_window(T)
    if not (0.050 < r0 < 0.060):
        errors.append(f"FAIL: r0 = {r0:.4f}, expected ~0.054")
    else:
        print(f"PASS: r0 = {r0:.4f}")

    if min_win != 90:
        errors.append(f"FAIL: min_window = {min_win}, expected 90")
    else:
        print(f"PASS: min_window = {min_win}")

    # 6. Monotonic dates
    if not df["date"].is_monotonic_increasing:
        errors.append("FAIL: Dates are not monotonically increasing")
    else:
        print("PASS: Dates monotonically increasing")

    # Summary
    print(f"\n{'='*40}")
    if errors:
        for e in errors:
            print(e)
        print(f"\n{len(errors)} check(s) FAILED")
        return False
    else:
        print("All checks PASSED")
        return True


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
