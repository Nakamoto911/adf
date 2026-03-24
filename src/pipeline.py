# src/pipeline.py
# Orchestrator: imports from all src/ modules and executes the end-to-end run.

from src.config import StrategyConfig
from src import data, features, models, backtest


def run(config: StrategyConfig):
    """Execute the full pipeline with the given config."""
    # TODO: Implement end-to-end pipeline
    pass
