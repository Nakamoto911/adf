from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StrategyConfig:
    # --- Universe & Data ---
    tickers: list = field(default_factory=list)
    start_date: str = "2000-01-01"
    end_date: str = "2024-12-31"

    # --- Model Hyperparameters ---
    # Add paper-specific hyperparameters here

    # --- Backtest Settings ---
    initial_capital: float = 100_000.0
    rebalance_frequency: str = "monthly"  # e.g., "daily", "weekly", "monthly"

    # --- Feature Engineering Toggles ---
    # Add feature toggles here

    # --- Execution ---
    transaction_cost_bps: float = 10.0  # basis points per trade
