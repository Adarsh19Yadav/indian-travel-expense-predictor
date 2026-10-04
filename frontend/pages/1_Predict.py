"""Page 1 — Trip Expense Prediction Form."""

import httpx
import streamlit as st
import plotly.graph_objects as go

API = "http://localhost:8000"

st.set_page_config(page_title="Predict Expense", page_icon="🔮", layout="wide")
st.title("🔮 Predict Your Trip Expense")
st.markdown("Fill in your trip details below and click **Predict** to get an instant estimate.")

# ── Destination options (from dataset) ───────────────────────────────────────
DESTINATIONS = sorted([
    "Agra", "Ahmedabad", "Allahabad", "Amritsar", "Aurangabad",
    "Bhubaneswar", "Chennai", "Coorg", "Darjeeling", "Delhi",
    "Dharamshala", "Goa", "Hampi", "Hyderabad", "Jaipur",
    "Jaisalmer", "Jodhpur", "Kochi", "Kodaikanal", "Kolkata",
    "Leh", "Lonavala", "Lucknow", "Madurai", "Manali",
    "Mount Abu", "Mumbai", "Munnar", "Mysore", "Nainital",
    "Ooty", "Puri", "Pondicherry", "Port Blair", "Pune",
    "Ranthambore", "Rishikesh", "Shimla", "Srinagar", "Udaipur",
    "Varanasi", "Varkala", "Vizag",
])

DEST_TYPES    = ["Heritage", "Religious", "Mountain", "City", "Nature", "Beach", "Wildlife", "Adventure"]
TRANSPORT     = ["Train", "Car", "Flight", "Bus"]
ACCOMMODATION = ["Budget", "2-Star", "3-Star", "4-Star", "5-Star"]
MEAL_PLANS    = ["Room Only", "Breakfast", "Half Board", "Full Board"]
SEASONS       = ["Off-Peak", "Shoulder", "Peak"]

# ── Form ──────────────────────────────────────────────────────────────────────
with st.form("predict_form"):
    st.subheader("Trip Details")

    col1, col2, col3 = st.columns(3)
    with col1:
        destination      = st.selectbox("Destination", DESTINATIONS, index=DESTINATIONS.index("Goa"))
        destination_type = st.selectbox("Destination Type", DEST_TYPES, index=DEST_TYPES.index("Beach"))
        transport_mode   = st.selectbox("Transport Mode", TRANSPORT, index=TRANSPORT.index("Flight"))

    with col2:
        travelers             = st.slider("Number of Travelers", 1, 20, 2)
        trip_days             = st.slider("Trip Duration (days)", 1, 30, 5)
        activities_count      = st.slider("Number of Activities", 0, 20, 3)

    with col3:
        accommodation_type    = st.selectbox("Accommodation", ACCOMMODATION, index=ACCOMMODATION.index("3-Star"))
        meal_plan             = st.selectbox("Meal Plan", MEAL_PLANS, index=MEAL_PLANS.index("Breakfast"))
        travel_season         = st.selectbox("Travel Season", SEASONS, index=SEASONS.index("Peak"))

    st.subheader("Logistics")
    col4, col5 = st.columns(2)
    with col4:
        booking_advance_days = st.slider("Booking Advance (days)", 0, 365, 30)
    with col5:
        distance_km = st.slider("Distance from home (km)", 50, 5000, 1400)

    submitted = st.form_submit_button("🔮 Predict Expense", use_container_width=True)

# ── Prediction ────────────────────────────────────────────────────────────────
if submitted:
    payload = {
        "destination":          destination,
        "destination_type":     destination_type,
        "travelers":            travelers,
        "trip_days":            trip_days,
        "transport_mode":       transport_mode,
        "accommodation_type":   accommodation_type,
        "meal_plan":            meal_plan,
        "activities_count":     activities_count,
        "travel_season":        travel_season,
        "booking_advance_days": booking_advance_days,
        "distance_km":          distance_km,
    }

    with st.spinner("Contacting prediction API..."):
        try:
            resp = httpx.post(f"{API}/predict", json=payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
        except httpx.ConnectError:
            st.error("Cannot connect to the backend API. Make sure it is running on http://localhost:8000")
            st.code("uvicorn backend.main:app --reload --port 8000", language="bash")
            st.stop()
        except Exception as e:
            st.error(f"Prediction failed: {e}")
            st.stop()

    pred  = result["predicted_expense"]
    low   = result["lower_bound"]
    high  = result["upper_bound"]
    model = result["model_name"]
    mape  = result["mape_pct"]

    st.markdown("---")
    st.subheader("Prediction Result")

    r1, r2, r3 = st.columns(3)
    r1.metric("Predicted Expense", f"₹{pred:,.0f}")
    r2.metric("Lower Estimate",    f"₹{low:,.0f}")
    r3.metric("Upper Estimate",    f"₹{high:,.0f}")

    # Gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pred,
        title={"text": f"Predicted Trip Expense (INR)<br><span style='font-size:0.8em;color:gray'>Model: {model} | MAPE: {mape:.1f}%</span>"},
        gauge={
            "axis":  {"range": [0, 300000], "tickformat": ",.0f"},
            "bar":   {"color": "#3b82d4"},
            "steps": [
                {"range": [0, 50000],   "color": "#d1fae5"},
                {"range": [50000, 150000],  "color": "#fef3c7"},
                {"range": [150000, 300000], "color": "#fee2e2"},
            ],
            "threshold": {
                "line":  {"color": "red", "width": 3},
                "value": pred,
            },
        },
        number={"prefix": "₹", "valueformat": ",.0f"},
    ))
    fig.update_layout(height=320, margin=dict(t=60, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Confidence range bar
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=["Low Estimate", "Prediction", "High Estimate"],
        y=[low, pred, high],
        marker_color=["#93c5fd", "#3b82d4", "#93c5fd"],
        text=[f"₹{v:,.0f}" for v in [low, pred, high]],
        textposition="outside",
    ))
    fig2.update_layout(
        title="Expense Range (based on model MAPE)",
        yaxis_title="INR",
        height=350,
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Comparable trips
    st.markdown("---")
    st.subheader("Similar Trips from Dataset")
    with st.spinner("Fetching comparable trips..."):
        try:
            comp = httpx.post(f"{API}/analytics/comparable-trips", json=payload, timeout=10)
            comp.raise_for_status()
            trips = comp.json()
            if trips:
                import pandas as pd
                cdf = pd.DataFrame(trips)
                cdf["actual_trip_expense"] = cdf["actual_trip_expense"].map("₹{:,.0f}".format)
                st.dataframe(cdf, use_container_width=True)
        except Exception:
            st.info("Could not fetch comparable trips.")
