"""
src/data.py — Data fetching and caching logic for Shiller monthly S&P 500 data.

Downloads Robert Shiller's IE data (real S&P 500 price, real dividend),
computes the price-dividend ratio, and caches results in data_cache/.
"""

import os
import glob
import hashlib
import datetime
import pickle
from pathlib import Path

import pandas as pd
import numpy as np

from src.config import StrategyConfig

CACHE_DIR = Path("data_cache")


def _cache_path(start: str, end: str) -> Path:
    """Generate a deterministic cache filename from date range."""
    tag = hashlib.md5(f"shiller_{start}_{end}".encode()).hexdigest()[:10]
    return CACHE_DIR / f"shiller_{start}_{end}_{tag}.pkl"


def _clean_old_cache(keep: Path) -> None:
    """Remove old Shiller cache files, keeping only the current one."""
    for f in CACHE_DIR.glob("shiller_*.pkl"):
        if f != keep:
            f.unlink()


def _is_stale(cache_file: Path, requested_end: str) -> bool:
    """Cache is stale if the requested end date is >7 days beyond what's cached."""
    if not cache_file.exists():
        return True
    try:
        cached_df = pd.read_pickle(cache_file)
        cached_end = cached_df["date"].max()
        requested = pd.Timestamp(requested_end + "-01")
        return (requested - cached_end).days > 7
    except Exception:
        return True


def fetch_shiller_data(config: StrategyConfig) -> pd.DataFrame:
    """
    Download Shiller's monthly IE data, compute P/D ratio, filter to date range.

    Returns DataFrame with columns: date, real_price, real_dividend, pd_ratio
    Index is sequential integer (not date).
    """
    cache_file = _cache_path(config.start_date, config.end_date)
    CACHE_DIR.mkdir(exist_ok=True)

    if not _is_stale(cache_file, config.end_date):
        return pd.read_pickle(cache_file)

    # --- Download and parse ---
    raw = _download_shiller(config.shiller_url)
    df = _parse_shiller(raw, config.start_date, config.end_date)

    # --- Cache ---
    df.to_pickle(cache_file)
    _clean_old_cache(keep=cache_file)

    return df


def _download_shiller(url: str) -> pd.DataFrame:
    """Download the Shiller IE Excel file and return the raw 'Data' sheet."""
    raw = pd.read_excel(url, sheet_name="Data", header=None)
    return raw


def _parse_shiller(raw: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """
    Parse Shiller's IE data sheet.

    The Excel layout has a header region; actual data rows have a numeric
    year.month value in column 0 (e.g. 1871.01). We detect the data region
    by looking for rows where column 0 is numeric and > 1800.

    Relevant columns (0-indexed):
      0: Date (year.month fraction, e.g. 2000.01)
      1: S&P Composite Price (nominal)
      2: Dividend (nominal, 12-month moving sum)
      3: Earnings
      4: CPI
      5: Date fraction (duplicate)
      6: Real Price (= col1 * CPI_base / col4)
      7: Real Dividend (= col2 * CPI_base / col4)
      8: Real Total Return Price
      9: Real Earnings
     10: Real TR Scaled Earnings
    """
    # Find header row: look for "Date" in column 0
    data_start = None
    for i, val in enumerate(raw.iloc[:, 0]):
        try:
            v = float(val)
            if v > 1800:
                data_start = i
                break
        except (ValueError, TypeError):
            continue

    if data_start is None:
        raise ValueError("Could not locate data start row in Shiller spreadsheet")

    df = raw.iloc[data_start:].copy()
    df.columns = range(df.shape[1])

    # Keep only rows with valid numeric date
    df = df[pd.to_numeric(df[0], errors="coerce").notna()].copy()
    df[0] = df[0].astype(float)

    # Parse date: year.month_fraction -> proper datetime
    def parse_date(val):
        year = int(val)
        # Month is encoded as fraction: .01=Jan, .1=Oct, .11=Nov, .12=Dec
        month_frac = round((val - year) * 100)
        month = max(1, min(12, int(month_frac)))
        return pd.Timestamp(year=year, month=month, day=1)

    df["date"] = df[0].apply(parse_date)

    # Extract real price (col 7) and real dividend (col 8)
    # Columns: 0=Date, 1=P, 2=D, 3=E, 4=CPI, 5=Fraction, 6=GS10, 7=RealPrice, 8=RealDiv
    df["real_price"] = pd.to_numeric(df[7], errors="coerce")
    df["real_dividend"] = pd.to_numeric(df[8], errors="coerce")

    # Drop rows with missing values in key columns
    df = df.dropna(subset=["real_price", "real_dividend"])

    # Filter to requested date range
    start_ts = pd.Timestamp(start + "-01")
    end_ts = pd.Timestamp(end + "-01")
    df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)].copy()

    # Compute price-dividend ratio
    # Shiller's real dividend is a 12-month moving sum, so P/D = real_price / real_dividend
    df["pd_ratio"] = df["real_price"] / df["real_dividend"]

    # Select and reset index
    result = df[["date", "real_price", "real_dividend", "pd_ratio"]].reset_index(drop=True)

    return result


def load_pd_ratio(config: StrategyConfig) -> np.ndarray:
    """Convenience: return just the P/D ratio as a numpy array (the y_t series)."""
    df = fetch_shiller_data(config)
    return df["pd_ratio"].values
