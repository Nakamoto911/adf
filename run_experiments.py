"""
run_experiments.py — Batch experiment runner for PSY (2015) replication.

Runs predefined experiment presets and saves results to reports/.
"""

import sys
import time
from pathlib import Path

from src.config import StrategyConfig
from src.pipeline import run, print_summary

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# --- Experiment Presets ---

PRESETS = {
    "baseline": StrategyConfig(),

    "sig_10pct": StrategyConfig(significance_level=0.10),

    "sig_1pct": StrategyConfig(significance_level=0.01),

    "delta_1.5": StrategyConfig(bubble_duration_delta=1.5),

    "delta_2.0": StrategyConfig(bubble_duration_delta=2.0),
}


def run_preset(name: str, config: StrategyConfig) -> dict:
    """Run a single experiment preset."""
    print(f"\n{'='*60}")
    print(f"Experiment: {name}")
    print(f"{'='*60}")
    t0 = time.time()
    results = run(config)
    elapsed = time.time() - t0
    print(f"Completed in {elapsed:.1f}s")
    print_summary(results)
    return results


def save_report(name: str, results: dict) -> None:
    """Save experiment results to a markdown report."""
    import pandas as pd

    path = REPORTS_DIR / f"experiment_{name}.md"
    lines = [
        f"# Experiment: {name}",
        "",
        f"- T = {results['T']}",
        f"- r0 = {results['r0']:.4f}",
        f"- Significance = {results['config'].significance_level}",
        f"- Delta = {results['config'].bubble_duration_delta}",
        f"- SADF = {results['sadf']:.2f}",
        f"- GSADF = {results['gsadf']:.2f}",
        f"- Episodes = {len(results['episodes'])}",
        "",
        "## Detected Episodes",
        "| # | Start | End | Duration | Peak BSADF |",
        "|---|-------|-----|----------|------------|",
    ]
    for i, ep in enumerate(results["episodes"], 1):
        s = pd.Timestamp(ep.start_date).strftime("%Y-%m")
        e = pd.Timestamp(ep.end_date).strftime("%Y-%m")
        lines.append(f"| {i} | {s} | {e} | {ep.duration} | {ep.peak_bsadf:.2f} |")

    path.write_text("\n".join(lines) + "\n")
    print(f"Report saved to {path}")


def main():
    if len(sys.argv) > 1:
        names = sys.argv[1:]
    else:
        names = list(PRESETS.keys())

    for name in names:
        if name not in PRESETS:
            print(f"Unknown preset: {name}. Available: {list(PRESETS.keys())}")
            continue
        results = run_preset(name, PRESETS[name])
        save_report(name, results)


if __name__ == "__main__":
    main()
