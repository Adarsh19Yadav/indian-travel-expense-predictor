"""
Travel Expense Prediction — FastAPI Backend
Serves both the REST API and the static web frontend from a single process.

Local dev:
    uvicorn backend.main:app --reload --port 8000

Production (Render):
    gunicorn backend.main:app -k uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:$PORT --workers 2
"""

import os
import pickle
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.schemas import (
    TripInput,
    PredictionResponse,
    DestinationStat,
    SeasonStat,
    TransportStat,
    AccommodationStat,
    DatasetSummary,
    FeatureImportance,
    ModelMetrics,
)
import backend.data_service as ds

# ── App init ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Indian Travel Expense Predictor",
    description="Predicts trip expenses using a Gradient Boosting model trained on 5,200 Indian travel records.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load model ────────────────────────────────────────────────────────────────
_BASE        = Path(__file__).parent.parent
_MODEL_PATH  = _BASE / "model" / "best_model.pkl"
_META_PATH   = _BASE / "model" / "metadata.json"

with open(_MODEL_PATH, "rb") as f:
    _model = pickle.load(f)

with open(_META_PATH) as f:
    _meta = json.load(f)

# Pre-compute feature importances once
def _compute_feature_importances() -> list[dict]:
    try:
        estimator = _model.named_steps["model"]
        pre       = _model.named_steps["pre"]
        num_names = ["travelers", "trip_days", "activities_count",
                     "booking_advance_days", "distance_km"]
        ord_names = ["accommodation_type", "travel_season", "meal_plan"]
        nom_names = list(
            pre.named_transformers_["nom"].get_feature_names_out(
                ["destination", "destination_type", "transport_mode"]
            )
        )
        all_names    = num_names + ord_names + nom_names
        importances  = estimator.feature_importances_
        fi = sorted(
            [{"feature": n, "importance": round(float(v), 6)}
             for n, v in zip(all_names, importances)],
            key=lambda x: x["importance"],
            reverse=True,
        )
        return fi
    except Exception:
        return []

_feature_importances = _compute_feature_importances()


# ── Prediction helper ─────────────────────────────────────────────────────────

def _predict_with_bounds(inp: TripInput) -> tuple[float, float, float]:
    row = pd.DataFrame([inp.model_dump()])
    pred = float(_model.predict(row)[0])
    mape = _meta["test_mape"] / 100          # e.g. 0.1121
    margin = pred * mape
    return pred, max(0, pred - margin), pred + margin


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["Health"])
def health():
    """JSON health check — used by the frontend status indicator."""
    return {"status": "ok", "model": _meta["best_model"]}


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(inp: TripInput):
    """Predict the total trip expense for the given inputs."""
    try:
        pred, low, high = _predict_with_bounds(inp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return PredictionResponse(
        predicted_expense=round(pred, 2),
        lower_bound=round(low, 2),
        upper_bound=round(high, 2),
        model_name=_meta["best_model"],
        mape_pct=_meta["test_mape"],
    )


@app.get("/analytics/summary", response_model=DatasetSummary, tags=["Analytics"])
def analytics_summary():
    return ds.get_summary()


@app.get("/analytics/by-destination", response_model=list[DestinationStat], tags=["Analytics"])
def analytics_by_destination():
    return ds.get_by_destination()


@app.get("/analytics/by-season", response_model=list[SeasonStat], tags=["Analytics"])
def analytics_by_season():
    return ds.get_by_season()


@app.get("/analytics/by-transport", response_model=list[TransportStat], tags=["Analytics"])
def analytics_by_transport():
    return ds.get_by_transport()


@app.get("/analytics/by-accommodation", response_model=list[AccommodationStat], tags=["Analytics"])
def analytics_by_accommodation():
    return ds.get_by_accommodation()


@app.get("/analytics/by-travelers", tags=["Analytics"])
def analytics_by_travelers():
    return ds.get_by_travelers()


@app.get("/analytics/by-trip-days", tags=["Analytics"])
def analytics_by_trip_days():
    return ds.get_by_trip_days()


@app.get("/analytics/expense-distribution", tags=["Analytics"])
def analytics_expense_distribution():
    return ds.get_expense_distribution()


@app.post("/analytics/comparable-trips", tags=["Analytics"])
def comparable_trips(inp: TripInput):
    rows = ds.get_comparable_trips(
        inp.destination, inp.transport_mode, inp.accommodation_type
    )
    return rows


@app.get("/model/metrics", response_model=ModelMetrics, tags=["Model"])
def model_metrics():
    return _meta


@app.get("/model/feature-importances", response_model=list[FeatureImportance], tags=["Model"])
def feature_importances():
    return _feature_importances


# ── Static frontend — must be mounted AFTER all API routes ────────────────────
_WEB_DIR = _BASE / "frontend" / "web"

# Serve /static/* → frontend/web/  (css, js, assets)
app.mount("/static", StaticFiles(directory=str(_WEB_DIR)), name="static")

# Catch-all: serve index.html for all non-API GET requests (SPA routing)
@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    """Serve the SPA index.html for any path not matched by an API route."""
    index = _WEB_DIR / "index.html"
    return FileResponse(str(index))
