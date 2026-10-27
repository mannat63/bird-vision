"""eBird service tests with mocked HTTP (no live API calls)."""

from __future__ import annotations

import httpx
import pytest

from app.services import ebird


class _Resp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else []

    def json(self):
        return self._payload


class _Client:
    def __init__(self, resp):
        self._resp = resp

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None, headers=None):
        assert headers and "X-eBirdApiToken" in headers
        if isinstance(self._resp, Exception):
            raise self._resp
        return self._resp


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("EBIRD_API_KEY", "test-key")
    ebird._cache.clear()
    yield
    get_settings.cache_clear()


def _patch(monkeypatch, resp):
    monkeypatch.setattr(httpx, "Client", lambda *a, **k: _Client(resp))


def test_success_returns_normalized(monkeypatch):
    payload = [{
        "speciesCode": "amecro", "comName": "American Crow",
        "sciName": "Corvus brachyrhynchos", "locName": "Park",
        "obsDt": "2026-10-20 08:00", "howMany": 3, "lat": 40.0, "lng": -75.0,
        "obsValid": True, "obsReviewed": False, "locationPrivate": True,
        "subId": "S123",
    }]
    _patch(monkeypatch, _Resp(200, payload))
    out = ebird.nearby_observations(40.0, -75.0)
    assert len(out) == 1
    assert out[0]["common_name"] == "American Crow"
    assert out[0]["source"] == "eBird"


def test_empty_is_not_error(monkeypatch):
    _patch(monkeypatch, _Resp(200, []))
    assert ebird.nearby_observations(40.0, -75.0) == []


def test_upstream_403_raises(monkeypatch):
    _patch(monkeypatch, _Resp(403, {}))
    with pytest.raises(ebird.EbirdError):
        ebird.nearby_observations(40.0, -75.0)


def test_transport_error_raises(monkeypatch):
    _patch(monkeypatch, httpx.ConnectError("boom"))
    with pytest.raises(ebird.EbirdError):
        ebird.nearby_observations(40.0, -75.0)


def test_invalid_coords_raise(monkeypatch):
    _patch(monkeypatch, _Resp(200, []))
    with pytest.raises(ebird.EbirdError):
        ebird.nearby_observations(999.0, -75.0)


def test_params_are_clamped(monkeypatch):
    captured = {}

    class _Capture(_Client):
        def get(self, url, params=None, headers=None):
            captured.update(params)
            return _Resp(200, [])

    monkeypatch.setattr(httpx, "Client", lambda *a, **k: _Capture(None))
    ebird.nearby_observations(40.0, -75.0, dist_km=999, back_days=999, max_results=99999)
    assert captured["dist"] == ebird.MAX_DIST_KM
    assert captured["back"] == ebird.MAX_BACK_DAYS
    assert captured["maxResults"] == 200


# --- location integrity (P3 regression) ---------------------------------- #
def test_request_uses_supplied_coordinates(monkeypatch):
    """The exact coordinates in the call must reach eBird — no substitution."""
    captured = {}

    class _Capture(_Client):
        def get(self, url, params=None, headers=None):
            captured["url"] = url
            captured.update(params)
            return _Resp(200, [])

    monkeypatch.setattr(httpx, "Client", lambda *a, **k: _Capture(None))
    ebird.nearby_observations(42.3601, -71.0589)
    assert captured["lat"] == "42.3601"
    assert captured["lng"] == "-71.0589"


def test_distant_coords_use_distinct_cache_keys(monkeypatch):
    seen = []

    class _Capture(_Client):
        def get(self, url, params=None, headers=None):
            seen.append((params["lat"], params["lng"]))
            return _Resp(200, [])

    monkeypatch.setattr(httpx, "Client", lambda *a, **k: _Capture(None))
    ebird.nearby_observations(42.3601, -71.0589)   # Boston
    ebird.nearby_observations(23.0225, 72.5714)    # Ahmedabad
    # Two distinct locations => two upstream calls, not a stale cache hit.
    assert len(seen) == 2
    assert seen[0] != seen[1]


# --- species-specific filtering (P4 regression) --------------------------- #
def test_species_recent_filters_by_species_code(monkeypatch):
    payload = [
        {"speciesCode": "blujay", "comName": "Blue Jay", "lat": 42.0, "lng": -71.0,
         "locId": "L1", "obsDt": "2026-10-20"},
        {"speciesCode": "amecro", "comName": "American Crow", "lat": 42.1,
         "lng": -71.1, "locId": "L2", "obsDt": "2026-10-20"},  # wrong species
    ]
    _patch(monkeypatch, _Resp(200, payload))
    out = ebird.species_recent_nearby("blujay", 42.3601, -71.0589)
    assert len(out) == 1
    assert out[0]["species_code"] == "blujay"


def test_species_recent_sorted_by_distance(monkeypatch):
    payload = [
        {"speciesCode": "blujay", "lat": 43.0, "lng": -71.0, "locId": "far",
         "obsDt": "x"},
        {"speciesCode": "blujay", "lat": 42.37, "lng": -71.06, "locId": "near",
         "obsDt": "y"},
    ]
    _patch(monkeypatch, _Resp(200, payload))
    out = ebird.species_recent_nearby("blujay", 42.3601, -71.0589)
    assert out[0]["location_id"] == "near"
    assert out[0]["distance_km"] <= out[1]["distance_km"]


def test_resolve_species_code_uses_scientific_name(monkeypatch):
    monkeypatch.setattr(ebird, "_load_taxonomy",
                        lambda: {"phoebastria nigripes": "bkfalb"})
    assert ebird.resolve_species_code("Phoebastria nigripes") == "bkfalb"
    assert ebird.resolve_species_code(None) is None
    assert ebird.resolve_species_code("Not A Bird") is None


def test_haversine_known_distance():
    # Boston to NYC is ~306 km.
    d = ebird.haversine_km(42.3601, -71.0589, 40.7128, -74.0060)
    assert 290 < d < 320
