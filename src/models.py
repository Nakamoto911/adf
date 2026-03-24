"""
src/models.py — Monte Carlo critical value simulation for PSY (2015).

Simulates random walks under H0 (unit root with no drift, k=0 lags) and
computes empirical quantiles for SADF, GSADF, and the BSADF date-stamping
critical value sequence.

Reference: refcard.md — 2,000 replications, T = 1,680.
"""

import numpy as np
from pathlib import Path

from src.config import StrategyConfig
from src.features import bsadf_sequence_fast, ADFPrefixSums

CACHE_DIR = Path("data_cache")


def simulate_critical_values(
    config: StrategyConfig,
    T: int = 1680,
    seed: int = 42,
    verbose: bool = True,
) -> dict:
    """
    Monte Carlo simulation of critical values under H0 (driftless random walk).

    For each replication:
      1. Generate y_t = y_{t-1} + ε_t, ε_t ~ N(0,1)
      2. Compute BSADF sequence, SADF, GSADF

    From the distribution across replications, extract quantiles.

    Parameters
    ----------
    config : StrategyConfig
    T : sample size (default 1680 to match paper)
    seed : random seed for reproducibility
    verbose : print progress

    Returns
    -------
    dict with keys:
        'bsadf_cv': dict of {quantile: array} — CV sequence for date-stamping
        'sadf_cv': dict of {quantile: float} — scalar CVs
        'gsadf_cv': dict of {quantile: float} — scalar CVs
        'n_reps': number of replications
        'T': sample size
    """
    cache_file = CACHE_DIR / f"mc_cv_T{T}_reps{config.mc_replications}_seed{seed}.pkl"
    CACHE_DIR.mkdir(exist_ok=True)

    if cache_file.exists():
        import pickle
        with open(cache_file, "rb") as f:
            cached = pickle.load(f)
        if verbose:
            print(f"Loaded cached critical values from {cache_file}")
        return cached

    rng = np.random.default_rng(seed)
    n_reps = config.mc_replications
    r0 = config.compute_r0(T)
    min_win = int(np.floor(T * r0))
    quantiles = [0.90, 0.95, 0.99]

    # Storage: BSADF sequences, SADF and GSADF scalars
    bsadf_matrix = np.full((n_reps, T), np.nan)
    sadf_vals = np.full(n_reps, np.nan)
    gsadf_vals = np.full(n_reps, np.nan)

    for rep in range(n_reps):
        # Generate driftless random walk: y_t = y_{t-1} + ε_t
        eps = rng.standard_normal(T)
        y = np.cumsum(eps)

        # BSADF sequence
        bsadf = bsadf_sequence_fast(y, min_win)
        bsadf_matrix[rep] = bsadf

        # SADF: sup of ADF(0, r2) for r2 in [min_win, T)
        ps = ADFPrefixSums(y)
        sadf_max = -np.inf
        for r2 in range(min_win, T):
            stat = ps.adf_tstat(0, r2)
            if not np.isnan(stat) and stat > sadf_max:
                sadf_max = stat
        sadf_vals[rep] = sadf_max

        # GSADF: sup of BSADF
        valid_bsadf = bsadf[~np.isnan(bsadf)]
        gsadf_vals[rep] = np.max(valid_bsadf) if len(valid_bsadf) > 0 else np.nan

        if verbose and (rep + 1) % 200 == 0:
            print(f"  MC rep {rep + 1}/{n_reps}")

    # Compute quantiles
    bsadf_cv = {}
    for q in quantiles:
        bsadf_cv[q] = np.nanquantile(bsadf_matrix, q, axis=0)

    sadf_cv = {q: np.nanquantile(sadf_vals, q) for q in quantiles}
    gsadf_cv = {q: np.nanquantile(gsadf_vals, q) for q in quantiles}

    result = {
        "bsadf_cv": bsadf_cv,
        "sadf_cv": sadf_cv,
        "gsadf_cv": gsadf_cv,
        "n_reps": n_reps,
        "T": T,
        "r0": r0,
        "min_win": min_win,
    }

    # Cache
    import pickle
    with open(cache_file, "wb") as f:
        pickle.dump(result, f)
    if verbose:
        print(f"Saved critical values to {cache_file}")

    return result


def print_cv_summary(cv_result: dict) -> None:
    """Print critical value summary matching paper Table 8 format."""
    print(f"\nMonte Carlo Critical Values (T={cv_result['T']}, "
          f"reps={cv_result['n_reps']}, r0={cv_result['r0']:.4f})")
    print("=" * 50)

    print("\n         90%      95%      99%")
    print(f"SADF   {cv_result['sadf_cv'][0.90]:7.2f}  "
          f"{cv_result['sadf_cv'][0.95]:7.2f}  "
          f"{cv_result['sadf_cv'][0.99]:7.2f}")
    print(f"GSADF  {cv_result['gsadf_cv'][0.90]:7.2f}  "
          f"{cv_result['gsadf_cv'][0.95]:7.2f}  "
          f"{cv_result['gsadf_cv'][0.99]:7.2f}")

    print("\nPaper Table 8 (finite sample T=1,680):")
    print("         90%      95%      99%")
    print(f"SADF     1.30     1.59     2.14")
    print(f"GSADF    2.17     2.34     2.74")
