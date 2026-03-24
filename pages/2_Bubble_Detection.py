"""Page 2: Bubble Detection — BSADF plot with CV overlay and bubble shading."""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from src.config import StrategyConfig
from src.data import fetch_shiller_data
from src.features import compute_all_stats
from src.models import simulate_critical_values
from src.backtest import date_stamp_bubbles

st.set_page_config(page_title="Bubble Detection", layout="wide")
st.header("Bubble Detection (PSY Date-Stamping)")

# Sidebar controls
st.sidebar.header("PSY Parameters")
significance = st.sidebar.selectbox(
    "Significance Level", [0.05, 0.10, 0.01], index=0,
    format_func=lambda x: f"{int(x*100)}%"
)
delta = st.sidebar.slider(
    "Min Bubble Duration (delta)", 0.5, 3.0, 1.0, 0.1,
    help="Minimum bubble duration = delta * log(T) observations"
)
mc_reps = st.sidebar.selectbox("MC Replications", [2000, 1000, 500], index=0)

config = StrategyConfig(
    significance_level=significance,
    bubble_duration_delta=delta,
    mc_replications=mc_reps,
)


@st.cache_data(show_spinner="Fetching data...")
def load_data():
    return fetch_shiller_data(StrategyConfig())


@st.cache_data(show_spinner="Computing BSADF sequence...")
def compute_stats(pd_ratio):
    cfg = StrategyConfig()
    return compute_all_stats(pd_ratio, cfg)


@st.cache_data(show_spinner="Loading critical values...")
def load_cvs(mc_reps):
    cfg = StrategyConfig(mc_replications=mc_reps)
    return simulate_critical_values(cfg, verbose=False)


df = load_data()
y = df["pd_ratio"].values
dates = df["date"].values
T = len(y)

stats = compute_stats(y)
cv = load_cvs(mc_reps)

bsadf = stats["bsadf_sequence"]
quantile = 1.0 - significance
cv_seq = cv["bsadf_cv"][quantile]

episodes = date_stamp_bubbles(bsadf, cv_seq, dates, config)

# Summary metrics
col1, col2, col3 = st.columns(3)
col1.metric("SADF", f"{stats['sadf']:.2f}", help="Paper: 3.30")
col2.metric("GSADF", f"{stats['gsadf']:.2f}", help="Paper: 4.21")
col3.metric("Bubble Episodes", len(episodes))

# BSADF vs CV plot
st.subheader("BSADF Sequence vs Critical Value")
fig, ax = plt.subplots(figsize=(14, 5))

dates_pd = pd.to_datetime(dates)
valid = ~np.isnan(bsadf) & ~np.isnan(cv_seq)

ax.plot(dates_pd[valid], bsadf[valid], linewidth=0.7, color="steelblue", label="BSADF")
ax.plot(dates_pd[valid], cv_seq[valid], linewidth=0.7, color="red", linestyle="--",
        label=f"{int(quantile*100)}% CV", alpha=0.8)

# Shade bubble episodes
for ep in episodes:
    start = pd.Timestamp(dates[ep.start_idx])
    end = pd.Timestamp(dates[ep.end_idx])
    ax.axvspan(start, end, alpha=0.15, color="salmon")

ax.set_ylabel("Test Statistic")
ax.set_xlabel("Date")
ax.legend(loc="upper left")
ax.xaxis.set_major_locator(mdates.YearLocator(20))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.grid(alpha=0.3)
fig.tight_layout()
st.pyplot(fig)

# P/D ratio with bubble shading
st.subheader("P/D Ratio with Bubble Episodes")
fig2, ax2 = plt.subplots(figsize=(14, 5))

ax2.plot(dates_pd, y, linewidth=0.7, color="steelblue")
for ep in episodes:
    start = pd.Timestamp(dates[ep.start_idx])
    end = pd.Timestamp(dates[ep.end_idx])
    ax2.axvspan(start, end, alpha=0.15, color="salmon")

ax2.set_ylabel("P/D Ratio")
ax2.set_xlabel("Date")
ax2.xaxis.set_major_locator(mdates.YearLocator(20))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax2.grid(alpha=0.3)
fig2.tight_layout()
st.pyplot(fig2)

# Episode table
st.subheader("Detected Episodes")
episode_data = []
for i, ep in enumerate(episodes, 1):
    episode_data.append({
        "#": i,
        "Start": pd.Timestamp(ep.start_date).strftime("%Y-%m"),
        "End": pd.Timestamp(ep.end_date).strftime("%Y-%m"),
        "Duration (months)": ep.duration,
        "Peak BSADF": f"{ep.peak_bsadf:.2f}",
    })
st.dataframe(pd.DataFrame(episode_data), use_container_width=True, hide_index=True)

# Critical value comparison
with st.expander("Critical Values vs Paper (Table 8)"):
    cv_data = {
        "": ["SADF (ours)", "SADF (paper)", "GSADF (ours)", "GSADF (paper)"],
        "90%": [
            f"{cv['sadf_cv'][0.90]:.2f}", "1.30",
            f"{cv['gsadf_cv'][0.90]:.2f}", "2.17",
        ],
        "95%": [
            f"{cv['sadf_cv'][0.95]:.2f}", "1.59",
            f"{cv['gsadf_cv'][0.95]:.2f}", "2.34",
        ],
        "99%": [
            f"{cv['sadf_cv'][0.99]:.2f}", "2.14",
            f"{cv['gsadf_cv'][0.99]:.2f}", "2.74",
        ],
    }
    st.table(pd.DataFrame(cv_data))
