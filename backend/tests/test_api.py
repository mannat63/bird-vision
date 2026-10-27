"""API tests via FastAPI TestClient. Groq/eBird are mocked."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("tensorflow")

from app.main import app  # noqa: E402
from app.ml.model import get_engine  # noqa: E402

ARTIFACTS = Path(__file__).resolve().parents[2]
SAMPLE = ARTIFACTS / "gradcam_example.png"


@pytest.fixture(scope="module")
def client():
    get_engine().load()
    return TestClient(app)


def _model_ready():
    eng = get_engine()
    eng.load()
    return eng.available


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_model_info(client):
    r = client.get("/api/model-info")
    assert r.status_code == 200
    body = r.json()
    assert body["num_classes"] == 200
    assert body["model_name"] == "EfficientNetB0"


def test_ready(client):
    r = client.get("/ready")
    assert r.status_code in (200, 503)


@pytest.mark.skipif(not _model_ready(), reason="model unavailable")
def test_predict_success(client):
    with open(SAMPLE, "rb") as f:
        r = client.post("/api/predict", files={"file": ("b.png", f, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert len(body["candidates"]) == 3
    assert body["top_prediction"]["species_id"] >= 0
    assert "confidence_note" in body


def test_predict_rejects_non_image(client):
    r = client.post(
        "/api/predict", files={"file": ("x.txt", b"hello world", "text/plain")}
    )
    assert r.status_code in (400, 415)


def test_predict_rejects_empty(client):
    r = client.post("/api/predict", files={"file": ("x.png", b"", "image/png")})
    assert r.status_code == 400


def test_species_metadata(client):
    r = client.get("/api/species/0")
    assert r.status_code == 200
    assert r.json()["common_name"] == "Black footed Albatross"


def test_species_out_of_range(client):
    assert client.get("/api/species/9999").status_code == 404


def test_observations_unavailable_without_key(client, monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("EBIRD_API_KEY", "")
    r = client.get("/api/observations/nearby?lat=40&lng=-75")
    assert r.status_code == 200
    assert r.json()["status"] == "unavailable"
    get_settings.cache_clear()


def test_observations_empty_vs_ok(client, monkeypatch):
    from app.config import get_settings
    from app.services import ebird

    get_settings.cache_clear()
    monkeypatch.setenv("EBIRD_API_KEY", "test-key")
    monkeypatch.setattr(ebird, "nearby_observations", lambda *a, **k: [])
    r = client.get("/api/observations/nearby?lat=40&lng=-75")
    assert r.json()["status"] == "empty"
    get_settings.cache_clear()


def test_observations_invalid_coords(client):
    assert client.get("/api/observations/nearby?lat=999&lng=0").status_code == 422


def test_llm_unavailable_without_key(client, monkeypatch):
    from app.services import llm

    monkeypatch.setattr(llm, "is_configured", lambda: False)
    r = client.get("/api/species/0/intel")
    assert r.status_code == 503


def test_llm_error_kind_maps_to_status(client, monkeypatch):
    from app.main import _LLM_KIND_HTTP
    from app.services import llm

    monkeypatch.setattr(llm, "is_configured", lambda: True)

    def boom(*a, **k):
        raise llm.LLMError("429 rate", kind="rate_limited")

    monkeypatch.setattr(llm, "species_intelligence", boom)
    r = client.get("/api/species/0/intel")
    assert r.status_code == _LLM_KIND_HTTP["rate_limited"][0] == 429


def test_metrics_endpoint(client):
    r = client.get("/api/metrics")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["num_classes"] == 200
    assert "test_top1_accuracy" in body


# --- location integrity: response echoes the searched center (P3) --------- #
def test_nearby_echoes_search_center(client, monkeypatch):
    from app.config import get_settings
    from app.services import ebird

    get_settings.cache_clear()
    monkeypatch.setenv("EBIRD_API_KEY", "test-key")
    monkeypatch.setattr(ebird, "nearby_observations", lambda *a, **k: [])
    r = client.get("/api/observations/nearby?lat=42.3601&lng=-71.0589&dist=10&back=5")
    body = r.json()
    assert body["search_center"] == {"lat": 42.3601, "lng": -71.0589}
    assert body["radius_km"] == 10 and body["back_days"] == 5
    get_settings.cache_clear()


# --- species-specific sightings (P4) -------------------------------------- #
def test_species_sightings_ok(client, monkeypatch):
    from app.config import get_settings
    from app.services import ebird

    get_settings.cache_clear()
    monkeypatch.setenv("EBIRD_API_KEY", "test-key")
    monkeypatch.setattr(ebird, "resolve_species_code", lambda sci: "bkfalb")
    monkeypatch.setattr(ebird, "species_recent_nearby", lambda *a, **k: [
        {"species_code": "bkfalb", "common_name": "Black-footed Albatross",
         "scientific_name": "Phoebastria nigripes", "location_name": "Cape",
         "location_id": "L9", "observed_at": "2026-10-20", "count": 1,
         "latitude": 42.0, "longitude": -70.9, "distance_km": 12.3,
         "observation_valid": True, "observation_reviewed": False,
         "location_private": False, "checklist_id": "S1",
         "map_url": "https://maps", "source": "eBird",
         "source_url": "https://ebird.org"},
    ])
    monkeypatch.setattr(ebird, "nearby_hotspots", lambda *a, **k: [])
    r = client.get("/api/species/0/sightings?lat=42.36&lng=-71.05&dist=25&back=14")
    body = r.json()
    assert body["status"] == "ok"
    assert body["species_code"] == "bkfalb"
    assert body["search_center"] == {"lat": 42.36, "lng": -71.05}
    assert body["sighting_count"] == 1
    get_settings.cache_clear()


def test_species_sightings_unresolved_without_sci_name(client, monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("EBIRD_API_KEY", "test-key")
    # species 16 ("017.Cardinal") has no verified scientific name in our data.
    r = client.get("/api/species/16/sightings?lat=42.36&lng=-71.05")
    assert r.json()["status"] == "unresolved"
    get_settings.cache_clear()


def test_species_sightings_empty_when_no_reports(client, monkeypatch):
    from app.config import get_settings
    from app.services import ebird

    get_settings.cache_clear()
    monkeypatch.setenv("EBIRD_API_KEY", "test-key")
    monkeypatch.setattr(ebird, "resolve_species_code", lambda sci: "bkfalb")
    monkeypatch.setattr(ebird, "species_recent_nearby", lambda *a, **k: [])
    monkeypatch.setattr(ebird, "nearby_hotspots", lambda *a, **k: [])
    r = client.get("/api/species/0/sightings?lat=42.36&lng=-71.05")
    body = r.json()
    assert body["status"] == "empty"
    assert body["sighting_count"] == 0
    get_settings.cache_clear()


def test_species_sightings_invalid_coords(client):
    assert client.get("/api/species/0/sightings?lat=999&lng=0").status_code == 422
