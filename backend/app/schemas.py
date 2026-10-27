"""Pydantic request/response schemas and consistent error envelope."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class CandidateOut(BaseModel):
    species_id: int
    label: str
    common_name: str
    scientific_name: str | None = None
    scientific_name_verified: bool = False
    score: float = Field(..., description="Raw (uncalibrated) softmax score")


class PredictionOut(BaseModel):
    prediction_id: str
    model_version: str
    top_prediction: CandidateOut
    candidates: list[CandidateOut]
    confident: bool
    confidence_status: str
    confidence_note: str
    inference_ms: float


class ModelInfoOut(BaseModel):
    model_name: str
    model_version: str
    available: bool
    load_error: str | None = None
    num_classes: int
    input_size: list[int]
    preprocessing: dict
    dataset_slug: str | None = None
    tensorflow_version: str | None = None
    parameter_count: int | None = None
    artifact_size_mb: float | None = None


class SpeciesOut(BaseModel):
    species_id: int
    label: str
    common_name: str
    scientific_name: str | None = None
    scientific_name_verified: bool
    taxonomy_source: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class GradcamOut(BaseModel):
    species_id: int
    common_name: str
    original_png: str
    overlay_png: str
    heatmap_png: str
    note: str


class ObservationOut(BaseModel):
    species_code: str | None = None
    common_name: str | None = None
    scientific_name: str | None = None
    location_name: str | None = None
    location_id: str | None = None
    observed_at: str | None = None
    count: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_km: float | None = None
    observation_valid: bool | None = None
    observation_reviewed: bool | None = None
    location_private: bool | None = None
    checklist_id: str | None = None
    map_url: str | None = None
    source: str = "eBird"
    source_url: str = "https://ebird.org"


class SearchCenter(BaseModel):
    lat: float
    lng: float


class ObservationsOut(BaseModel):
    status: str  # "ok" | "empty" | "unavailable"
    count: int
    observations: list[ObservationOut]
    message: str | None = None
    search_center: SearchCenter
    radius_km: int
    back_days: int
    query: dict


class HotspotOut(BaseModel):
    location_id: str | None = None
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    num_species_all_time: int | None = None
    latest_obs_dt: str | None = None
    distance_km: float | None = None
    has_recent_species: bool = False
    map_url: str | None = None
    source: str = "eBird"


class SpeciesSightingsOut(BaseModel):
    # status: ok | empty | unavailable | unresolved
    status: str
    species_id: int
    common_name: str
    scientific_name: str | None = None
    species_code: str | None = None
    search_center: SearchCenter
    radius_km: int
    back_days: int
    sighting_count: int
    sightings: list[ObservationOut]
    hotspots: list[HotspotOut]
    message: str | None = None
    captive_note: str
