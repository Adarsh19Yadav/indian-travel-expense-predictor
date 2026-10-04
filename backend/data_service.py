"""Pandas-powered analytics service over the travel expense dataset."""

import json
from pathlib import Path
import pandas as pd
import numpy as np

_BASE = Path(__file__).parent.parent
_CSV  = _BASE / "dataset_indian_travel_expense.csv"
_META = _BASE / "model" / "metadata.json"

# Load once at import time
_df = pd.read_csv(_CSV)

with open(_META) as f:
    _meta = json.load(f)


# ── Dataset summary ───────────────────────────────────────────────────────────

def get_summary() -> dict:
    exp = _df["actual_trip_expense"]
    return {
        "total_records":       int(len(_df)),
        "avg_expense":         round(float(exp.mean()), 2),
        "min_expense":         round(float(exp.min()), 2),
        "max_expense":         round(float(exp.max()), 2),
        "median_expense":      round(float(exp.median()), 2),
        "destinations":        int(_df["destination"].nunique()),
        "destination_types":   sorted(_df["destination_type"].unique().tolist()),
        "transport_modes":     sorted(_df["transport_mode"].unique().tolist()),
        "accommodation_types": sorted(_df["accommodation_type"].unique().tolist()),
        "seasons":             sorted(_df["travel_season"].unique().tolist()),
        "meal_plans":          sorted(_df["meal_plan"].unique().tolist()),
    }


# ── By destination ────────────────────────────────────────────────────────────

def get_by_destination() -> list[dict]:
    grp = (
        _df.groupby(["destination", "destination_type"], as_index=False)
        .agg(avg_expense=("actual_trip_expense", "mean"),
             trip_count =("actual_trip_expense", "count"))
        .sort_values("avg_expense", ascending=False)
    )
    grp["avg_expense"] = grp["avg_expense"].round(2)
    return grp.to_dict(orient="records")


# ── By season ─────────────────────────────────────────────────────────────────

def get_by_season() -> list[dict]:
    order = ["Off-Peak", "Shoulder", "Peak"]
    grp = (
        _df.groupby("travel_season", as_index=False)
        .agg(avg_expense=("actual_trip_expense", "mean"),
             trip_count =("actual_trip_expense", "count"))
    )
    grp["avg_expense"] = grp["avg_expense"].round(2)
    grp["_order"] = grp["travel_season"].map({s: i for i, s in enumerate(order)})
    grp = grp.sort_values("_order").drop(columns="_order")
    grp = grp.rename(columns={"travel_season": "season"})
    return grp.to_dict(orient="records")


# ── By transport ──────────────────────────────────────────────────────────────

def get_by_transport() -> list[dict]:
    grp = (
        _df.groupby("transport_mode", as_index=False)
        .agg(avg_expense=("actual_trip_expense", "mean"),
             trip_count =("actual_trip_expense", "count"))
        .sort_values("avg_expense", ascending=False)
    )
    grp["avg_expense"] = grp["avg_expense"].round(2)
    return grp.to_dict(orient="records")


# ── By accommodation ──────────────────────────────────────────────────────────

def get_by_accommodation() -> list[dict]:
    order = ["Budget", "2-Star", "3-Star", "4-Star", "5-Star"]
    grp = (
        _df.groupby("accommodation_type", as_index=False)
        .agg(avg_expense=("actual_trip_expense", "mean"),
             trip_count =("actual_trip_expense", "count"))
    )
    grp["avg_expense"] = grp["avg_expense"].round(2)
    grp["_order"] = grp["accommodation_type"].map({s: i for i, s in enumerate(order)})
    grp = grp.sort_values("_order").drop(columns="_order")
    return grp.to_dict(orient="records")


# ── Expense distribution (histogram buckets) ──────────────────────────────────

def get_expense_distribution(bins: int = 20) -> dict:
    counts, edges = np.histogram(_df["actual_trip_expense"], bins=bins)
    labels = [f"{int(edges[i]/1000)}k-{int(edges[i+1]/1000)}k" for i in range(len(edges)-1)]
    return {"labels": labels, "counts": counts.tolist()}


# ── Comparable trips ──────────────────────────────────────────────────────────

def get_comparable_trips(
    destination: str,
    transport_mode: str,
    accommodation_type: str,
    n: int = 5,
) -> list[dict]:
    mask = (
        (_df["destination"]        == destination) &
        (_df["transport_mode"]     == transport_mode) &
        (_df["accommodation_type"] == accommodation_type)
    )
    subset = _df[mask].copy()
    if len(subset) == 0:
        subset = _df[_df["destination"] == destination].copy()
    if len(subset) == 0:
        subset = _df.copy()
    sample = subset.sample(min(n, len(subset)), random_state=1)
    return sample.to_dict(orient="records")


# ── Model metrics ─────────────────────────────────────────────────────────────

def get_model_metrics() -> dict:
    return _meta


# ── Feature importances ───────────────────────────────────────────────────────

def get_feature_importances() -> list[dict]:
    # Hard-coded from training output (Gradient Boosting top features)
    # These are re-read from the saved model at startup in main.py for accuracy
    return []


# ── Expense by travelers ──────────────────────────────────────────────────────

def get_by_travelers() -> list[dict]:
    grp = (
        _df.groupby("travelers", as_index=False)
        .agg(avg_expense=("actual_trip_expense", "mean"),
             trip_count =("actual_trip_expense", "count"))
        .sort_values("travelers")
    )
    grp["avg_expense"] = grp["avg_expense"].round(2)
    return grp.to_dict(orient="records")


# ── Expense by trip duration ──────────────────────────────────────────────────

def get_by_trip_days() -> list[dict]:
    grp = (
        _df.groupby("trip_days", as_index=False)
        .agg(avg_expense=("actual_trip_expense", "mean"),
             trip_count =("actual_trip_expense", "count"))
        .sort_values("trip_days")
    )
    grp["avg_expense"] = grp["avg_expense"].round(2)
    return grp.to_dict(orient="records")
