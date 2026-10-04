"""Streamlit entry point — Travel Expense Predictor."""

import streamlit as st

st.set_page_config(
    page_title="Indian Travel Expense Predictor",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar branding ──────────────────────────────────────────────────────────
st.sidebar.title("✈️ Travel Expense Predictor")
st.sidebar.markdown(
    "Predict your Indian trip costs using a machine-learning model "
    "trained on **5,200 real travel records**."
)
st.sidebar.markdown("---")
st.sidebar.caption("Model: Gradient Boosting  |  R² = 0.9622")

# ── Home page ─────────────────────────────────────────────────────────────────
st.title("🇮🇳 Indian Travel Expense Predictor")
st.markdown(
    """
    Welcome! Use the sidebar to navigate between pages.

    | Page | What you can do |
    |------|----------------|
    | **Predict** | Enter your trip details and get an instant expense prediction |
    | **Analytics** | Explore trends across destinations, seasons, and transport modes |
    | **Model Info** | Review model performance metrics and feature importances |

    ---
    """
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records", "5,200")
col2.metric("Destinations", "57")
col3.metric("Model R²", "0.9622")
col4.metric("Mean Abs Error", "₹11,177")

st.markdown("---")
st.info("👈 Select a page from the sidebar to get started.")
