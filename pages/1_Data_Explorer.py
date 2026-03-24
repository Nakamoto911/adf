"""Page 1: Data Explorer — Shiller P/D ratio time series."""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from src.config import StrategyConfig
from src.data import fetch_shiller_data

st.set_page_config(page_title="Data Explorer", layout="wide")
st.header("Data Explorer")

# Sidebar controls
st.sidebar.header("Data Settings")
start_date = st.sidebar.text_input("Start Date (YYYY-MM)", "1871-01")
end_date = st.sidebar.text_input("End Date (YYYY-MM)", "2010-12")

config = StrategyConfig(start_date=start_date, end_date=end_date)


@st.cache_data(show_spinner="Fetching Shiller data...")
def load_data(start, end):
    cfg = StrategyConfig(start_date=start, end_date=end)
    return fetch_shiller_data(cfg)


df = load_data(start_date, end_date)

# Summary metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Observations (T)", len(df))
col2.metric("Date Range", f"{df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}")
col3.metric("P/D Mean", f"{df['pd_ratio'].mean():.2f}")
col4.metric("r0 (min window frac)", f"{config.compute_r0(len(df)):.4f}")

# P/D ratio plot
st.subheader("S&P 500 Real Price-Dividend Ratio")
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df["date"], df["pd_ratio"], linewidth=0.8, color="steelblue")
ax.set_ylabel("P/D Ratio")
ax.set_xlabel("Date")
ax.xaxis.set_major_locator(mdates.YearLocator(20))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.grid(alpha=0.3)
fig.tight_layout()
st.pyplot(fig)

# Real price and dividend
st.subheader("Real Price & Real Dividend")
fig2, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

ax1.plot(df["date"], df["real_price"], linewidth=0.8, color="darkgreen")
ax1.set_ylabel("Real Price")
ax1.grid(alpha=0.3)

ax2.plot(df["date"], df["real_dividend"], linewidth=0.8, color="darkorange")
ax2.set_ylabel("Real Dividend")
ax2.set_xlabel("Date")
ax2.xaxis.set_major_locator(mdates.YearLocator(20))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax2.grid(alpha=0.3)

fig2.tight_layout()
st.pyplot(fig2)

# Raw data table
with st.expander("Raw Data"):
    st.dataframe(df, use_container_width=True)
