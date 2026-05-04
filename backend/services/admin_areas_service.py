"""
GPS → Karachi district + town using packaged bounding boxes (see data/karachi_town_bboxes.json).

Boxes are indicative; for production replace with official TMC polygon GeoJSON and use the same
lookup API (extend `_hit_from_geojson` when you add real geometries).
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from shapely.geometry import Point, box

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_BBOX_FILE = _DATA_DIR / "karachi_town_bboxes.json"


def _area_deg2(entry: dict[str, Any]) -> float:
    return (entry["max_lat"] - entry["min_lat"]) * (entry["max_lng"] - entry["min_lng"])


@lru_cache
def _load_bbox_config() -> dict[str, Any]:
    if not _BBOX_FILE.is_file():
        logger.warning("Karachi bbox file missing: %s", _BBOX_FILE)
        return {"meta": {}, "areas": []}
    with open(_BBOX_FILE, encoding="utf-8") as f:
        return json.load(f)


def _inside_karachi_bounds(lat: float, lng: float, meta: dict[str, Any]) -> bool:
    kb = (meta or {}).get("karachi_bounds") or {}
    if not kb:
        return True
    return (
        kb.get("min_lat", -90) <= lat <= kb.get("max_lat", 90)
        and kb.get("min_lng", -180) <= lng <= kb.get("max_lng", 180)
    )


def lookup_karachi_admin(lat: float, lng: float) -> dict[str, Any]:
    """
    Return { district, town, label, source, inside_karachi_bounds }.
    On miss: district/town/label are None, source is 'none'.
    """
    cfg = _load_bbox_config()
    meta = cfg.get("meta") or {}
    areas: list[dict[str, Any]] = cfg.get("areas") or []

    inside = _inside_karachi_bounds(lat, lng, meta)
    p = Point(lng, lat)
    candidates: list[dict[str, Any]] = []
    for a in areas:
        try:
            b = box(a["min_lng"], a["min_lat"], a["max_lng"], a["max_lat"])
        except (KeyError, TypeError, ValueError):
            continue
        if b.covers(p):
            candidates.append(a)

    if not candidates:
        return {
            "district": None,
            "town": None,
            "label": None,
            "source": "none",
            "inside_karachi_bounds": inside,
        }

    # Smallest box wins (most specific); tie-break by higher priority.
    def sort_key(a: dict[str, Any]) -> tuple[float, int]:
        ar = _area_deg2(a)
        pri = int(a.get("priority") or 0)
        return (ar, -pri)

    best = min(candidates, key=sort_key)
    district = str(best["district"])
    town = str(best["town"])
    label = f"{town} ({district})"
    return {
        "district": district,
        "town": town,
        "label": label,
        "source": "karachi_admin",
        "inside_karachi_bounds": inside,
    }
