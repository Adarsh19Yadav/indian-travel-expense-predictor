"""Page 3 — Model Performance & Feature Importances."""

import httpx
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

API = "http://localhost:8000"

st.set_page_config(page_title="Model Info", page_icon="🤖", layout="wide")
st.title("🤖 Model Performance & Insights")
st.markdown(
    "Overview of the machine-learning model that powers predictions, including "
    "metrics, feature importances, and a comparison across all evaluated models."
)


def fetch(path: str, method: str = "get", json=None):
    try:
        fn = httpx.get if method == "get" else httpx.post
        r  = fn(f"{API}{path}", json=json, timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        st.error("Backend not running. Start it with: `uvicorn backend.main:app --reload --port 8000`")
        st.stop()
    except Exception as e:
        st.error(f"API error: {e}")
        st.stop()


# ── Load data ──────────────────────────────────────────────────────────────────
metrics = fetch("/model/metrics")
fi_data = fetch("/model/feature-importances")

# ── Best model KPIs ────────────────────────────────────────────────────────────
st.subheader(f"Best Model: {metrics['best_model']}")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Test R²",  f"{metrics['test_r2']:.4f}")
k2.metric("MAE",      f"₹{metrics['test_mae']:,.0f}")
k3.metric("RMSE",     f"₹{metrics['test_rmse']:,.0f}")
k4.metric("MAPE",     f"{metrics['test_mape']:.2f}%")

st.markdown("---")

# ── Tab layout ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📊 Model Comparison",
    "🔍 Feature Importances",
    "ℹ️ Model Details",
])

# ── Tab 1: Model comparison ────────────────────────────────────────────────────
with tab1:
    all_res = metrics["all_results"]
    comp_df = pd.DataFrame([
        {
            "Model":       name,
            "CV R²":       round(v["cv_r2_mean"], 4),
            "CV Std":      round(v["cv_r2_std"],  4),
            "Test R²":     round(v["test_r2"],    4),
            "MAE (INR)":   round(v["mae"],        0),
            "RMSE (INR)":  round(v["rmse"],       0),
            "MAPE (%)":    round(v["mape"],       2),
        }
        for name, v in all_res.items()
    ])

    # Grouped bar: R² comparison
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="CV R²",
        x=comp_df["Model"],
        y=comp_df["CV R²"],
        marker_color="#93c5fd",
        text=comp_df["CV R²"],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Test R²",
        x=comp_df["Model"],
        y=comp_df["Test R²"],
        marker_color="#3b82d4",
        text=comp_df["Test R²"],
        textposition="outside",
    ))
    fig.update_layout(
        barmode="group",
        title="CV R² vs Test R² — All Models",
        yaxis=dict(title="R² Score", range=[0.75, 1.0]),
        height=400,
        legend_title="Metric",
    )
    st.plotly_chart(fig, use_container_width=True)

    # MAE & RMSE comparison
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name="MAE",
        x=comp_df["Model"],
        y=comp_df["MAE (INR)"],
        marker_color="#7c5cd8",
        text=comp_df["MAE (INR)"].map("{:,.0f}".format),
        textposition="outside",
    ))
    fig2.add_trace(go.Bar(
        name="RMSE",
        x=comp_df["Model"],
        y=comp_df["RMSE (INR)"],
        marker_color="#c4b5fd",
        text=comp_df["RMSE (INR)"].map("{:,.0f}".format),
        textposition="outside",
    ))
    fig2.update_layout(
        barmode="group",
        title="MAE vs RMSE (INR) — All Models",
        yaxis_title="Error (INR)",
        height=400,
        legend_title="Metric",
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**Full Metrics Table**")
    st.dataframe(comp_df, use_container_width=True, hide_index=True)


# ── Tab 2: Feature importances ────────────────────────────────────────────────
with tab2:
    fi_df = pd.DataFrame(fi_data).head(20)

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.bar(
            fi_df.sort_values("importance"),
            x="importance",
            y="feature",
            orientation="h",
            title=f"Top {len(fi_df)} Feature Importances — {metrics['best_model']}",
            labels={"importance": "Importance Score", "feature": "Feature"},
            color="importance",
            color_continuous_scale="Blues",
        )
        fig.update_layout(height=600, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Top 10 Features**")
        top10 = fi_df.head(10).copy()
        top10["importance"] = top10["importance"].map("{:.4f}".format)
        st.dataframe(top10, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("**Key Insights**")
        st.info(
            "- **travelers** is the #1 driver (~39% importance)\n"
            "- **accommodation_type** is #2 (~25%)\n"
            "- **trip_days** is #3 (~16%)\n"
            "- Taking a **Flight** adds a significant premium\n"
            "- **Peak season** meaningfully increases costs"
        )

    # Treemap of feature groups
    fi_df2 = fi_df.copy()
    fi_df2["group"] = fi_df2["feature"].apply(
        lambda f: "Numerical" if f in ["travelers","trip_days","activities_count","booking_advance_days","distance_km"]
                  else ("Ordinal" if f in ["accommodation_type","travel_season","meal_plan"]
                        else "Categorical (OHE)")
    )
    fig2 = px.treemap(
        fi_df2,
        path=["group", "feature"],
        values="importance",
        title="Feature Importance by Group",
        color="importance",
        color_continuous_scale="Blues",
    )
    fig2.update_layout(height=500)
    st.plotly_chart(fig2, use_container_width=True)


# ── Tab 3: Model details ──────────────────────────────────────────────────────
with tab3:
    st.subheader("Pipeline Architecture")
    st.markdown("""
    ```
    ColumnTransformer (Preprocessor)
    ├── StandardScaler           → travelers, trip_days, activities_count,
    │                               booking_advance_days, distance_km
    ├── OrdinalEncoder           → accommodation_type (Budget→5-Star),
    │                               travel_season (Off-Peak→Peak),
    │                               meal_plan (Room Only→Full Board)
    └── OneHotEncoder            → destination (57 values),
                                    destination_type (8 values),
                                    transport_mode (4 values)

    GradientBoostingRegressor
    ├── n_estimators : 400
    ├── learning_rate: 0.05
    ├── max_depth    : 5
    ├── subsample    : 0.8
    └── min_samples_leaf: 3
    ```
    """)

    st.subheader("Training Configuration")
    cfg_col1, cfg_col2 = st.columns(2)
    with cfg_col1:
        st.markdown("""
        | Parameter | Value |
        |-----------|-------|
        | Dataset size | 5,200 rows |
        | Train / Test split | 80% / 20% |
        | Cross-validation | 5-fold KFold |
        | Random state | 42 |
        """)
    with cfg_col2:
        st.markdown("""
        | Metric | Score |
        |--------|-------|
        | CV R² (mean) | 0.9608 |
        | CV R² (std)  | 0.0023 |
        | Test R²      | 0.9622 |
        | MAE          | ₹11,177 |
        | RMSE         | ₹16,023 |
        | MAPE         | 11.21%  |
        """)

    st.subheader("All Models Evaluated")
    st.markdown("""
    | Model | Notes |
    |-------|-------|
    | Ridge Regression | Baseline linear model |
    | Random Forest | Ensemble of 300 trees |
    | **Gradient Boosting** ✅ | **Best model — selected** |
    | XGBoost | Very close to GB; slightly lower R² |
    """)
