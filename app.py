import streamlit as st

st.set_page_config(
    page_title="PSY (2015) Bubble Detection",
    layout="wide",
    page_icon="📈",
)
st.title("PSY (2015) — Testing for Multiple Bubbles")
st.markdown(
    "Replication of Phillips, Shi & Yu (2015). "
    "Select a page from the sidebar to explore the data, test statistics, "
    "and detected bubble episodes."
)
st.info("Use the sidebar to navigate between pages.")
