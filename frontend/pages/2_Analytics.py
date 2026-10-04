"""Page 2 — Dataset Analytics & EDA."""

import httpx
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

API = "http://localhost:8000"

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
st.title("📊 Travel Expense Analytics")
st.markdown("Explore patterns and trends across the **5,200-record** Indian travel expense dataset.")


def fetch(path: str):
    try:
        r = httpx.get(f"{API}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        st.error("Backend not running. Start it with: `uvicorn backend.main:app --reload --port 8000`")
        st.stop()
    except Exception as e:
        st.error(f"API error: {e}")
        st.stop()


# ── Summary KPIs ──────────────────────────────────────────────────────────────
summary = fetch("/analytics/summary")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Records",     f"{summary['total_records']:,}")
k2.metric("Avg Expense",       f"₹{summary['avg_expense']:,.0f}")
k3.metric("Median Expense",    f"₹{summary['median_expense']:,.0f}")
k4.metric("Min Expense",       f"₹{summary['min_expense']:,.0f}")
k5.metric("Max Expense",       f"₹{summary['max_expense']:,.0f}")

st.markdown("---")

# ── Tab layout ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ By Destination",
    "🌦️ By Season",
    "🚗 By Transport",
    "🏨 By Accommodation",
    "📈 Distributions",
])

# ── Tab 1: Destination ────────────────────────────────────────────────────────
with tab1:
    dest_data = fetch("/analytics/by-destination")
    dest_df   = pd.DataFrame(dest_data)

    st.subheader("Average Expense by Destination (Top 20)")
    top20 = dest_df.head(20).sort_values("avg_expense")
    fig = px.bar(
        top20,
        x="avg_expense",
        y="destination",
        color="destination_type",
        orientation="h",
        text=top20["avg_expense"].map("₹{:,.0f}".format),
        title="Top 20 Destinations by Average Expense",
        labels={"avg_expense": "Avg Expense (INR)", "destination": "Destination"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(height=550, legend_title="Destination Type")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Average Expense by Destination Type")
    type_df = (
        dest_df.groupby("destination_type", as_index=False)
        .agg(avg_expense=("avg_expense", "mean"), trips=("trip_count", "sum"))
        .sort_values("avg_expense", ascending=False)
    )
    fig2 = px.pie(
        type_df,
        values="avg_expense",
        names="destination_type",
        title="Share of Average Expense by Destination Type",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig2.update_traces(textinfo="label+percent")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Full Destination Table**")
    dest_df["avg_expense"] = dest_df["avg_expense"].map("₹{:,.0f}".format)
    st.dataframe(dest_df, use_container_width=True, hide_index=True)


# ── Tab 2: Season ─────────────────────────────────────────────────────────────
with tab2:
    season_data = fetch("/analytics/by-season")
    season_df   = pd.DataFrame(season_data)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            season_df,
            x="season",
            y="avg_expense",
            color="season",
            text=season_df["avg_expense"].map("₹{:,.0f}".format),
            title="Average Expense by Travel Season",
            labels={"avg_expense": "Avg Expense (INR)"},
            color_discrete_map={
                "Off-Peak": "#93c5fd",
                "Shoulder": "#fcd34d",
                "Peak":     "#f87171",
            },
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(
            season_df,
            values="trip_count",
            names="season",
            title="Trip Count Distribution by Season",
            color_discrete_map={
                "Off-Peak": "#93c5fd",
                "Shoulder": "#fcd34d",
                "Peak":     "#f87171",
            },
        )
        fig2.update_traces(textinfo="label+value+percent")
        st.plotly_chart(fig2, use_container_width=True)


# ── Tab 3: Transport ──────────────────────────────────────────────────────────
with tab3:
    trans_data = fetch("/analytics/by-transport")
    trans_df   = pd.DataFrame(trans_data)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            trans_df,
            x="transport_mode",
            y="avg_expense",
            color="transport_mode",
            text=trans_df["avg_expense"].map("₹{:,.0f}".format),
            title="Average Expense by Transport Mode",
            labels={"avg_expense": "Avg Expense (INR)"},
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(
            trans_df,
            values="trip_count",
            names="transport_mode",
            title="Trip Count by Transport Mode",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig2.update_traces(textinfo="label+value+percent")
        st.plotly_chart(fig2, use_container_width=True)


# ── Tab 4: Accommodation ──────────────────────────────────────────────────────
with tab4:
    acc_data = fetch("/analytics/by-accommodation")
    acc_df   = pd.DataFrame(acc_data)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            acc_df,
            x="accommodation_type",
            y="avg_expense",
            color="accommodation_type",
            text=acc_df["avg_expense"].map("₹{:,.0f}".format),
            title="Average Expense by Accommodation Type",
            labels={"avg_expense": "Avg Expense (INR)"},
            color_discrete_sequence=px.colors.sequential.Blues_r[:5],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.funnel(
            acc_df.sort_values("avg_expense", ascending=False),
            x="avg_expense",
            y="accommodation_type",
            title="Expense Funnel — Accommodation Tier",
        )
        st.plotly_chart(fig2, use_container_width=True)


# ── Tab 5: Distributions ──────────────────────────────────────────────────────
with tab5:
    col1, col2 = st.columns(2)

    with col1:
        dist_data = fetch("/analytics/expense-distribution")
        fig = go.Figure(go.Bar(
            x=dist_data["labels"],
            y=dist_data["counts"],
            marker_color="#3b82d4",
            name="Trips",
        ))
        fig.update_layout(
            title="Expense Distribution (Histogram)",
            xaxis_title="Expense Range (INR)",
            yaxis_title="Number of Trips",
            xaxis_tickangle=-45,
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        trav_data = fetch("/analytics/by-travelers")
        trav_df   = pd.DataFrame(trav_data)
        fig2 = px.line(
            trav_df,
            x="travelers",
            y="avg_expense",
            markers=True,
            title="Average Expense by Number of Travelers",
            labels={"avg_expense": "Avg Expense (INR)", "travelers": "Travelers"},
        )
        fig2.update_traces(line_color="#7c5cd8", marker_color="#7c5cd8")
        st.plotly_chart(fig2, use_container_width=True)

    days_data = fetch("/analytics/by-trip-days")
    days_df   = pd.DataFrame(days_data)
    fig3 = px.area(
        days_df,
        x="trip_days",
        y="avg_expense",
        title="Average Expense by Trip Duration",
        labels={"avg_expense": "Avg Expense (INR)", "trip_days": "Trip Days"},
        color_discrete_sequence=["#3b82d4"],
    )
    st.plotly_chart(fig3, use_container_width=True)
