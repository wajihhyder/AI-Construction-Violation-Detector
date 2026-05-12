"""
Aerial encroachment analysis.

Given an aerial image plus its GPS coords and the district where it was submitted,
we compare the building closest to the GPS pin against OSM road footprints and
the SBCA minimum-setback rule for that district. The output uses the existing
AIAnalysisResult schema: `violation_type` is set to "Encroachment" when a
building extends onto / under the required setback strip, with the deficit
recorded in `setback_error` (meters).

We annotate the aerial image with the offending building outline and the
encroachment buffer to give SBCA staff visual evidence.
"""

from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import httpx
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points

from core.config import settings
from services.encroachment.osm_client import (
    DEFAULT_SEARCH_RADIUS_M,
    fetch_nearby_features,
)
from services.rule_engine import get_district_rules

logger = logging.getLogger(__name__)

EARTH_RADIUS_M = 6_371_000.0
EVIDENCE_CANVAS_PX = 720
MIN_BUILDING_OVERLAP_M = 0.10  # below this we treat as measurement noise


@dataclass(frozen=True)
class EncroachmentResult:
    violation_flag: bool
    violation_type: str | None
    setback_error: float | None
    image_evidence_path: str
    notes: str
    workflow_status: str | None = None


def _meters_per_degree(lat: float) -> tuple[float, float]:
    """Return (meters per deg lat, meters per deg lng) at the given latitude."""
    lat_rad = math.radians(lat)
    m_per_deg_lat = 111_132.92 - 559.82 * math.cos(2 * lat_rad)
    m_per_deg_lng = 111_412.84 * math.cos(lat_rad)
    return m_per_deg_lat, max(m_per_deg_lng, 1e-6)


def _project_to_meters(
    geom: BaseGeometry,
    origin_lat: float,
    origin_lng: float,
) -> BaseGeometry:
    """Flat-earth project lon/lat geometry to local meters centred on origin."""
    m_lat, m_lng = _meters_per_degree(origin_lat)

    def _xy(x: float, y: float) -> tuple[float, float]:
        return ((x - origin_lng) * m_lng, (y - origin_lat) * m_lat)

    if isinstance(geom, Polygon):
        exterior = [_xy(x, y) for x, y in geom.exterior.coords]
        return Polygon(exterior)
    if isinstance(geom, LineString):
        return LineString([_xy(x, y) for x, y in geom.coords])
    if isinstance(geom, Point):
        return Point(_xy(geom.x, geom.y))
    raise TypeError(f"Unsupported geometry: {type(geom).__name__}")


def _pick_target_building(
    buildings: list[Polygon],
    origin_lat: float,
    origin_lng: float,
) -> tuple[Polygon, Polygon] | None:
    """
    Return (lonlat_polygon, projected_meters_polygon) for the building whose
    footprint sits closest to the GPS pin, or None if none can be projected.
    """
    pin = Point(0.0, 0.0)
    best: tuple[float, Polygon, Polygon] | None = None
    for b in buildings:
        projected = _project_to_meters(b, origin_lat, origin_lng)
        if not isinstance(projected, Polygon):
            continue
        distance = projected.distance(pin)
        if best is None or distance < best[0]:
            best = (distance, b, projected)
    return (best[1], best[2]) if best else None


def _measure_encroachment(
    building_m: Polygon,
    roads_m: list[LineString],
    required_setback_m: float,
) -> float:
    """
    Return the maximum encroachment depth (meters) of `building_m` into the
    required setback strip alongside any nearby road. 0.0 means no breach.
    """
    if not roads_m or required_setback_m <= 0:
        return 0.0
    worst = 0.0
    for road in roads_m:
        try:
            buffer_poly = road.buffer(required_setback_m, cap_style=2)
        except (ValueError, TypeError):
            continue
        if not buffer_poly.intersects(building_m):
            continue
        overlap = buffer_poly.intersection(building_m)
        if overlap.is_empty:
            continue
        nearest_road_pt, nearest_building_pt = nearest_points(road, building_m)
        gap = nearest_road_pt.distance(nearest_building_pt)
        deficit = max(required_setback_m - gap, 0.0)
        if deficit > worst:
            worst = deficit
    return worst


