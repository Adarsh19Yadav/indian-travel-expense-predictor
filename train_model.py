"""
Travel Expense Prediction — ML Pipeline
Target: actual_trip_expense (regression)
Models evaluated: Linear Regression, Random Forest, Gradient Boosting, XGBoost
Best model is saved to model/best_model.pkl
"""

import os
import warnings
import pickle
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error,
)

warnings.filterwarnings("ignore")

# ── 1. Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv("dataset_indian_travel_expense.csv")
print(f"Dataset: {df.shape[0]:,} rows × {df.shape[1]} columns")

TARGET = "actual_trip_expense"
X = df.drop(columns=[TARGET])
y = df[TARGET]

# ── 2. Feature definitions ────────────────────────────────────────────────────
num_features = ["travelers", "trip_days", "activities_count",
                "booking_advance_days", "distance_km"]

# Ordered categoricals — gives the model meaningful ordinal signal
accommodation_order = ["Budget", "2-Star", "3-Star", "4-Star", "5-Star"]
season_order        = ["Off-Peak", "Shoulder", "Peak"]
meal_order          = ["Room Only", "Breakfast", "Half Board", "Full Board"]

ord_features  = ["accommodation_type", "travel_season", "meal_plan"]
nom_features  = ["destination", "destination_type", "transport_mode"]   # one-hot

# ── 3. Preprocessing ──────────────────────────────────────────────────────────
from sklearn.preprocessing import OneHotEncoder

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), num_features),
        ("ord", OrdinalEncoder(
            categories=[accommodation_order, season_order, meal_order],
            handle_unknown="use_encoded_value", unknown_value=-1
         ), ord_features),
        ("nom", OneHotEncoder(handle_unknown="ignore", sparse_output=False), nom_features),
    ],
    remainder="drop",
)

# ── 4. Train / test split ─────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Train: {len(X_train):,}  |  Test: {len(X_test):,}")

# ── 5. Model definitions ──────────────────────────────────────────────────────
models = {
    "Ridge Regression": Ridge(alpha=10),
    "Random Forest": RandomForestRegressor(
        n_estimators=300, max_depth=None, min_samples_leaf=2,
        n_jobs=-1, random_state=42
    ),
    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=400, learning_rate=0.05, max_depth=5,
        subsample=0.8, min_samples_leaf=3, random_state=42
    ),
}

# Optionally add XGBoost if available
try:
    from xgboost import XGBRegressor
    models["XGBoost"] = XGBRegressor(
        n_estimators=400, learning_rate=0.05, max_depth=6,
        subsample=0.8, colsample_bytree=0.8, reg_lambda=1,
        n_jobs=-1, random_state=42, verbosity=0
    )
    print("XGBoost detected — included in evaluation.")
except ImportError:
    print("XGBoost not installed — skipping (pip install xgboost to include).")

# ── 6. Train & evaluate ───────────────────────────────────────────────────────
kf = KFold(n_splits=5, shuffle=True, random_state=42)
results = {}

print("\n{:<22}  {:>8}  {:>10}  {:>10}  {:>8}".format(
    "Model", "CV R2", "Test R2", "MAE (INR)", "MAPE %"))
print("-" * 66)

best_r2    = -np.inf
best_name  = None
best_pipe  = None

for name, model in models.items():
    pipe = Pipeline([("pre", preprocessor), ("model", model)])

    # 5-fold CV on training set
    cv_scores = cross_val_score(pipe, X_train, y_train,
                                cv=kf, scoring="r2", n_jobs=-1)

    # Fit on full training set, score on held-out test set
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    r2   = r2_score(y_test, y_pred)
    mae  = mean_absolute_error(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred) * 100
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    results[name] = {
        "cv_r2_mean": cv_scores.mean(),
        "cv_r2_std":  cv_scores.std(),
        "test_r2":    r2,
        "mae":        mae,
        "rmse":       rmse,
        "mape":       mape,
        "y_pred":     y_pred,
    }

    print("{:<22}  {:>8.4f}  {:>10.4f}  {:>10,.0f}  {:>8.2f}".format(
        name, cv_scores.mean(), r2, mae, mape))

    if r2 > best_r2:
        best_r2   = r2
        best_name = name
        best_pipe = pipe

print(f"\nBest model: {best_name}  (Test R2 = {best_r2:.4f})")

# ── 7. Feature importance (tree models) ──────────────────────────────────────
os.makedirs("model", exist_ok=True)

def get_feature_names(pipe):
    pre = pipe.named_steps["pre"]
    num_names = num_features
    ord_names = ord_features
    nom_names = list(pre.named_transformers_["nom"].get_feature_names_out(nom_features))
    return num_names + ord_names + nom_names

