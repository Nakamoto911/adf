"""
src/backtest.py — Bubble date-stamping for PSY (2015).

Compares the BSADF sequence against the Monte Carlo critical value sequence
to identify bubble origination and termination dates.

Algorithm (refcard Pipeline steps 5-7):
  - Origination: r̂_e = inf{r2 : BSADF(r2) > scv(r2)}
  - Termination: r̂_f = inf{r2 >= r̂_e + δ·log(T)/T : BSADF(r2) < scv(r2)}
  - After termination, repeat to find subsequent bubbles.
  - Minimum bubble duration: δ·log(T) observations.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass

from src.config import StrategyConfig


@dataclass
class BubbleEpisode:
    start_idx: int
    end_idx: int
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    duration: int  # in observations
    peak_bsadf: float


def date_stamp_bubbles(
    bsadf: np.ndarray,
    cv_sequence: np.ndarray,
    dates: np.ndarray,
    config: StrategyConfig,
) -> list[BubbleEpisode]:
    """
    Identify bubble episodes by comparing BSADF to critical value sequence.

    Parameters
    ----------
    bsadf : BSADF sequence (length T, NaN before first computable r2)
    cv_sequence : Critical value sequence at chosen significance level (length T)
    dates : Array of pd.Timestamp (length T)
    config : StrategyConfig (for min bubble duration)

    Returns
    -------
    List of BubbleEpisode objects
    """
    T = len(bsadf)
    min_dur = config.compute_min_bubble_duration(T)
    # Minimum gap after origination before termination can be declared
    # δ·log(T)/T expressed as index offset: δ·log(T) observations
    min_gap = min_dur

    episodes = []
    t = 0

    while t < T:
        # Skip NaN regions
        if np.isnan(bsadf[t]) or np.isnan(cv_sequence[t]):
            t += 1
            continue

        # Step 5: Find origination — first t where BSADF > CV
        if bsadf[t] > cv_sequence[t]:
            start_idx = t

            # Step 6: Find termination — first t after start + min_gap where BSADF < CV
            end_idx = None
            search_from = start_idx + min_gap

            for s in range(search_from, T):
                if np.isnan(bsadf[s]) or np.isnan(cv_sequence[s]):
                    continue
                if bsadf[s] < cv_sequence[s]:
                    end_idx = s
                    break

            # If no termination found, bubble runs to end of sample
            if end_idx is None:
                end_idx = T - 1

            duration = end_idx - start_idx
            if duration >= min_dur:
                peak = np.nanmax(bsadf[start_idx : end_idx + 1])
                episodes.append(BubbleEpisode(
                    start_idx=start_idx,
                    end_idx=end_idx,
                    start_date=dates[start_idx],
                    end_date=dates[end_idx],
                    duration=duration,
                    peak_bsadf=peak,
                ))

            # Step 7: Resume search after termination
            t = end_idx + 1
        else:
            t += 1

    return episodes


def print_episodes(episodes: list[BubbleEpisode]) -> None:
    """Print detected episodes in a table format matching paper Figure 7."""
    print(f"\nDetected Bubble Episodes ({len(episodes)} total)")
    print("=" * 70)
    print(f"{'#':<4} {'Start':<12} {'End':<12} {'Duration':<10} {'Peak BSADF':<12}")
    print("-" * 70)
    for i, ep in enumerate(episodes, 1):
        start_str = _fmt_date(ep.start_date)
        end_str = _fmt_date(ep.end_date)
        print(f"{i:<4} {start_str:<12} {end_str:<12} {ep.duration:<10} {ep.peak_bsadf:<12.2f}")


def print_comparison(episodes: list[BubbleEpisode]) -> None:
    """Print comparison against paper's Figure 7 episodes."""
    paper_episodes = [
        ("Post long-depression", "1879M10", "1880M04"),
        ("1917 crash (downturn)", "1917M08", "1918M04"),
        ("Great crash", "1928M11", "1929M10"),
        ("Postwar boom", "1955M01", "1956M04"),
        ("Black Monday", "1986M06", "1987M09"),
        ("Dot-com bubble", "1995M11", "2001M08"),
        ("Subprime (downturn)", "2009M02", "2009M04"),
    ]

    print(f"\nComparison with Paper (Figure 7)")
    print("=" * 80)
    print(f"{'Paper Episode':<25} {'Paper Start':<12} {'Paper End':<12} {'Our Match'}")
    print("-" * 80)

    for name, p_start, p_end in paper_episodes:
        # Find closest matching episode by date overlap
        match = _find_match(episodes, p_start, p_end)
        if match:
            m_start = _fmt_date(match.start_date)
            m_end = _fmt_date(match.end_date)
            print(f"{name:<25} {p_start:<12} {p_end:<12} {m_start}–{m_end}")
        else:
            print(f"{name:<25} {p_start:<12} {p_end:<12} MISSED")


def _fmt_date(d) -> str:
    """Format date as YYYYMmm regardless of type."""
    ts = pd.Timestamp(d)
    return ts.strftime("%YM%m")


def _find_match(
    episodes: list[BubbleEpisode], paper_start: str, paper_end: str
) -> BubbleEpisode | None:
    """Find episode overlapping with paper's date range (within 24 months)."""
    ps = pd.Timestamp(paper_start.replace("M", "-") + "-01")
    pe = pd.Timestamp(paper_end.replace("M", "-") + "-01")

    best = None
    best_overlap = -1
    for ep in episodes:
        ep_start = pd.Timestamp(ep.start_date)
        ep_end = pd.Timestamp(ep.end_date)
        # Check if within 24 months of paper dates
        if ep_end < ps - pd.DateOffset(months=24):
            continue
        if ep_start > pe + pd.DateOffset(months=24):
            continue
        # Compute overlap
        overlap_start = max(ep_start, ps)
        overlap_end = min(ep_end, pe)
        overlap = int((overlap_end - overlap_start) / np.timedelta64(1, "D"))
        if overlap > best_overlap:
            best_overlap = overlap
            best = ep

    return best
