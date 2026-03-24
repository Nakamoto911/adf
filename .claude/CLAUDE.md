# CLAUDE.md

This file provides strict guidance for Claude Code when working in this repository.

## Project Overview
The goal is to replicate the research paper methodology and results.

## Directory Structure
- `src/`: Core modular pipeline (data, features, models, backtest, config).
- `diagnostics/`: Isolated data audits, ML pipeline health scripts, and component tests.
- `reports/`: Destination for all auto-generated markdown reports, CSVs, and PDFs.
- `data_cache/`: Local `.pkl` cache for downloaded financial data.
- `./.claude/`: Project-local LLM rulebook and memory files.
- `pages/`: Streamlit multipage dashboard screens.
- root: Entry points only (`app.py`, `run_experiments.py`, `requirements.txt`).

## Primary Reference: The Refcard
When verifying implementation against the paper, **ALWAYS use `refcard.md` as the primary reference.** It contains all formulas, hyperparameters, feature definitions, and numerical results extracted from the paper. Do not parse the raw PDF unless investigating a gap listed in the "Undisclosed" section of the refcard.

## Architecture Rules

### 1. The Modular Pipeline (`src/`)
Do not build monolithic files. The pipeline must be strictly separated:
- `config.py`: `StrategyConfig` dataclass (hyperparameters, toggles).
- `data.py`: API fetching and caching logic.
- `features.py`: Feature engineering and mathematical transformations.
- `models.py`: Algorithm classes (e.g., ML models, mathematical models) with standard fit/predict APIs.
- `backtest.py`: Walk-forward simulation, portfolio allocation, and metric calculation.
- `pipeline.py`: The orchestrator that imports the above and executes the end-to-end run.

### 2. Diagnostics & Testing (`diagnostics/`)
There is no formal pytest framework. All data quality audits, isolated component tests, and ML health checks live in `diagnostics/`.
**MANDATORY:** When creating a new test or diagnostic script, place it in `diagnostics/` and add an entry with its description to `diagnostics/TESTS.md`.

### 3. Caching Protocol
All data downloads MUST be cached in `data_cache/` using `.pkl` files.
- Implement staleness checks (e.g., if end date is >7 days behind requested date, re-fetch).
- Clean up old cache files for a ticker when saving a new one.

### 4. Dashboard Deployment Rule
When any algorithm improvement is made, it MUST be deployed to the UI and Experiment Runner.
1. Add to `src/config.py`.
2. Implement in the relevant `src/` module.
3. Add sidebar controls in the Streamlit `pages/`.
4. Add a new experiment preset in `run_experiments.py`.

## Session Memory & Experiment Tracking (CRITICAL)

You have a **project-local** auto-memory directory (`./.claude/`) that persists across conversations for this specific repository. Do NOT confuse this with your global `~/.claude/` directory.
**MANDATORY PROTOCOL:**
1. **At Session Start:** Read `./.claude/MEMORY.md` and `./.claude/experiments.md` to understand prior context.
2. **After Running Experiments:** Log parameters, results, and conclusions in `./.claude/experiments.md`.
3. **After Code Changes:** Record what changed and why in `./.claude/experiments.md`.
4. **State Management:** Keep `./.claude/MEMORY.md` updated with the *current* best performance numbers, known gaps vs. the paper, and core architectural decisions. Keep `MEMORY.md` < 200 lines.
