# ✈️ Indian Travel Expense Predictor

A full-stack machine-learning application that predicts travel expenses for trips across India. Built with a **FastAPI** backend serving a trained **Gradient Boosting** model and a **Streamlit** frontend with interactive Plotly visualisations.

---

## 📸 Application Pages

| Page | Description |
|------|-------------|
| **Home** | Dashboard overview with dataset KPIs |
| **🔮 Predict** | Input form → real-time expense prediction with confidence range |
| **📊 Analytics** | EDA charts: by destination, season, transport, accommodation |
| **🤖 Model Info** | Model comparison table, feature importances, pipeline details |

---

## 🗂️ Project Structure

```
Travel Expense Project/
├── backend/
│   ├── __init__.py
│   ├── main.py              ← FastAPI application & API routes
│   ├── schemas.py           ← Pydantic request/response models
│   └── data_service.py      ← Pandas analytics over the CSV dataset
├── frontend/
│   ├── app.py               ← Streamlit home page (entry point)
│   └── pages/
│       ├── 1_Predict.py     ← Trip input form + prediction result
│       ├── 2_Analytics.py   ← Dataset EDA & trend charts
│       └── 3_Model_Info.py  ← Model metrics & feature importances
├── model/
│   ├── best_model.pkl       ← Serialised sklearn Pipeline (trained)
│   ├── metadata.json        ← Model metrics for all evaluated models
│   ├── feature_importances.png
│   ├── actual_vs_predicted.png
│   └── model_comparison.png
├── dataset_indian_travel_expense.csv  ← 5,200-row training dataset
├── train_model.py           ← Full ML training pipeline script
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the model (already done — skip if `model/best_model.pkl` exists)

```bash
python train_model.py
```

### 3. Start the FastAPI backend

```bash
uvicorn backend.main:app --reload --port 8000
```

The API will be live at **http://localhost:8000**  
Interactive API docs: **http://localhost:8000/docs**

### 4. Start the Streamlit frontend (new terminal)

```bash
streamlit run frontend/app.py
```

The app will open at **http://localhost:8501**

---

## 🛠️ Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend UI | Streamlit | 1.35 |
| Charts | Plotly | 5.22 |
| Backend API | FastAPI | 0.111 |
| API Server | Uvicorn | 0.29 |
| Data Validation | Pydantic v2 | 2.7 |
| HTTP Client | httpx | 0.27 |
| ML Model | scikit-learn (GradientBoosting) | 1.4 |
| Data Processing | Pandas / NumPy | 2.2 / 1.26 |

---

## 🔌 API Reference

Base URL: `http://localhost:8000`

### Prediction

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict` | Predict trip expense from inputs |
| `POST` | `/analytics/comparable-trips` | Find similar trips in the dataset |

**POST `/predict` — Request body:**
```json
{
  "destination": "Goa",
  "destination_type": "Beach",
  "travelers": 2,
  "trip_days": 5,
  "transport_mode": "Flight",
  "accommodation_type": "3-Star",
  "meal_plan": "Breakfast",
  "activities_count": 3,
  "travel_season": "Peak",
  "booking_advance_days": 30,
  "distance_km": 1400
}
```

**Response:**
```json
{
  "predicted_expense": 75447.98,
  "lower_bound": 66991.77,
  "upper_bound": 83904.19,
  "model_name": "Gradient Boosting",
  "mape_pct": 11.208
}
```

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/analytics/summary` | Dataset-level KPIs |
| `GET` | `/analytics/by-destination` | Avg expense per destination |
| `GET` | `/analytics/by-season` | Avg expense per travel season |
| `GET` | `/analytics/by-transport` | Avg expense by transport mode |
| `GET` | `/analytics/by-accommodation` | Avg expense by accommodation tier |
| `GET` | `/analytics/by-travelers` | Avg expense by group size |
| `GET` | `/analytics/by-trip-days` | Avg expense by trip duration |
| `GET` | `/analytics/expense-distribution` | Histogram bucket data |