if hasattr(best_pipe.named_steps["model"], "feature_importances_"):
    feat_names = get_feature_names(best_pipe)
    importances = best_pipe.named_steps["model"].feature_importances_
    fi_df = (
        pd.DataFrame({"feature": feat_names, "importance": importances})
        .sort_values("importance", ascending=False)
        .head(20)
    )
    print("\nTop-10 feature importances:")
    print(fi_df.head(10).to_string(index=False))

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(fi_df["feature"][::-1], fi_df["importance"][::-1], color="#3b82d4")
    ax.set_xlabel("Importance")
    ax.set_title(f"Feature Importances - {best_name}")
    plt.tight_layout()
    fig.savefig("model/feature_importances.png", dpi=120)
    plt.close()
    print("Saved model/feature_importances.png")

# ── 8. Actual vs predicted plot ───────────────────────────────────────────────
y_best_pred = results[best_name]["y_pred"]
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Scatter: actual vs predicted
axes[0].scatter(y_test, y_best_pred, alpha=0.35, s=18, color="#3b82d4")
lims = [y.min(), y.max()]
axes[0].plot(lims, lims, "r--", lw=1.5)
axes[0].set_xlabel("Actual (INR)")
axes[0].set_ylabel("Predicted (INR)")
axes[0].set_title(f"Actual vs Predicted - {best_name}")

# Residuals
residuals = y_test.values - y_best_pred
axes[1].scatter(y_best_pred, residuals, alpha=0.35, s=18, color="#7c5cd8")
axes[1].axhline(0, color="red", lw=1.5, linestyle="--")
axes[1].set_xlabel("Predicted (INR)")
axes[1].set_ylabel("Residual (INR)")
axes[1].set_title("Residuals Plot")

plt.tight_layout()
fig.savefig("model/actual_vs_predicted.png", dpi=120)
plt.close()
print("Saved model/actual_vs_predicted.png")

# ── 9. Model comparison bar chart ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 4))
names_list = list(results.keys())
r2_list    = [results[n]["test_r2"] for n in names_list]
colors     = ["#3b82d4" if n == best_name else "#c9d8ef" for n in names_list]
bars = ax.bar(names_list, r2_list, color=colors)
ax.set_ylim(0, 1)
ax.set_ylabel("Test R2")
ax.set_title("Model Comparison - Test R2")
for bar, v in zip(bars, r2_list):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 0.005,
            f"{v:.4f}", ha="center", va="bottom", fontsize=9)
plt.tight_layout()
fig.savefig("model/model_comparison.png", dpi=120)
plt.close()
print("Saved model/model_comparison.png")

# ── 10. Save best model & metadata ───────────────────────────────────────────
model_path = "model/best_model.pkl"
with open(model_path, "wb") as f:
    pickle.dump(best_pipe, f)
print(f"Saved best model -> {model_path}")

metadata = {
    "best_model":  best_name,
    "test_r2":     round(best_r2, 6),
    "test_mae":    round(results[best_name]["mae"], 2),
    "test_rmse":   round(results[best_name]["rmse"], 2),
    "test_mape":   round(results[best_name]["mape"], 4),
    "features": {
        "numerical":   num_features,
        "ordinal":     ord_features,
        "nominal":     nom_features,
    },
    "all_results": {
        n: {
            "cv_r2_mean": round(v["cv_r2_mean"], 6),
            "cv_r2_std":  round(v["cv_r2_std"],  6),
            "test_r2":    round(v["test_r2"],    6),
            "mae":        round(v["mae"],         2),
            "rmse":       round(v["rmse"],        2),
            "mape":       round(v["mape"],        4),
        }
        for n, v in results.items()
    },
}
with open("model/metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
print("Saved model/metadata.json")

# ── 11. Quick inference example ───────────────────────────────────────────────
print("\n-- Sample prediction ----------------------------------------------------------")
sample = pd.DataFrame([{
    "destination":          "Goa",
    "destination_type":     "Beach",
    "travelers":            2,
    "trip_days":            5,
    "transport_mode":       "Flight",
    "accommodation_type":   "3-Star",
    "meal_plan":            "Breakfast",
    "activities_count":     3,
    "travel_season":        "Peak",
    "booking_advance_days": 30,
    "distance_km":          1400,
}])
pred = best_pipe.predict(sample)[0]
print(f"  Input: Goa Beach trip, 2 travellers, 5 days, Flight, 3-Star, Peak season")
print(f"  Predicted expense: INR {pred:,.2f}")
print("\nDone!")
