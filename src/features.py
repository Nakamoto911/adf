"""
src/features.py — ADF test statistics for PSY (2015) bubble detection.

Implements:
  - Rolling ADF regression (t-ratio of β̂) via prefix-sum optimization
  - BSADF sequence (backward sup ADF for date-stamping)
  - SADF statistic (PWY test)
  - GSADF statistic (PSY test)

Reference: refcard.md for all formulas and hyperparameters.

Performance: prefix sums give O(1) per ADF stat after O(T) preprocessing.
Inner loops over r1 are fully vectorized with numpy.
"""

import numpy as np
from src.config import StrategyConfig


class ADFPrefixSums:
    """
    Precompute prefix sums for O(1) ADF t-stat evaluation on any subsample.

    For the ADF regression with k=0 lags on window y[r1:r2+1]:
        Δy_t = α + β·y_{t-1} + ε_t

    The effective sample has n = r2 - r1 observations, with:
        dep = Δy_t for t in [r1+1, r2]
        regressor = y_{t-1} for t in [r1+1, r2], i.e. y[r1:r2]
    """

    def __init__(self, y: np.ndarray):
        T = len(y)
        self.y = y
        self.T = T

        # Prefix sums (length T+1, index k means sum of elements 0..k-1)
        # S[k] = Σ_{t=0}^{k-1} y[t]
        self.S = np.zeros(T + 1)
        self.S[1:] = np.cumsum(y)

        # S2[k] = Σ_{t=0}^{k-1} y[t]²
        self.S2 = np.zeros(T + 1)
        self.S2[1:] = np.cumsum(y ** 2)

        # Sxy[k] = Σ_{t=0}^{k-1} y[t]·y[t+1]  (length T, valid for k up to T-1)
        prods = y[:-1] * y[1:]
        self.Sxy = np.zeros(T)
        self.Sxy[1:] = np.cumsum(prods)

        # Sd2[k] = Σ_{t=0}^{k-1} (y[t+1]-y[t])²  (length T)
        diffs2 = np.diff(y) ** 2
        self.Sd2 = np.zeros(T)
        self.Sd2[1:] = np.cumsum(diffs2)

    def adf_tstat(self, r1: int, r2: int) -> float:
        """Compute ADF t-stat for window y[r1:r2+1] in O(1)."""
        n = r2 - r1  # effective obs count
        if n < 3:
            return np.nan

        sx = self.S[r2] - self.S[r1]
        sx2 = self.S2[r2] - self.S2[r1]
        sdy = self.y[r2] - self.y[r1]  # telescoping sum
        sxdy = (self.Sxy[r2] - self.Sxy[r1]) - (self.S2[r2] - self.S2[r1])
        sdy2 = self.Sd2[r2] - self.Sd2[r1]

        det = n * sx2 - sx * sx
        if det == 0:
            return np.nan

        beta1 = (n * sxdy - sx * sdy) / det
        beta0 = (sdy - beta1 * sx) / n

        rss = sdy2 - beta0 * sdy - beta1 * sxdy
        if rss <= 0:
            return np.nan

        s2 = rss / (n - 2)
        var_beta1 = s2 * n / det
        if var_beta1 <= 0:
            return np.nan

        return beta1 / np.sqrt(var_beta1)

    def bsadf_at_r2_vectorized(self, r2: int, min_win: int) -> float:
        """
        Compute BSADF(r2) = sup_{r1 ∈ [0, r2-min_win]} ADF(r1, r2).
        Vectorized over all r1 values.
        """
        r1_max = r2 - min_win
        if r1_max < 0:
            return np.nan

        r1_vals = np.arange(0, r1_max + 1)
        n = r2 - r1_vals  # effective obs count per window

        sx = self.S[r2] - self.S[r1_vals]
        sx2 = self.S2[r2] - self.S2[r1_vals]
        sdy = self.y[r2] - self.y[r1_vals]
        sxdy = (self.Sxy[r2] - self.Sxy[r1_vals]) - (self.S2[r2] - self.S2[r1_vals])
        sdy2 = self.Sd2[r2] - self.Sd2[r1_vals]

        det = n * sx2 - sx * sx

        # Mask degenerate cases
        valid = (det != 0) & (n >= 3)

        beta1 = np.where(valid, (n * sxdy - sx * sdy) / np.where(valid, det, 1), np.nan)
        beta0 = np.where(valid, (sdy - beta1 * sx) / n, np.nan)

        rss = np.where(valid, sdy2 - beta0 * sdy - beta1 * sxdy, np.nan)
        valid = valid & (rss > 0)

        s2 = np.where(valid, rss / (n - 2), np.nan)
        var_beta1 = np.where(valid, s2 * n / np.where(valid, det, 1), np.nan)
        valid = valid & (var_beta1 > 0)

        t_stats = np.where(valid, beta1 / np.sqrt(np.where(valid, var_beta1, 1)), -np.inf)

        if not np.any(valid):
            return np.nan
        return np.max(t_stats)


