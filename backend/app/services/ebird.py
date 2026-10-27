"""eBird observation service.

Wraps the official eBird API 2.0. The API token is read from the server
environment and never leaves the backend.

Reference: https://documenter.getpostman.com/view/664302/S1ENwy59
  GET /data/obs/geo/recent                recent nearby observations (all species)
  GET /data/obs/geo/recent/{speciesCode}  recent nearby observations of one species
  GET /ref/hotspot/geo                     nearby birding hotspots
  GET /ref/taxonomy/ebird                  full eBird/Clements taxonomy

Auth header: X-eBirdApiToken: <key>

This module never fabricates observations. An upstream/transport failure raises
``EbirdError`` (surfaced as "data unavailable"); a successful call that returns
an empty list is a genuine "no observations" result — the two are kept strictly
distinct. Species codes are resolved from the *verified scientific name* against
the official eBird taxonomy, never by string-munging a common name.
"""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass

import httpx

from app.config import get_settings

BASE_URL = "https://api.ebird.org/v2"
RECENT_NEARBY = "/data/obs/geo/recent"
RECENT_NEARBY_SPECIES = "/data/obs/geo/recent/{code}"
HOTSPOTS_NEARBY = "/ref/hotspot/geo"
TAXONOMY = "/ref/taxonomy/ebird"

MAX_DIST_KM = 50
MAX_BACK_DAYS = 30


class EbirdError(RuntimeError):
    """Upstream eBird error or misconfiguration (distinct from empty results)."""


# --------------------------------------------------------------------------- #
# Generic response cache (per fully-qualified query)
# --------------------------------------------------------------------------- #
@dataclass
class _CacheEntry:
    expires: float
    value: object


_cache: dict[tuple, _CacheEntry] = {}
_CACHE_TTL_S = 120.0
_cache_lock = threading.Lock()


def _cache_get(key: tuple):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and hit.expires > now:
            return hit.value
    return None


def _cache_put(key: tuple, value, ttl: float = _CACHE_TTL_S):
    with _cache_lock:
        _cache[key] = _CacheEntry(expires=time.time() + ttl, value=value)


# --------------------------------------------------------------------------- #
# Low-level request helper
# --------------------------------------------------------------------------- #
def _get(path: str, params: dict):
    settings = get_settings()
    if not settings.ebird_api_key:
        raise EbirdError("eBird API key not configured")
    headers = {"X-eBirdApiToken": settings.ebird_api_key}
    try:
        with httpx.Client(timeout=settings.ebird_timeout_s) as client:
            resp = client.get(BASE_URL + path, params=params, headers=headers)
    except httpx.HTTPError as exc:
        raise EbirdError(f"eBird request failed: {exc}") from exc
    if resp.status_code == 403:
        raise EbirdError("eBird rejected the API key (403)")
    if resp.status_code >= 400:
        raise EbirdError(f"eBird upstream error ({resp.status_code})")
    try:
        return resp.json()
    except ValueError as exc:
        raise EbirdError("eBird returned a non-JSON response") from exc


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two points."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 2)


def _validate(lat: float, lng: float, dist: int, back: int, max_results: int):
    if not (-90.0 <= lat <= 90.0):
        raise EbirdError("latitude out of range (-90..90)")
    if not (-180.0 <= lng <= 180.0):
        raise EbirdError("longitude out of range (-180..180)")
    return (
        lat,
        lng,
        max(1, min(int(dist), MAX_DIST_KM)),
        max(1, min(int(back), MAX_BACK_DAYS)),
        max(1, min(int(max_results), 200)),
    )


def _maps_url(lat, lng) -> str | None:
    if lat is None or lng is None:
        return None
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"


# --------------------------------------------------------------------------- #
# Taxonomy: resolve a verified scientific name -> eBird species code
# --------------------------------------------------------------------------- #
_taxonomy_map: dict[str, str] | None = None
_taxonomy_lock = threading.Lock()
_TAXONOMY_TTL_S = 24 * 3600
_taxonomy_loaded_at = 0.0


def _load_taxonomy() -> dict[str, str]:
    global _taxonomy_map, _taxonomy_loaded_at
    now = time.time()
    if _taxonomy_map is not None and (now - _taxonomy_loaded_at) < _TAXONOMY_TTL_S:
        return _taxonomy_map
    with _taxonomy_lock:
        if _taxonomy_map is not None and (now - _taxonomy_loaded_at) < _TAXONOMY_TTL_S:
            return _taxonomy_map
        data = _get(TAXONOMY, {"fmt": "json", "cat": "species"})
        mapping: dict[str, str] = {}
        for entry in data:
            sci = (entry.get("sciName") or "").strip().lower()
            code = entry.get("speciesCode")
            if sci and code:
                mapping[sci] = code
        if not mapping:
            raise EbirdError("eBird taxonomy returned no usable entries")
        _taxonomy_map = mapping
        _taxonomy_loaded_at = time.time()
        return mapping


