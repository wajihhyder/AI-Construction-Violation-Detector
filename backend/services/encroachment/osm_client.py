"""
OpenStreetMap Overpass API client for building / road footprints.

We use the public Overpass instance with a short timeout. If the call fails or
returns no usable polygons, callers fall back to a Manual_Review verdict —
encroachment must never be claimed without geometry to back it up.
"""

from __future__ import annotations

import logging
import math
from typing import Any

import httpx
from shapely.geometry import LineString, Polygon

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT_S = 12.0
DEFAULT_SEARCH_RADIUS_M = 60.0


def _bbox_around(lat: float, lng: float, radius_m: float) -> tuple[float, float, float, float]:
    """Return (south, west, north, east) padded by radius_m around (lat, lng)."""
    lat_delta = radius_m / 111_320.0
    lng_delta = radius_m / (111_320.0 * max(math.cos(math.radians(lat)), 1e-6))
    return (lat - lat_delta, lng - lng_delta, lat + lat_delta, lng + lng_delta)


def _ways_to_geometry(elements: list[dict[str, Any]]) -> dict[str, list]:
    """
    Split Overpass `out geom` ways into building polygons and road lines.

    We only consume closed `building` ways and `highway` ways here — that's enough
    to compute encroachment of a building footprint onto the road right-of-way.
    """
    buildings: list[Polygon] = []
    roads: list[LineString] = []
    for el in elements:
        if el.get("type") != "way":
            continue
        geom = el.get("geometry") or []
        if len(geom) < 2:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in geom if "lon" in pt and "lat" in pt]
        if len(coords) < 2:
            continue
        tags = el.get("tags") or {}
        if "building" in tags and len(coords) >= 4 and coords[0] == coords[-1]:
            try:
                poly = Polygon(coords)
                if poly.is_valid and poly.area > 0:
                    buildings.append(poly)
            except (ValueError, TypeError) as e:
                logger.debug("Skip invalid building way %s: %s", el.get("id"), e)
        elif "highway" in tags:
            try:
                roads.append(LineString(coords))
            except (ValueError, TypeError) as e:
                logger.debug("Skip invalid highway way %s: %s", el.get("id"), e)
    return {"buildings": buildings, "roads": roads}


async def fetch_nearby_features(
    lat: float,
    lng: float,
    radius_m: float = DEFAULT_SEARCH_RADIUS_M,
) -> dict[str, list]:
    """
    Pull buildings and roads near (lat, lng) from OSM Overpass.

    Returns {"buildings": [Polygon, ...], "roads": [LineString, ...]} on success.
    Raises httpx.HTTPError / RuntimeError on transport / parse failures so the
    caller can route the report to manual review.
    """
    south, west, north, east = _bbox_around(lat, lng, radius_m)
    query = f"""
    [out:json][timeout:{int(OVERPASS_TIMEOUT_S)}];
    (
      way["building"]({south},{west},{north},{east});
      way["highway"]({south},{west},{north},{east});
    );
    out geom;
    """
    async with httpx.AsyncClient(timeout=OVERPASS_TIMEOUT_S) as client:
        response = await client.post(OVERPASS_URL, data={"data": query})
        response.raise_for_status()
        payload = response.json()
    elements = payload.get("elements") or []
    return _ways_to_geometry(elements)
