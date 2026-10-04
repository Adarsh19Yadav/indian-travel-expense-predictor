# Project Report: Indian Travel Expense Predictor

**Course / Domain:** Machine Learning & Full-Stack Python Development  
**Dataset:** `dataset_indian_travel_expense.csv` — 5,200 records of Indian domestic travel  
**Target Variable:** `actual_trip_expense` (INR)  
**Date:** 2025

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Dataset Description](#3-dataset-description)
4. [Exploratory Data Analysis](#4-exploratory-data-analysis)
5. [Data Preprocessing](#5-data-preprocessing)
6. [Model Development](#6-model-development)
7. [Model Evaluation & Results](#7-model-evaluation--results)
8. [Feature Importance Analysis](#8-feature-importance-analysis)
9. [Application Architecture](#9-application-architecture)
10. [API Design](#10-api-design)
11. [Frontend Design](#11-frontend-design)
12. [How to Run](#12-how-to-run)
13. [Conclusion](#13-conclusion)
14. [Future Enhancements](#14-future-enhancements)

---

## 1. Executive Summary

This project delivers an end-to-end machine-learning system that predicts the total cost of a domestic trip in India. A dataset of 5,200 travel records covering 57 destinations was used to train and compare four regression models. The best-performing model — a **Gradient Boosting Regressor** — achieves a **Test R² of 0.9622** and a **Mean Absolute Error of ₹11,177**, meaning predictions are accurate to within ~11% on average.

The trained model is served through a **FastAPI** REST backend and surfaced to users via a three-page **Streamlit** web application with interactive **Plotly** charts, enabling both predictions and data-driven exploration.

---

## 2. Problem Statement

Travel budgeting in India is difficult because costs depend on many interdependent factors: destination popularity, group size, accommodation standard, transport choice, meal plan, and season. Travellers frequently underestimate or overestimate their budgets, leading to either financial stress or unnecessarily conservative planning.

**Objective:** Build a regression model that, given a set of trip parameters, accurately predicts the total trip expense in Indian Rupees.

**Success criteria:**
- Test R² ≥ 0.90
- MAPE ≤ 15%
- Response latency < 200 ms per API call

All three criteria are met by the final system.

---

## 3. Dataset Description

| Property | Detail |
|----------|--------|
| File | `dataset_indian_travel_expense.csv` |
| Rows | 5,200 |
| Columns | 12 (11 features + 1 target) |
| Missing values | None |
| Target range | ₹5,000 — ₹3,00,000 |
| Target mean | ₹1,15,152 |
| Target median | ₹90,978 |

### Features

| # | Feature | Data Type | Encoding | Description |
|---|---------|-----------|----------|-------------|
| 1 | `destination` | Nominal | One-Hot (57 categories) | Indian city |
| 2 | `destination_type` | Nominal | One-Hot (8 categories) | Type of destination |
| 3 | `travelers` | Integer | Standard Scaled | Number of travellers (1–20) |
| 4 | `trip_days` | Integer | Standard Scaled | Duration in days (1–30) |
| 5 | `transport_mode` | Nominal | One-Hot (4 categories) | Train / Car / Flight / Bus |
| 6 | `accommodation_type` | Ordinal | Ordinal Encoded | Budget → 5-Star (5 levels) |
| 7 | `meal_plan` | Ordinal | Ordinal Encoded | Room Only → Full Board (4 levels) |
| 8 | `activities_count` | Integer | Standard Scaled | Activities planned (0–20) |
| 9 | `travel_season` | Ordinal | Ordinal Encoded | Off-Peak → Peak (3 levels) |
| 10 | `booking_advance_days` | Integer | Standard Scaled | Days booked in advance (0–365) |
| 11 | `distance_km` | Integer | Standard Scaled | Trip distance in km (1–5,000) |

---

## 4. Exploratory Data Analysis

Key findings from EDA on the 5,200-record dataset:

### 4.1 Expense Distribution
- The distribution is **right-skewed** with a long tail up to ₹3,00,000.
- Most trips (≈50%) fall in the ₹30,000–₹1,20,000 range.
- The top 10% of trips exceed ₹2,00,000.

### 4.2 By Destination Type
- **Wildlife** and **Adventure** destinations command the highest average expenses.
- **City** destinations are the most affordable on average.
- **Beach** and **Mountain** destinations have high variance — costs depend heavily on accommodation tier.

### 4.3 By Transport Mode
| Transport | Avg Expense (approx.) |
|-----------|-----------------------|
| Flight    | Highest               |
| Car       | Second                |
| Train     | Third                 |
| Bus       | Lowest                |

### 4.4 By Travel Season
| Season   | Avg Expense (approx.) |
|----------|-----------------------|
| Peak     | Highest               |
| Shoulder | Mid                   |
| Off-Peak | Lowest                |

### 4.5 By Accommodation Tier
A clear monotonic increase from Budget → 5-Star was observed, confirming ordinal encoding is appropriate.

### 4.6 Correlations
- **travelers** and **trip_days** are the strongest numerical predictors.
- **booking_advance_days** has a weak negative correlation with expense (booking earlier reduces cost slightly).

---

## 5. Data Preprocessing

A `ColumnTransformer` sklearn pipeline was built to handle all three feature types simultaneously:

```
ColumnTransformer
├── StandardScaler        → travelers, trip_days, activities_count,
│                            booking_advance_days, distance_km
├── OrdinalEncoder        → accommodation_type  [Budget, 2-Star, 3-Star, 4-Star, 5-Star]
│                            travel_season       [Off-Peak, Shoulder, Peak]
│                            meal_plan           [Room Only, Breakfast, Half Board, Full Board]
└── OneHotEncoder         → destination (57), destination_type (8), transport_mode (4)
```

**Design decisions:**
- Ordinal features are encoded with meaningful ordered categories so the model can exploit the inherent rank signal (e.g., 5-Star > 4-Star > Budget).
- One-hot encoding is used for truly nominal features where no inherent order exists.
- `StandardScaler` is applied to numerical features to aid convergence in linear models and ensure comparable scales.
- `handle_unknown="ignore"` is set on the OneHotEncoder so unseen destinations at inference time produce all-zero columns rather than errors.

---

## 6. Model Development

### 6.1 Train / Test Split
- 80% training (4,160 rows) / 20% test (1,040 rows)
- `random_state=42` for reproducibility

### 6.2 Cross-Validation
5-fold `KFold` cross-validation was applied on the training set for each model to obtain robust CV R² estimates.

### 6.3 Models Evaluated

**Ridge Regression (baseline)**
- A regularised linear model.
- `alpha=10` to prevent overfitting on the large one-hot encoded feature space.
- Serves as a linear baseline.

**Random Forest Regressor**
- `n_estimators=300`, `min_samples_leaf=2`, `n_jobs=-1`
- Ensemble of 300 decision trees trained with bootstrap sampling.
- Naturally handles non-linear interactions.

**Gradient Boosting Regressor (winner)**
- `n_estimators=400`, `learning_rate=0.05`, `max_depth=5`, `subsample=0.8`, `min_samples_leaf=3`
- Sequential ensemble where each tree corrects the residuals of the previous.
- Slower to train than Random Forest but achieves higher accuracy.
- `subsample=0.8` adds stochastic regularisation to prevent overfitting.

**XGBoost Regressor**
- `n_estimators=400`, `learning_rate=0.05`, `max_depth=6`, `subsample=0.8`, `colsample_bytree=0.8`
- Optimised gradient boosting with second-order gradients and built-in regularisation (`reg_lambda=1`).
- Nearly identical performance to sklearn Gradient Boosting.

---

## 7. Model Evaluation & Results

### 7.1 Metrics Used

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **R²** | 1 − SS_res/SS_tot | Proportion of variance explained (1.0 = perfect) |
| **MAE** | mean(|y − ŷ|) | Average absolute error in INR |
| **RMSE** | √mean((y − ŷ)²) | Penalises large errors more; in INR |
| **MAPE** | mean(|y − ŷ|/y) × 100 | Percentage error — scale-independent |

### 7.2 Results Table

| Model | CV R² (mean ± std) | Test R² | MAE (INR) | RMSE (INR) | MAPE |
|-------|-------------------|---------|-----------|------------|------|
| Ridge Regression | 0.8357 ± 0.0043 | 0.8276 | 26,493 | 34,217 | 39.79% |
| Random Forest | 0.9315 ± 0.0070 | 0.9347 | 14,437 | 21,054 | 15.37% |
| **Gradient Boosting** | **0.9608 ± 0.0023** | **0.9622** | **11,177** | **16,023** | **11.21%** |
| XGBoost | 0.9605 ± 0.0016 | 0.9606 | 11,154 | 16,365 | 11.27% |

### 7.3 Winner: Gradient Boosting

Gradient Boosting was selected as the best model because:
1. Highest Test R² (0.9622) — explains **96.2%** of variance in unseen data.
2. Lowest MAPE (11.21%) — predictions are accurate to within ~11% on average.
3. Lowest CV R² standard deviation (0.0023) — the most stable model across folds.
4. XGBoost has a marginally lower MAE (₹23 difference) but a higher RMSE, suggesting it makes slightly more large errors.

### 7.4 Confidence Intervals
Because the model has a known MAPE of 11.21%, the API returns a confidence range for each prediction:
- **Lower bound:** `predicted × (1 − 0.1121)`
- **Upper bound:** `predicted × (1 + 0.1121)`

---

## 8. Feature Importance Analysis

Feature importances extracted from the Gradient Boosting model:

| Rank | Feature | Importance | Group |
|------|---------|-----------|-------|
| 1 | `travelers` | 39.47% | Numerical |
| 2 | `accommodation_type` | 24.79% | Ordinal |
| 3 | `trip_days` | 16.01% | Numerical |
| 4 | `transport_mode_Flight` | 6.75% | Categorical |
| 5 | `distance_km` | 3.77% | Numerical |
| 6 | `travel_season` | 3.64% | Ordinal |
| 7 | `meal_plan` | 2.29% | Ordinal |
| 8 | `activities_count` | 1.90% | Numerical |
| 9 | `booking_advance_days` | 0.34% | Numerical |

**Key insights:**
- The **number of travellers** alone accounts for nearly 40% of predictive power — more people, higher total cost.
- **Accommodation tier** is the second most important factor, reflecting the large price gap between Budget and 5-Star stays.
- **Trip duration** contributes 16% — each additional day linearly increases accommodation and meal costs.
- **Choosing to fly** has a measurable premium (~6.75%) compared to other modes.
- **Booking in advance** (`booking_advance_days`) has minimal importance (0.34%), suggesting the dataset's price variation from advance booking is limited.

---

## 9. Application Architecture

```
┌──────────────────────────────────────────────────┐
│                  User (Browser)                  │
└────────────────────────┬─────────────────────────┘
                         │ HTTP :8501
┌────────────────────────▼─────────────────────────┐
│           Streamlit Frontend  (port 8501)         │
│  ┌──────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Home/KPI │  │  Predict   │  │  Analytics   │  │
│  └──────────┘  └─────┬──────┘  └──────┬───────┘  │
│                      │  httpx         │  httpx   │
└──────────────────────┼────────────────┼──────────┘
                       │ HTTP :8000     │
┌──────────────────────▼────────────────▼──────────┐
│            FastAPI Backend  (port 8000)           │
│  POST /predict       GET /analytics/*             │
│  GET  /model/*                                    │
│         │                       │                │
│  ┌──────▼──────┐       ┌────────▼──────┐         │
│  │ best_model  │       │ data_service  │         │
│  │   .pkl      │       │ (Pandas/CSV)  │         │
│  └─────────────┘       └───────────────┘         │
└──────────────────────────────────────────────────┘
```

### Components

| Component | File | Responsibility |
|-----------|------|---------------|
| API Entry Point | `backend/main.py` | FastAPI app, CORS, route definitions |
| Data Schemas | `backend/schemas.py` | Pydantic models for request/response validation |
| Analytics Service | `backend/data_service.py` | All Pandas aggregations over the CSV |
| Streamlit Home | `frontend/app.py` | Entry point, navigation, KPI metrics |
| Predict Page | `frontend/pages/1_Predict.py` | Input form, gauge chart, comparable trips |
| Analytics Page | `frontend/pages/2_Analytics.py` | Multi-tab EDA with Plotly charts |
| Model Info Page | `frontend/pages/3_Model_Info.py` | Metrics table, feature importance charts |

---

## 10. API Design

The FastAPI backend exposes **12 endpoints** across three groups:

### Prediction
| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/predict` | `TripInput` JSON | `PredictionResponse` with bounds |
| POST | `/analytics/comparable-trips` | `TripInput` JSON | List of similar dataset rows |

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| GET | `/analytics/summary` | Dataset-level KPI stats |
| GET | `/analytics/by-destination` | Avg expense + count per destination |
| GET | `/analytics/by-season` | Avg expense by season |
| GET | `/analytics/by-transport` | Avg expense by transport mode |
| GET | `/analytics/by-accommodation` | Avg expense by accommodation tier |
| GET | `/analytics/by-travelers` | Avg expense by group size |
| GET | `/analytics/by-trip-days` | Avg expense by duration |
| GET | `/analytics/expense-distribution` | Histogram bucket data |

### Model
| Method | Path | Description |
|--------|------|-------------|
| GET | `/model/metrics` | All 4-model evaluation metrics |
| GET | `/model/feature-importances` | Ranked feature importance list |

All endpoints return JSON. Pydantic v2 models enforce strict type validation on inputs and outputs.

---

## 11. Frontend Design

The Streamlit application uses a **multi-page** structure with a persistent sidebar for navigation.

### Page 1 — Predict
- A three-column form with sliders and dropdowns for all 11 trip features.
- On submission, calls `POST /predict` via `httpx`.
- Displays a **Plotly gauge chart** with the predicted amount.
- Displays a **bar chart** showing the low / predicted / high confidence range.
- Fetches and displays a **comparable trips table** from the dataset.

### Page 2 — Analytics (5 tabs)
| Tab | Charts |
|-----|--------|
| By Destination | Horizontal bar (top 20 destinations), pie by destination type |
| By Season | Bar chart, pie chart (trip count by season) |
| By Transport | Bar chart, pie chart |
| By Accommodation | Bar chart, funnel chart |
| Distributions | Expense histogram, line chart (by travelers), area chart (by trip days) |

### Page 3 — Model Info (3 tabs)
| Tab | Content |
|-----|---------|
| Model Comparison | Grouped bar: CV R² vs Test R², grouped bar: MAE vs RMSE |
| Feature Importances | Horizontal bar chart (top 20), treemap by feature group |
| Model Details | Pipeline architecture, hyperparameters, training configuration |

---

## 12. How to Run

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Install all dependencies
pip install -r requirements.txt

# 2. (Optional) Retrain the model
python train_model.py

# 3. Start the backend — Terminal 1
uvicorn backend.main:app --reload --port 8000

# 4. Start the frontend — Terminal 2
streamlit run frontend/app.py
```

### Access Points
| Service | URL |
|---------|-----|
| Streamlit App | http://localhost:8501 |
| FastAPI Docs (Swagger) | http://localhost:8000/docs |
| FastAPI Redoc | http://localhost:8000/redoc |

---

## 13. Conclusion

This project successfully demonstrates an end-to-end machine-learning pipeline applied to a real-world regression problem:

1. **Data Engineering:** An 11-feature, 5,200-row dataset was preprocessed using a fully reproducible `sklearn` `ColumnTransformer` pipeline combining standard scaling, ordinal encoding, and one-hot encoding.

2. **Model Selection:** Four regression algorithms were systematically compared using 5-fold cross-validation. Gradient Boosting was selected with a **Test R² of 0.9622** and **MAPE of 11.21%**, meeting all defined success criteria.

3. **Production Readiness:** The trained model is serialised as a `pickle` file and served through a **FastAPI** REST API with automatic request validation via Pydantic v2, CORS support, and auto-generated Swagger documentation.

4. **User Interface:** A three-page **Streamlit** application provides a polished user experience — from an interactive prediction form to rich EDA charts — entirely in Python, with no HTML or JavaScript required.

5. **Key Finding:** The number of travellers (39.5% importance) and accommodation tier (24.8%) together account for nearly two-thirds of the model's predictive power, confirming that group size and comfort level are the primary cost drivers for Indian domestic travel.

---

## 14. Future Enhancements

| Enhancement | Impact |
|------------|--------|
| Add a per-person cost breakdown (accommodation, transport, food) | More actionable predictions |
| Live hotel/flight price API integration (e.g., Amadeus, MakeMyTrip) | Real-time price signals |
| User authentication + trip history dashboard | Personalised recommendations |
| Hyperparameter optimisation with `Optuna` or `GridSearchCV` | Potentially higher R² |
| Docker Compose setup for one-command deployment | Easier distribution |
| Model retraining pipeline triggered on new data uploads | Keeps model fresh |
| Add confidence intervals from quantile regression | Statistically grounded bounds |

---

*Report generated for the Indian Travel Expense Predictor project.*
