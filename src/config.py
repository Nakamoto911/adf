from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass
class StrategyConfig:
    # --- Data Source ---
    shiller_url: str = (
        "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
    )
    start_date: str = "1871-01"
    end_date: str = "2010-12"
    frequency: str = "monthly"

    # --- ADF Regression ---
    lag_order: int = 0  # Fixed k=0 per paper

    # --- Test Parameters ---
    significance_level: float = 0.05  # 5% for empirical application
    mc_replications: int = 2000  # Monte Carlo reps for critical values

    # --- Minimum Window Size ---
    # r0 = 0.01 + 1.8 / sqrt(T); for T=1680 -> ~0.054 -> ~90 obs
    r0_constant: float = 0.01
    r0_coeff: float = 1.8

    # --- Minimum Bubble Duration ---
    # delta * log(T) observations; delta is frequency-dependent
    bubble_duration_delta: float = 1.0  # Start with 1.0 for monthly, calibrate if needed

    # --- Backtest Settings ---
    initial_capital: float = 100_000.0
    transaction_cost_bps: float = 10.0

    def compute_r0(self, T: int) -> float:
        """Minimum window fraction: r0 = 0.01 + 1.8/sqrt(T)."""
        return self.r0_constant + self.r0_coeff / math.sqrt(T)

    def compute_min_window(self, T: int) -> int:
        """Minimum window size in observations."""
        return int(math.floor(T * self.compute_r0(T)))

    def compute_min_bubble_duration(self, T: int) -> int:
        """Minimum bubble duration in observations: delta * log(T)."""
        return int(math.floor(self.bubble_duration_delta * math.log(T)))
