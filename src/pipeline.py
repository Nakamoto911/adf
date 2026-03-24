"""
src/pipeline.py — Orchestrator for PSY (2015) bubble detection pipeline.

Imports from all src/ modules and executes the end-to-end run:
  1. Fetch Shiller data and compute P/D ratio
  2. Compute BSADF sequence, SADF, GSADF
  3. Load or generate Monte Carlo critical values
  4. Date-stamp bubble episodes
  5. Return consolidated results
"""

from src.config import StrategyConfig
from src import data, features, models, backtest


def run(config: StrategyConfig) -> dict:
    """Execute the full PSY bubble detection pipeline."""

    # 1. Data
    df = data.fetch_shiller_data(config)
    y = df["pd_ratio"].values
    dates = df["date"].values
    T = len(y)

    # 2. Test statistics
    stats = features.compute_all_stats(y, config)

    # 3. Critical values
    cv = models.simulate_critical_values(config, T=T, verbose=False)

    # 4. Date-stamping
    cv_seq = cv["bsadf_cv"][1.0 - config.significance_level]
    episodes = backtest.date_stamp_bubbles(
        stats["bsadf_sequence"], cv_seq, dates, config
    )

    return {
        "df": df,
        "y": y,
        "dates": dates,
        "T": T,
        "sadf": stats["sadf"],
        "gsadf": stats["gsadf"],
        "bsadf_sequence": stats["bsadf_sequence"],
        "r0": stats["r0"],
        "cv": cv,
        "cv_sequence": cv_seq,
        "episodes": episodes,
        "config": config,
    }


def print_summary(results: dict) -> None:
    """Print a summary of pipeline results."""
    print(f"\nPSY (2015) Replication Results")
    print("=" * 60)
    print(f"Sample: T={results['T']}, r0={results['r0']:.4f}")
    print(f"SADF  = {results['sadf']:.2f}  (paper: 3.30)")
    print(f"GSADF = {results['gsadf']:.2f}  (paper: 4.21)")

    models.print_cv_summary(results["cv"])
    backtest.print_episodes(results["episodes"])
    backtest.print_comparison(results["episodes"])