def _annotate_aerial(
    image_path: str,
    building_lonlat: Polygon | None,
    roads_lonlat: list[LineString],
    origin_lat: float,
    origin_lng: float,
    required_setback_m: float,
) -> str:
    """Render the OSM polygons / setback buffer onto the aerial image."""
    try:
        with Image.open(image_path) as img:
            base = img.convert("RGB").copy()
    except (FileNotFoundError, OSError) as e:
        logger.warning("Cannot open aerial image %s for annotation: %s", image_path, e)
        return image_path

    canvas_w, canvas_h = base.size
    if min(canvas_w, canvas_h) > EVIDENCE_CANVAS_PX:
        scale = EVIDENCE_CANVAS_PX / float(min(canvas_w, canvas_h))
        canvas_w = int(canvas_w * scale)
        canvas_h = int(canvas_h * scale)
        base = base.resize((canvas_w, canvas_h))

    geoms_m: list[BaseGeometry] = []
    if building_lonlat is not None:
        geoms_m.append(_project_to_meters(building_lonlat, origin_lat, origin_lng))
    geoms_m.extend(_project_to_meters(r, origin_lat, origin_lng) for r in roads_lonlat)
    if not geoms_m:
        return image_path

    extent = max((g.bounds[2] - g.bounds[0] for g in geoms_m), default=0.0)
    extent = max(extent, max((g.bounds[3] - g.bounds[1] for g in geoms_m), default=0.0))
    extent = max(extent, 4 * max(required_setback_m, 1.0))
    half = extent / 2.0 + max(required_setback_m, 1.0)
    px_per_m = min(canvas_w, canvas_h) / (2 * half)

    def _to_px(x: float, y: float) -> tuple[float, float]:
        return (canvas_w / 2 + x * px_per_m, canvas_h / 2 - y * px_per_m)

    overlay = base.copy()
    draw = ImageDraw.Draw(overlay, "RGBA")
    for road in roads_lonlat:
        line_m = _project_to_meters(road, origin_lat, origin_lng)
        if not isinstance(line_m, LineString):
            continue
        pts = [_to_px(x, y) for x, y in line_m.coords]
        if len(pts) >= 2:
            draw.line(pts, fill=(80, 200, 255, 255), width=3)
        if required_setback_m > 0:
            buffer_poly = line_m.buffer(required_setback_m, cap_style=2)
            if isinstance(buffer_poly, Polygon) and not buffer_poly.is_empty:
                ring = [_to_px(x, y) for x, y in buffer_poly.exterior.coords]
                if len(ring) >= 3:
                    draw.polygon(ring, fill=(255, 200, 80, 60), outline=(255, 200, 80, 200))

    if building_lonlat is not None:
        building_m = _project_to_meters(building_lonlat, origin_lat, origin_lng)
        if isinstance(building_m, Polygon):
            ring = [_to_px(x, y) for x, y in building_m.exterior.coords]
            if len(ring) >= 3:
                draw.polygon(ring, fill=(255, 80, 80, 90), outline=(255, 80, 80, 255))

    pin = _to_px(0.0, 0.0)
    r = 6
    draw.ellipse((pin[0] - r, pin[1] - r, pin[0] + r, pin[1] + r), fill=(255, 255, 255, 255))

    out_dir = Path(settings.UPLOAD_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = f"encroachment_{uuid4().hex}.jpg"
    out_path = out_dir / out_name
    overlay.save(out_path, format="JPEG", quality=92)
    return f"/uploads/{out_name}"


def _manual_review(image_path: str, message: str) -> EncroachmentResult:
    return EncroachmentResult(
        violation_flag=False,
        violation_type="Manual_Review",
        setback_error=None,
        image_evidence_path=image_path,
        notes=message,
        workflow_status="Under_Review",
    )


def _parse_gps_string(gps: str | None) -> tuple[float, float] | None:
    if not gps:
        return None
    try:
        lat_str, lng_str = gps.split(",", 1)
        lat = float(lat_str.strip())
        lng = float(lng_str.strip())
    except (ValueError, AttributeError):
        return None
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        return None
    return lat, lng


async def analyze_aerial_encroachment(
    image_path: str,
    district: str,
    gps_coords: str | None,
) -> EncroachmentResult:
    """
    Public entry point used by ai_service.process_aerial_image.

    Requires GPS coords to fetch OSM context; reports without coords are routed
    to manual review.
    """
    coords = _parse_gps_string(gps_coords)
    if coords is None:
        return _manual_review(
            image_path,
            "Aerial submission missing GPS coordinates — routed to manual setback / encroachment review.",
        )

    lat, lng = coords
    rules = get_district_rules(district)
    required_setback_m = float(rules.get("min_setback_m", 0.0) or 0.0)

    try:
        features = await fetch_nearby_features(lat, lng, radius_m=DEFAULT_SEARCH_RADIUS_M)
    except (httpx.HTTPError, ValueError, RuntimeError) as e:
        logger.warning("Overpass fetch failed for (%s, %s): %s", lat, lng, e)
        return _manual_review(
            image_path,
            "OpenStreetMap context unavailable — aerial report routed to manual encroachment review.",
        )

    buildings = features.get("buildings") or []
    roads = features.get("roads") or []
    if not buildings:
        return _manual_review(
            image_path,
            "No OSM building footprint near submission GPS — manual encroachment review required.",
        )

    picked = _pick_target_building(buildings, lat, lng)
    if picked is None:
        return _manual_review(
            image_path,
            "Could not project nearby OSM buildings — manual encroachment review required.",
        )
    target_lonlat, target_m = picked

    roads_m = [
        line for line in (_project_to_meters(r, lat, lng) for r in roads)
        if isinstance(line, LineString)
    ]

    deficit = _measure_encroachment(target_m, roads_m, required_setback_m)
    evidence_path = _annotate_aerial(
        image_path,
        target_lonlat,
        roads,
        lat,
        lng,
        required_setback_m,
    )

    if deficit > MIN_BUILDING_OVERLAP_M:
        rounded = round(deficit, 2)
        return EncroachmentResult(
            violation_flag=True,
            violation_type="Encroachment",
            setback_error=rounded,
            image_evidence_path=evidence_path,
            notes=(
                f"Building footprint extends {rounded}m into the required "
                f"{required_setback_m:.1f}m setback from the nearest road in {district}."
            ),
        )

    return EncroachmentResult(
        violation_flag=False,
        violation_type=None,
        setback_error=0.0,
        image_evidence_path=evidence_path,
        notes=(
            f"Aerial review found no encroachment past the {required_setback_m:.1f}m "
            f"setback for {district}."
        ),
    )


def analyze_aerial_encroachment_sync(
    image_path: str,
    district: str,
    gps_coords: str | None,
) -> EncroachmentResult:
    """Synchronous helper for callers outside async contexts (tests, scripts)."""
    return asyncio.run(analyze_aerial_encroachment(image_path, district, gps_coords))
