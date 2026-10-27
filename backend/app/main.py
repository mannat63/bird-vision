"""BirdVision AI FastAPI application.

Endpoints:
  GET  /health                     process health
  GET  /ready                      model artifacts loaded?
  GET  /api/model-info             architecture/version/class count
  POST /api/predict                genuine CNN inference on an uploaded image
  POST /api/explain                Grad-CAM for an uploaded image
  GET  /api/species/{id}           species metadata
  POST /api/species/{id}/ask       Groq-assisted Q&A (optional)
  GET  /api/species/{id}/intel     Groq species intelligence (optional)
  GET  /api/observations/nearby    eBird recent nearby observations
  GET  /api/metrics                persisted evaluation metrics
"""

import json
import logging
import uuid

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app import __version__
from app.config import Settings, get_settings
from app.ml import gradcam
from app.ml.model import ModelEngine, get_engine
from app.ml.preprocess import InvalidImageError
from app.schemas import (
    AskRequest,
    GradcamOut,
    ModelInfoOut,
    ObservationsOut,
    PredictionOut,
    SpeciesOut,
    SpeciesSightingsOut,
)
from app.services import ebird as ebird_service
from app.services import llm as llm_service
from app.services.species import species_record

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("birdvision")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="BirdVision AI API", version=__version__)
app.state.limiter = limiter

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

GRADCAM_NOTE = (
    "Grad-CAM shows image regions whose activations most influenced the "
    "predicted class score. It is an attribution heatmap, not proof of causal "
    "reasoning and not a correctness guarantee."
)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429, content={"error": "rate_limited", "detail": str(exc)}
    )


@app.on_event("startup")
def _startup() -> None:
    # Attempt to load the model at startup so /ready reflects reality, but do
    # not crash the process if it fails — endpoints report unavailability.
    try:
        get_engine().load()
    except Exception as exc:  # pragma: no cover
        logger.error("Model load error at startup: %s", exc)


def engine_dep() -> ModelEngine:
    eng = get_engine()
    eng.load()
    return eng


# --------------------------------------------------------------------------- #
# Health / readiness / info
# --------------------------------------------------------------------------- #
@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/ready")
def ready(eng: ModelEngine = Depends(engine_dep)) -> JSONResponse:
    if eng.available:
        return JSONResponse({"ready": True})
    return JSONResponse(
        {"ready": False, "error": eng.load_error or "model unavailable"},
        status_code=503,
    )


@app.get("/api/model-info", response_model=ModelInfoOut)
def model_info(eng: ModelEngine = Depends(engine_dep)) -> ModelInfoOut:
    return ModelInfoOut(**eng.model_info())


# --------------------------------------------------------------------------- #
# Prediction
# --------------------------------------------------------------------------- #
async def _read_upload(file: UploadFile, settings: Settings) -> bytes:
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(415, "Unsupported media type; upload an image")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty upload")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            413, f"Image exceeds {settings.max_upload_bytes // (1024*1024)} MB limit"
        )
    # Magic-byte sniff: reject files that are not real images regardless of
    # the client-declared content type.
    if not _looks_like_image(data):
        raise HTTPException(415, "File does not appear to be a valid image")
    return data


_MAGIC = [b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"BM", b"RIFF"]


def _looks_like_image(data: bytes) -> bool:
    head = data[:16]
    return any(head.startswith(m) for m in _MAGIC) or (
        head[:4] == b"RIFF" and b"WEBP" in data[:16]
    )


@app.post("/api/predict", response_model=PredictionOut)
@limiter.limit("30/minute")
async def predict(
    request: Request,  # required positional for slowapi
    file: UploadFile = File(...),
    eng: ModelEngine = Depends(engine_dep),
    settings: Settings = Depends(get_settings),
) -> PredictionOut:
    if not eng.available:
        raise HTTPException(503, "Model not available")
    data = await _read_upload(file, settings)
    try:
        result = eng.predict(data)
    except InvalidImageError:
        raise HTTPException(400, "Could not decode image")
    cands = [c.__dict__ for c in result.candidates]
    return PredictionOut(
        prediction_id=str(uuid.uuid4()),
        model_version=result.model_version,
        top_prediction=cands[0],
        candidates=cands,
        confident=result.confident,
        confidence_status=result.confidence_status,
        confidence_note=result.confidence_note,
        inference_ms=result.inference_ms,
    )


