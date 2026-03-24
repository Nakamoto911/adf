"""
diagnostics/test_adf_regression.py — Unit tests for ADF regression on known series.

Tests:
  - Random walk: ADF stat should be negative (unit root)
  - Explosive process: ADF stat should be positive
  - Stationary AR(1): ADF stat should be strongly negative
  - Prefix-sum ADF matches naive OLS ADF
"""

import sys
sys.path.insert(0, ".")

import numpy as np


def run_checks():
    from src.features import ADFPrefixSums
    errors = []
    rng = np.random.default_rng(42)

    # 1. Random walk: ADF stat should be < 0 (non-rejection of unit root)
    rw = np.cumsum(rng.standard_normal(500))
    ps = ADFPrefixSums(rw)
    stat_rw = ps.adf_tstat(0, 499)
    if stat_rw >= 0:
        errors.append(f"FAIL: Random walk ADF = {stat_rw:.3f}, expected < 0")
    else:
        print(f"PASS: Random walk ADF = {stat_rw:.3f} (< 0)")

    # 2. Explosive process: ADF stat should be >> 0
    y_exp = np.zeros(200)
    y_exp[0] = 100
    for t in range(1, 200):
        y_exp[t] = 1.02 * y_exp[t - 1] + rng.standard_normal()
    ps_exp = ADFPrefixSums(y_exp)
    stat_exp = ps_exp.adf_tstat(0, 199)
    if stat_exp <= 0:
        errors.append(f"FAIL: Explosive ADF = {stat_exp:.3f}, expected > 0")
    else:
        print(f"PASS: Explosive ADF = {stat_exp:.3f} (> 0)")

    # 3. Stationary AR(1): ADF stat should be << -2
    y_stat = np.zeros(500)
    for t in range(1, 500):
        y_stat[t] = 0.5 * y_stat[t - 1] + rng.standard_normal()
    ps_stat = ADFPrefixSums(y_stat)
    stat_stat = ps_stat.adf_tstat(0, 499)
    if stat_stat >= -2:
        errors.append(f"FAIL: Stationary ADF = {stat_stat:.3f}, expected << -2")
    else:
        print(f"PASS: Stationary ADF = {stat_stat:.3f} (<< -2)")

    # 4. Prefix-sum ADF matches naive OLS ADF
    y_test = np.cumsum(rng.standard_normal(100))
    ps_test = ADFPrefixSums(y_test)

    # Naive OLS for comparison
    dy = np.diff(y_test[10:80])
    y_lag = y_test[10:79]
    X = np.column_stack([np.ones(len(dy)), y_lag])
    beta = np.linalg.lstsq(X, dy, rcond=None)[0]
    resid = dy - X @ beta
    s2 = np.dot(resid, resid) / (len(dy) - 2)
    cov = s2 * np.linalg.inv(X.T @ X)
    naive_stat = beta[1] / np.sqrt(cov[1, 1])

    prefix_stat = ps_test.adf_tstat(10, 79)
    diff = abs(naive_stat - prefix_stat)
    if diff > 1e-8:
        errors.append(f"FAIL: Prefix={prefix_stat:.8f} vs Naive={naive_stat:.8f}, diff={diff:.2e}")
    else:
        print(f"PASS: Prefix matches naive OLS (diff={diff:.2e})")

    # 5. Subsample consistency: different windows give different stats
    stat_a = ps_test.adf_tstat(0, 50)
    stat_b = ps_test.adf_tstat(0, 99)
    stat_c = ps_test.adf_tstat(30, 99)
    if stat_a == stat_b == stat_c:
        errors.append("FAIL: All subsample stats identical (should vary)")
    else:
        print(f"PASS: Subsample stats vary ({stat_a:.3f}, {stat_b:.3f}, {stat_c:.3f})")

    # Summary
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