def resolve_species_code(scientific_name: str | None) -> str | None:
    """Return the eBird species code for a verified scientific name, or None.

    Never guesses from a common name. Returns None when the name is missing or
    not present in the official taxonomy.
    """
    if not scientific_name:
        return None
    try:
        return _load_taxonomy().get(scientific_name.strip().lower())
    except EbirdError:
        raise


# --------------------------------------------------------------------------- #
# Observations
# --------------------------------------------------------------------------- #
def _normalize(o: dict, center: tuple[float, float] | None = None) -> dict:
    lat, lng = o.get("lat"), o.get("lng")
    distance = (
        haversine_km(center[0], center[1], lat, lng)
        if center and lat is not None and lng is not None
        else None
    )
    return {
        "species_code": o.get("speciesCode"),
        "common_name": o.get("comName"),
        "scientific_name": o.get("sciName"),
        "location_name": o.get("locName"),
        "location_id": o.get("locId"),
        "observed_at": o.get("obsDt"),
        "count": o.get("howMany"),
        "latitude": lat,
        "longitude": lng,
        "distance_km": distance,
        "observation_valid": o.get("obsValid"),
        "observation_reviewed": o.get("obsReviewed"),
        "location_private": o.get("locationPrivate"),
        "checklist_id": o.get("subId"),
        "map_url": _maps_url(lat, lng),
        "source": "eBird",
        "source_url": "https://ebird.org",
    }


def nearby_observations(
    lat: float, lng: float, dist_km: int = 25, back_days: int = 14,
    max_results: int = 50,
) -> list[dict]:
    """Recent observations of ALL species near a point (generic feed)."""
    lat, lng, dist_km, back_days, max_results = _validate(
        lat, lng, dist_km, back_days, max_results
    )
    key = ("nearby", round(lat, 4), round(lng, 4), dist_km, back_days, max_results)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    raw = _get(RECENT_NEARBY, {
        "lat": f"{lat:.4f}", "lng": f"{lng:.4f}", "dist": dist_km,
        "back": back_days, "maxResults": max_results,
    })
    obs = [_normalize(o, (lat, lng)) for o in raw if isinstance(o, dict)]
    obs.sort(key=lambda o: (o["distance_km"] is None, o["distance_km"] or 0))
    _cache_put(key, obs)
    return obs


def species_recent_nearby(
    species_code: str, lat: float, lng: float, dist_km: int = 25,
    back_days: int = 14, max_results: int = 100,
) -> list[dict]:
    """Recent observations of ONE species near a point, sorted by distance.

    Defensively filters the response by the requested species code.
    """
    lat, lng, dist_km, back_days, max_results = _validate(
        lat, lng, dist_km, back_days, max_results
    )
    key = ("species", species_code, round(lat, 4), round(lng, 4), dist_km,
           back_days, max_results)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    raw = _get(RECENT_NEARBY_SPECIES.format(code=species_code), {
        "lat": f"{lat:.4f}", "lng": f"{lng:.4f}", "dist": dist_km,
        "back": back_days, "maxResults": max_results,
    })
    obs = [
        _normalize(o, (lat, lng))
        for o in raw
        if isinstance(o, dict) and o.get("speciesCode") == species_code
    ]
    obs.sort(key=lambda o: (o["distance_km"] is None, o["distance_km"] or 0))
    _cache_put(key, obs)
    return obs


def nearby_hotspots(
    lat: float, lng: float, dist_km: int = 25, species_loc_ids: set | None = None,
) -> list[dict]:
    """Nearby birding hotspots, sorted by distance.

    If ``species_loc_ids`` is given (location ids where the target species was
    recently reported), each hotspot is flagged ``has_recent_species``.
    """
    lat, lng, dist_km, _, _ = _validate(lat, lng, dist_km, 1, 1)
    key = ("hotspots", round(lat, 4), round(lng, 4), dist_km)
    cached = _cache_get(key)
    hotspots = cached
    if hotspots is None:
        raw = _get(HOTSPOTS_NEARBY, {
            "lat": f"{lat:.4f}", "lng": f"{lng:.4f}", "dist": dist_km, "fmt": "json",
        })
        hotspots = []
        for h in raw if isinstance(raw, list) else []:
            hlat, hlng = h.get("lat"), h.get("lng")
            hotspots.append({
                "location_id": h.get("locId"),
                "name": h.get("locName"),
                "latitude": hlat,
                "longitude": hlng,
                "num_species_all_time": h.get("numSpeciesAllTime"),
                "latest_obs_dt": h.get("latestObsDt"),
                "distance_km": haversine_km(lat, lng, hlat, hlng)
                if hlat is not None and hlng is not None else None,
                "map_url": _maps_url(hlat, hlng),
                "source": "eBird",
            })
        hotspots.sort(key=lambda h: (h["distance_km"] is None, h["distance_km"] or 0))
        _cache_put(key, hotspots)
    # Flag (non-mutating copy) which hotspots recently reported the species.
    ids = species_loc_ids or set()
    return [{**h, "has_recent_species": h["location_id"] in ids} for h in hotspots]