@app.post("/api/explain", response_model=GradcamOut)
@limiter.limit("15/minute")
async def explain(
    request: Request,
    file: UploadFile = File(...),
    eng: ModelEngine = Depends(engine_dep),
    settings: Settings = Depends(get_settings),
) -> GradcamOut:
    if not eng.available:
        raise HTTPException(503, "Model not available")
    data = await _read_upload(file, settings)
    try:
        result = eng.predict(data)
    except InvalidImageError:
        raise HTTPException(400, "Could not decode image")
    top = result.candidates[0]
    try:
        images = gradcam.generate(data, eng._model, top.species_id)
    except gradcam.GradCAMError as exc:
        raise HTTPException(500, f"Grad-CAM unavailable: {exc}")
    return GradcamOut(
        species_id=top.species_id,
        common_name=top.common_name,
        note=GRADCAM_NOTE,
        **images,
    )


# --------------------------------------------------------------------------- #
# Species metadata + LLM enrichment (Groq)
# --------------------------------------------------------------------------- #
_LLM_KIND_HTTP = {
    "rate_limited": (429, "AI enrichment is rate-limited. Please wait and retry."),
    "unavailable": (503, "AI enrichment is temporarily unavailable (provider "
                         "overloaded). The species ID and all other features "
                         "still work — retry in a moment."),
    "timeout": (504, "AI enrichment timed out. Please retry."),
    "auth": (502, "AI enrichment is misconfigured on the server "
                  "(authentication). This does not affect species ID."),
    "quota": (402, "AI enrichment quota has been exhausted on the server."),
    "config": (502, "AI enrichment request was rejected as invalid."),
    "empty": (502, "AI enrichment returned no content. Please retry."),
}


def _llm_http(exc: "llm_service.LLMError") -> HTTPException:
    status, message = _LLM_KIND_HTTP.get(
        getattr(exc, "kind", "unavailable"),
        (503, "AI enrichment is temporarily unavailable."),
    )
    return HTTPException(status, message)


def _species_or_404(species_id: int, eng: ModelEngine) -> dict:
    if species_id < 0 or species_id >= len(eng.class_names):
        raise HTTPException(404, "Unknown species id")
    return species_record(species_id, eng.class_names[species_id])


@app.get("/api/species/{species_id}", response_model=SpeciesOut)
def species(species_id: int, eng: ModelEngine = Depends(engine_dep)) -> SpeciesOut:
    return SpeciesOut(**_species_or_404(species_id, eng))


@app.get("/api/species/{species_id}/intel")
@limiter.limit("10/minute")
def species_intel(
    request: Request, species_id: int, eng: ModelEngine = Depends(engine_dep)
) -> dict:
    rec = _species_or_404(species_id, eng)
    if not llm_service.is_configured():
        raise HTTPException(503, "AI enrichment not configured")
    try:
        return llm_service.species_intelligence(
            rec["common_name"], rec["scientific_name"]
        )
    except llm_service.LLMError as exc:
        raise _llm_http(exc)


@app.post("/api/species/{species_id}/ask")
@limiter.limit("10/minute")
def species_ask(
    request: Request,
    species_id: int,
    body: AskRequest,
    eng: ModelEngine = Depends(engine_dep),
) -> dict:
    rec = _species_or_404(species_id, eng)
    if not llm_service.is_configured():
        raise HTTPException(503, "AI enrichment not configured")
    try:
        return llm_service.ask_expert(
            rec["common_name"], rec["scientific_name"], body.question
        )
    except llm_service.LLMError as exc:
        raise _llm_http(exc)


# --------------------------------------------------------------------------- #
# eBird observations
# --------------------------------------------------------------------------- #
CAPTIVE_NOTE = (
    "These are wild, community-reported sightings and birding hotspots from "
    "eBird — not captive-viewing venues. BirdVision does not assert that any "
    "zoo, aviary or wildlife centre holds this species, because no reliable "
    "captive-collection data source is integrated."
)


def _obs_meta(lat: float, lng: float, dist: int, back: int) -> dict:
    return {
        "search_center": {"lat": lat, "lng": lng},
        "radius_km": dist,
        "back_days": back,
        "query": {"lat": lat, "lng": lng, "dist": dist, "back": back},
    }