### Model

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/model/metrics` | All model evaluation metrics |
| `GET` | `/model/feature-importances` | Ranked feature importance list |

---

## 📊 Dataset

| Property | Value |
|----------|-------|
| File | `dataset_indian_travel_expense.csv` |
| Rows | 5,200 |
| Target | `actual_trip_expense` (INR) |
| Features | 11 |
| Destinations | 57 Indian cities |

### Feature Descriptions

| Feature | Type | Description |
|---------|------|-------------|
| `destination` | Nominal | Indian city name (57 unique values) |
| `destination_type` | Nominal | Heritage, Religious, Mountain, City, Nature, Beach, Wildlife, Adventure |
| `travelers` | Numerical | Number of people on the trip (1–20) |
| `trip_days` | Numerical | Duration of the trip in days (1–30) |
| `transport_mode` | Nominal | Train, Car, Flight, Bus |
| `accommodation_type` | Ordinal | Budget → 2-Star → 3-Star → 4-Star → 5-Star |
| `meal_plan` | Ordinal | Room Only → Breakfast → Half Board → Full Board |
| `activities_count` | Numerical | Number of planned activities (0–20) |
| `travel_season` | Ordinal | Off-Peak → Shoulder → Peak |
| `booking_advance_days` | Numerical | Days booked in advance (0–365) |
| `distance_km` | Numerical | Distance from origin in km (1–5000) |

---

## 🤖 Model Performance

Four regression models were trained and evaluated with 5-fold cross-validation:

| Model | CV R² | Test R² | MAE (INR) | RMSE (INR) | MAPE |
|-------|--------|---------|-----------|------------|------|
| Ridge Regression | 0.8357 | 0.8276 | 26,493 | 34,217 | 39.79% |
| Random Forest | 0.9315 | 0.9347 | 14,437 | 21,054 | 15.37% |
| **Gradient Boosting** ✅ | **0.9608** | **0.9622** | **11,177** | **16,023** | **11.21%** |
| XGBoost | 0.9605 | 0.9606 | 11,154 | 16,365 | 11.27% |

**Winner: Gradient Boosting** — highest Test R² (0.9622) and lowest MAPE (11.21%).

### Top Feature Importances

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | travelers | 39.47% |
| 2 | accommodation_type | 24.79% |
| 3 | trip_days | 16.01% |
| 4 | transport_mode (Flight) | 6.75% |
| 5 | distance_km | 3.77% |
| 6 | travel_season | 3.64% |
| 7 | meal_plan | 2.29% |
| 8 | activities_count | 1.90% |

---

## 🔮 Using the Trained Model Programmatically

```python
import pickle
import pandas as pd

# Load model
with open("model/best_model.pkl", "rb") as f:
    model = pickle.load(f)

# Predict
sample = pd.DataFrame([{
    "destination":          "Manali",
    "destination_type":     "Mountain",
    "travelers":            4,
    "trip_days":            7,
    "transport_mode":       "Train",
    "accommodation_type":   "3-Star",
    "meal_plan":            "Full Board",
    "activities_count":     5,
    "travel_season":        "Peak",
    "booking_advance_days": 60,
    "distance_km":          600,
}])

prediction = model.predict(sample)[0]
print(f"Estimated expense: INR {prediction:,.2f}")
```

---

## 📁 Categorical Value Reference

| Feature | Allowed Values |
|---------|---------------|
| `destination_type` | Heritage, Religious, Mountain, City, Nature, Beach, Wildlife, Adventure |
| `transport_mode` | Train, Car, Flight, Bus |
| `accommodation_type` | Budget, 2-Star, 3-Star, 4-Star, 5-Star |
| `meal_plan` | Room Only, Breakfast, Half Board, Full Board |
| `travel_season` | Off-Peak, Shoulder, Peak |

---

## 📄 License

This project is for educational and demonstration purposes.