def bsadf_sequence(y: np.ndarray, r0: float, lag: int = 0) -> np.ndarray:
    """
    Compute the BSADF sequence for date-stamping.

    For each r2 from r0 to 1:
        BSADF(r2) = sup_{r1 ∈ [0, r2-r0]} ADF(r1, r2)

    Returns array of length T with np.nan before first computable r2.
    """
    T = len(y)
    min_win = int(np.floor(T * r0))
    ps = ADFPrefixSums(y)
    bsadf = np.full(T, np.nan)

    for r2_idx in range(min_win, T):
        bsadf[r2_idx] = ps.bsadf_at_r2_vectorized(r2_idx, min_win)

    return bsadf


def sadf_stat(y: np.ndarray, r0: float, lag: int = 0) -> float:
    """
    SADF (PWY) test statistic.
    SADF(r0) = sup_{r2 ∈ [r0, 1]} ADF(0, r2)
    """
    T = len(y)
    min_win = int(np.floor(T * r0))
    ps = ADFPrefixSums(y)
    sup_adf = -np.inf

    for r2_idx in range(min_win, T):
        stat = ps.adf_tstat(0, r2_idx)
        if not np.isnan(stat) and stat > sup_adf:
            sup_adf = stat

    return sup_adf if sup_adf > -np.inf else np.nan


def gsadf_stat(y: np.ndarray, r0: float, lag: int = 0) -> float:
    """
    GSADF (PSY) test statistic — supremum of the BSADF sequence.
    """
    bsadf = bsadf_sequence(y, r0, lag)
    valid = bsadf[~np.isnan(bsadf)]
    return np.max(valid) if len(valid) > 0 else np.nan


def compute_all_stats(y: np.ndarray, config: StrategyConfig):
    """
    Compute SADF, GSADF, and full BSADF sequence.

    Returns dict with keys: 'sadf', 'gsadf', 'bsadf_sequence', 'r0', 'T'
    """
    T = len(y)
    r0 = config.compute_r0(T)
    lag = config.lag_order
    min_win = int(np.floor(T * r0))
    ps = ADFPrefixSums(y)

    # BSADF sequence (vectorized)
    bsadf = np.full(T, np.nan)
    for r2_idx in range(min_win, T):
        bsadf[r2_idx] = ps.bsadf_at_r2_vectorized(r2_idx, min_win)

    # SADF: sup of ADF(0, r2) over r2
    sadf_vals = np.array([ps.adf_tstat(0, r2) for r2 in range(min_win, T)])
    sadf_val = np.nanmax(sadf_vals)

    # GSADF: sup of BSADF
    gsadf_val = np.nanmax(bsadf)

    return {
        "sadf": sadf_val,
        "gsadf": gsadf_val,
        "bsadf_sequence": bsadf,
        "r0": r0,
        "T": T,
    }


def bsadf_sequence_fast(y: np.ndarray, min_win: int) -> np.ndarray:
    """
    Fast BSADF computation for Monte Carlo use (skips config overhead).
    Returns array of length T.
    """
    T = len(y)
    ps = ADFPrefixSums(y)
    bsadf = np.full(T, np.nan)

    for r2_idx in range(min_win, T):
        bsadf[r2_idx] = ps.bsadf_at_r2_vectorized(r2_idx, min_win)

    return bsadf
