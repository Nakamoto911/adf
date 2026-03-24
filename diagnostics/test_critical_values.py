"""
diagnostics/test_critical_values.py — Compare MC critical values to paper Table 8.

Checks that our simulated CVs are within reasonable tolerance of the paper's
finite-sample values (T=1,680, Table 8).
"""

import sys
sys.path.insert(0, ".")

from src.config import StrategyConfig
from src.models import simulate_critical_values


def run_checks():
    config = StrategyConfig()
    cv = simulate_critical_values(config, verbose=False)
    errors = []

    # Paper Table 8 finite-sample T=1,680
    paper = {
        "sadf": {0.90: 1.30, 0.95: 1.59, 0.99: 2.14},
        "gsadf": {0.90: 2.17, 0.95: 2.34, 0.99: 2.74},
    }

    # Tolerance: MC with 2000 reps has sampling error ~0.3 for tail quantiles
    tol = 0.35

    for test in ["sadf", "gsadf"]:
        for q in [0.90, 0.95, 0.99]:
            ours = cv[f"{test}_cv"][q]
            theirs = paper[test][q]
            diff = abs(ours - theirs)
            status = "PASS" if diff < tol else "FAIL"
            msg = f"{status}: {test.upper()} {int(q*100)}% = {ours:.2f} (paper: {theirs:.2f}, diff={diff:.2f})"
            print(msg)
            if diff >= tol:
                errors.append(msg)

    # Check BSADF CV sequence exists and has correct shape
    bsadf_cv_95 = cv["bsadf_cv"][0.95]
    T = cv["T"]
    if len(bsadf_cv_95) != T:
        errors.append(f"FAIL: BSADF CV length = {len(bsadf_cv_95)}, expected {T}")
    else:
        print(f"PASS: BSADF CV sequence length = {T}")

    import numpy as np
    valid = ~np.isnan(bsadf_cv_95)
    n_valid = np.sum(valid)
    expected_valid = T - cv["min_win"]
    if n_valid != expected_valid:
        errors.append(f"FAIL: BSADF CV valid count = {n_valid}, expected {expected_valid}")
    else:
        print(f"PASS: BSADF CV valid entries = {n_valid}")

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