@app.get("/api/observations/nearby", response_model=ObservationsOut)
@limiter.limit("20/minute")
def observations_nearby(
    request: Request,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    dist: int = Query(25, ge=1, le=50),
    back: int = Query(14, ge=1, le=30),
    max_results: int = Query(50, ge=1, le=200),
) -> ObservationsOut:
    meta = _obs_meta(lat, lng, dist, back)
    if not get_settings().ebird_api_key:
        return ObservationsOut(
            status="unavailable", count=0, observations=[],
            message="eBird integration not configured on the server", **meta,
        )
    try:
        obs = ebird_service.nearby_observations(lat, lng, dist, back, max_results)
    except ebird_service.EbirdError as exc:
        return ObservationsOut(
            status="unavailable", count=0, observations=[],
            message=f"eBird data unavailable: {exc}", **meta,
        )
    if not obs:
        return ObservationsOut(
            status="empty", count=0, observations=[],
            message="No eBird observations reported for this area/time window",
            **meta,
        )
    return ObservationsOut(status="ok", count=len(obs), observations=obs, **meta)


@app.get("/api/species/{species_id}/sightings", response_model=SpeciesSightingsOut)
@limiter.limit("20/minute")
def species_sightings(
    request: Request,
    species_id: int,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    dist: int = Query(25, ge=1, le=50),
    back: int = Query(14, ge=1, le=30),
    eng: ModelEngine = Depends(engine_dep),
) -> SpeciesSightingsOut:
    """'Where can I see this bird near me?' — species-specific recent eBird
    sightings plus nearby hotspots, using the current identification."""
    rec = _species_or_404(species_id, eng)
    base = dict(
        species_id=species_id,
        common_name=rec["common_name"],
        scientific_name=rec["scientific_name"],
        search_center={"lat": lat, "lng": lng},
        radius_km=dist,
        back_days=back,
        captive_note=CAPTIVE_NOTE,
    )

    if not get_settings().ebird_api_key:
        return SpeciesSightingsOut(
            status="unavailable", species_code=None, sighting_count=0,
            sightings=[], hotspots=[],
            message="eBird integration not configured on the server", **base,
        )

    # Resolve to an eBird species code via the VERIFIED scientific name only.
    if not rec["scientific_name"]:
        return SpeciesSightingsOut(
            status="unresolved", species_code=None, sighting_count=0,
            sightings=[], hotspots=[],
            message=(
                "This species has no human-verified scientific name in our "
                "metadata, so it cannot be resolved to an eBird taxon. "
                "Species-specific sightings are unavailable for it."
            ), **base,
        )
    try:
        code = ebird_service.resolve_species_code(rec["scientific_name"])
    except ebird_service.EbirdError as exc:
        return SpeciesSightingsOut(
            status="unavailable", species_code=None, sighting_count=0,
            sightings=[], hotspots=[],
            message=f"eBird taxonomy unavailable: {exc}", **base,
        )
    if not code:
        return SpeciesSightingsOut(
            status="unresolved", species_code=None, sighting_count=0,
            sightings=[], hotspots=[],
            message=(
                f"'{rec['scientific_name']}' was not found in the eBird "
                "taxonomy, so species-specific sightings cannot be fetched."
            ), **base,
        )

    try:
        sightings = ebird_service.species_recent_nearby(code, lat, lng, dist, back)
        loc_ids = {s["location_id"] for s in sightings if s.get("location_id")}
        hotspots = ebird_service.nearby_hotspots(lat, lng, dist, loc_ids)
    except ebird_service.EbirdError as exc:
        return SpeciesSightingsOut(
            status="unavailable", species_code=code, sighting_count=0,
            sightings=[], hotspots=[],
            message=f"eBird data unavailable: {exc}", **base,
        )

    status = "ok" if sightings else "empty"
    msg = None if sightings else (
        f"No recent {rec['common_name']} reports within {dist} km in the last "
        f"{back} days. Try a larger radius or a longer date window."
    )
    return SpeciesSightingsOut(
        status=status, species_code=code, sighting_count=len(sightings),
        sightings=sightings, hotspots=hotspots[:15], message=msg, **base,
    )


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
@app.get("/api/metrics")
def metrics(settings: Settings = Depends(get_settings)) -> dict:
    path = settings.metrics_path
    if not path.exists():
        return {"status": "not_evaluated",
                "message": "No evaluation metrics artifact found"}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["status"] = "ok"
    return data
