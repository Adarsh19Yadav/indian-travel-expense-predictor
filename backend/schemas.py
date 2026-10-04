"""Pydantic request/response schemas for the Travel Expense Prediction API."""

from typing import Literal
from pydantic import BaseModel, Field


# ── Input schema ──────────────────────────────────────────────────────────────

class TripInput(BaseModel):
    destination: str = Field(..., example="Goa")
    destination_type: Literal[
        "Heritage", "Religious", "Mountain", "City",
        "Nature", "Beach", "Wildlife", "Adventure"
    ] = Field(..., example="Beach")
    travelers: int = Field(..., ge=1, le=20, example=2)
    trip_days: int = Field(..., ge=1, le=30, example=5)
    transport_mode: Literal["Train", "Car", "Flight", "Bus"] = Field(..., example="Flight")
    accommodation_type: Literal[
        "Budget", "2-Star", "3-Star", "4-Star", "5-Star"
    ] = Field(..., example="3-Star")
    meal_plan: Literal[
        "Room Only", "Breakfast", "Half Board", "Full Board"
    ] = Field(..., example="Breakfast")
    activities_count: int = Field(..., ge=0, le=20, example=3)
    travel_season: Literal["Off-Peak", "Shoulder", "Peak"] = Field(..., example="Peak")
    booking_advance_days: int = Field(..., ge=0, le=365, example=30)
    distance_km: int = Field(..., ge=1, le=5000, example=1400)


# ── Output schemas ────────────────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    predicted_expense: float
    lower_bound: float
    upper_bound: float
    model_name: str
    mape_pct: float


class DestinationStat(BaseModel):
    destination: str
    avg_expense: float
    trip_count: int
    destination_type: str


class SeasonStat(BaseModel):
    season: str
    avg_expense: float
    trip_count: int


class TransportStat(BaseModel):
    transport_mode: str
    avg_expense: float
    trip_count: int


class AccommodationStat(BaseModel):
    accommodation_type: str
    avg_expense: float
    trip_count: int


class DatasetSummary(BaseModel):
    total_records: int
    avg_expense: float
    min_expense: float
    max_expense: float
    median_expense: float
    destinations: int
    destination_types: list[str]
    transport_modes: list[str]
    accommodation_types: list[str]
    seasons: list[str]
    meal_plans: list[str]


class FeatureImportance(BaseModel):
    feature: str
    importance: float


class ModelMetrics(BaseModel):
    best_model: str
    test_r2: float
    test_mae: float
    test_rmse: float
    test_mape: float
    all_results: dict
