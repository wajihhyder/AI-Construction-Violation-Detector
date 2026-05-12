"""
Aerial encroachment screening pipeline.

1. YOLO building segmenter (Roboflow encroachment dataset) finds candidate
   building footprints in the submitted aerial image (pixel space).
2. OpenStreetMap context (roads, public-space, water, mapped buildings) is
   pulled for the lat/lng around the submission.
3. The OSM features are projected to the same pixel grid using a configurable
   real-world span (AI_ENCROACHMENT_IMAGE_SPAN_M).
4. Each detected building footprint is sliced into per-category geometries:
   road / public-space / water / unmapped / compliant. Areas are accumulated
   in m² and a color-coded overlay JPEG is written next to the original
   upload — matching the screenshot the SBCA team designed.

Anywhere the pipeline cannot run with confidence (model missing, no GPS,
Overpass unreachable) the aerial report is routed to manual review without
fabricating numbers.
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

import httpx
from PIL import Image, ImageDraw, ImageFont
from shapely.affinity import scale, translate
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

from core.config import settings
from services.encroachment.osm_client import OSMContext, fetch_osm_context
from services.encroachment.segmenter import detect_building_polygons

logger = logging.getLogger(__name__)


ENCROACHMENT_CATEGORIES: tuple[str, ...] = (
    "road",
    "public_space",
    "water",
    "unmapped",
    "compliant",
)

VIOLATION_TYPE_BY_CATEGORY = {
    "road": "Road_Encroachment",
    "public_space": "Public_Space_Encroachment",
    "water": "Water_Encroachment",
    "unmapped": "Unmapped_Construction",
}

CATEGORY_COLORS = {
    "road": (255, 60, 95, 165),         # pink/red
    "public_space": (200, 80, 220, 150),  # magenta
    "water": (80, 170, 255, 150),       # blue
    "unmapped": (255, 175, 70, 150),    # amber
    "compliant": (70, 200, 120, 150),   # green
}
CATEGORY_LABELS = {
    "road": "Road encroachment",
    "public_space": "Public-space encroachment",
    "water": "Water encroachment",
    "unmapped": "Unmapped construction",
    "compliant": "Compliant footprint",
}

MIN_FRAGMENT_AREA_PX = 8.0
LEGEND_PAD_PX = 14
SWATCH_PX = 14


@dataclass(frozen=True)
class EncroachmentResult:
    violation_flag: bool
    violation_type: str | None
    total_area_m2: float
    breakdown_m2: dict[str, float]
    image_evidence_path: str
    notes: str
    workflow_status: str | None = None

    def breakdown_json(self) -> str:
        return json.dumps(self.breakdown_m2, separators=(",", ":"))


def _manual_review(image_path: str, message: str) -> EncroachmentResult:
    return EncroachmentResult(
        violation_flag=False,
        violation_type="Manual_Review",
        total_area_m2=0.0,
        breakdown_m2={c: 0.0 for c in ENCROACHMENT_CATEGORIES},
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


def _meters_per_degree(lat: float) -> tuple[float, float]:
    lat_rad = math.radians(lat)
    m_per_deg_lat = 111_132.92 - 559.82 * math.cos(2 * lat_rad)
    m_per_deg_lng = 111_412.84 * math.cos(lat_rad)
    return m_per_deg_lat, max(m_per_deg_lng, 1e-6)


@dataclass
class _PixelProjector:
    width_px: int
    height_px: int
    px_per_m: float
    origin_lat: float
    origin_lng: float
    m_per_deg_lat: float
    m_per_deg_lng: float

    def project(self, geom: BaseGeometry) -> BaseGeometry:
        """lon/lat → meters (centred on origin) → image pixels (origin top-left)."""
        translated = translate(geom, xoff=-self.origin_lng, yoff=-self.origin_lat)
        meters = scale(
            translated,
            xfact=self.m_per_deg_lng,
            yfact=self.m_per_deg_lat,
            origin=(0, 0),
        )
        # Pixel y axis points down; image y in meters points up → flip with negative scale.
        pixels = scale(meters, xfact=self.px_per_m, yfact=-self.px_per_m, origin=(0, 0))
        return translate(pixels, xoff=self.width_px / 2, yoff=self.height_px / 2)


@dataclass
class _SlicedBuilding:
    raw_area_px: float
    per_category_px: dict[str, float] = field(default_factory=dict)


def _polygon_iter(geom: BaseGeometry) -> list[Polygon]:
    if isinstance(geom, Polygon):
        return [geom] if not geom.is_empty else []
    if isinstance(geom, MultiPolygon):
        return [p for p in geom.geoms if not p.is_empty]
    return []


def _safe_intersection(a: BaseGeometry, b: BaseGeometry) -> BaseGeometry | None:
    try:
        return a.intersection(b)
    except Exception as e:  # shapely TopologyException etc.
        logger.debug("Intersection failed: %s", e)
        return None


def _safe_difference(a: BaseGeometry, b: BaseGeometry) -> BaseGeometry | None:
    try:
        return a.difference(b)
    except Exception as e:
        logger.debug("Difference failed: %s", e)
        return None


def _build_road_buffer(
    roads_px: list[LineString],
    half_width_px: float,
) -> BaseGeometry | None:
    if not roads_px or half_width_px <= 0:
        return None
    buffers = []
    for road in roads_px:
        try:
            buf = road.buffer(half_width_px, cap_style=2, join_style=2)
            if not buf.is_empty:
                buffers.append(buf)
        except Exception as e:
            logger.debug("Road buffer failed: %s", e)
    if not buffers:
        return None
    try:
        from shapely.ops import unary_union
        return unary_union(buffers)
    except Exception as e:
        logger.debug("Road buffer union failed: %s", e)
        return buffers[0]


def _build_union(polys: list[Polygon]) -> BaseGeometry | None:
    if not polys:
        return None
    try:
        from shapely.ops import unary_union
        return unary_union(polys)
    except Exception as e:
        logger.debug("Polygon union failed: %s", e)
        return polys[0]


def _classify_building(
    building_px: Polygon,
    layers_px: dict[str, BaseGeometry | None],
) -> dict[str, list[Polygon]]:
    """
    Returns {category: [polygon_fragments]} so we can both measure and draw.
    Categories are checked in priority order: road > public_space > water >
    compliant (mapped) > unmapped (leftover).
    """
    categories: dict[str, list[Polygon]] = {c: [] for c in ENCROACHMENT_CATEGORIES}
    remaining: BaseGeometry = building_px
    if not isinstance(remaining, Polygon) or remaining.is_empty:
        return categories

    for cat in ("road", "public_space", "water", "compliant"):
        layer = layers_px.get(cat)
        if layer is None or remaining.is_empty:
            continue
        hit = _safe_intersection(remaining, layer)
        if hit is None or hit.is_empty:
            continue
        for piece in _polygon_iter(hit):
            if piece.area >= MIN_FRAGMENT_AREA_PX:
                categories[cat].append(piece)
        leftover = _safe_difference(remaining, layer)
        if leftover is None:
            break
        remaining = leftover

    if not remaining.is_empty:
        for piece in _polygon_iter(remaining):
            if piece.area >= MIN_FRAGMENT_AREA_PX:
                categories["unmapped"].append(piece)

    return categories


def _aggregate_breakdown(
    sliced: list[dict[str, list[Polygon]]],
    px_to_m2: float,
) -> dict[str, float]:
    totals = {c: 0.0 for c in ENCROACHMENT_CATEGORIES}
    for record in sliced:
        for cat, pieces in record.items():
            totals[cat] += sum(p.area for p in pieces) * px_to_m2
    return {c: round(v, 1) for c, v in totals.items()}


def _pick_violation_type(breakdown_m2: dict[str, float]) -> tuple[str | None, bool]:
    """Pick the highest-area encroachment category as the headline violation."""
    encroaching = {c: breakdown_m2.get(c, 0.0) for c in VIOLATION_TYPE_BY_CATEGORY}
    if not any(v > 0 for v in encroaching.values()):
        return None, False
    top_cat = max(encroaching, key=lambda c: encroaching[c])
    if encroaching[top_cat] <= 0:
        return None, False
    return VIOLATION_TYPE_BY_CATEGORY[top_cat], True


def _open_aerial(image_path: str) -> Image.Image | None:
    try:
        with Image.open(image_path) as img:
            return img.convert("RGB").copy()
    except (FileNotFoundError, OSError) as e:
        logger.warning("Cannot open aerial image %s: %s", image_path, e)
        return None


def _make_projector(
    image_size_px: tuple[int, int],
    lat: float,
    lng: float,
) -> _PixelProjector:
    width_px, height_px = image_size_px
    longer_px = max(width_px, height_px)
    px_per_m = longer_px / float(settings.AI_ENCROACHMENT_IMAGE_SPAN_M)
    m_per_deg_lat, m_per_deg_lng = _meters_per_degree(lat)
    return _PixelProjector(
        width_px=width_px,
        height_px=height_px,
        px_per_m=px_per_m,
        origin_lat=lat,
        origin_lng=lng,
        m_per_deg_lat=m_per_deg_lat,
        m_per_deg_lng=m_per_deg_lng,
    )


def _project_osm(
    context: OSMContext,
    projector: _PixelProjector,
) -> dict[str, BaseGeometry | None]:
    roads_px: list[LineString] = []
    for road in context.roads:
        projected = projector.project(road)
        if isinstance(projected, LineString) and not projected.is_empty:
            roads_px.append(projected)

    def _project_polys(polys: list[Polygon]) -> list[Polygon]:
        out: list[Polygon] = []
        for poly in polys:
            projected = projector.project(poly)
            for p in _polygon_iter(projected):
                if p.area >= MIN_FRAGMENT_AREA_PX:
                    out.append(p)
        return out

    public_px = _project_polys(context.public_space)
    water_px = _project_polys(context.water)
    buildings_px = _project_polys(context.buildings)

    half_width_px = settings.AI_ENCROACHMENT_ROAD_BUFFER_M * projector.px_per_m
    return {
        "road": _build_road_buffer(roads_px, half_width_px),
        "public_space": _build_union(public_px),
        "water": _build_union(water_px),
        "compliant": _build_union(buildings_px),
        "roads_lines": roads_px,
    }


def _render_polygon(
    draw: ImageDraw.ImageDraw,
    poly: Polygon,
    color: tuple[int, int, int, int],
) -> None:
    if poly.is_empty:
        return
    outline = (color[0], color[1], color[2], 230)
    coords = [(float(x), float(y)) for x, y in poly.exterior.coords]
    if len(coords) >= 3:
        draw.polygon(coords, fill=color, outline=outline)


def _draw_legend(
    draw: ImageDraw.ImageDraw,
    canvas_size: tuple[int, int],
    breakdown_m2: dict[str, float],
) -> None:
    width, _ = canvas_size
    line_h = SWATCH_PX + 6
    legend_w = 268
    legend_h = LEGEND_PAD_PX * 2 + line_h * len(ENCROACHMENT_CATEGORIES) + 22
    x0 = width - legend_w - 12
    y0 = 12
    draw.rectangle(
        (x0, y0, x0 + legend_w, y0 + legend_h),
        fill=(20, 20, 20, 220),
        outline=(255, 255, 255, 160),
    )
    try:
        font = ImageFont.load_default()
    except OSError:
        font = None
    draw.text((x0 + LEGEND_PAD_PX, y0 + 8), "Encroachment classification", fill=(245, 245, 245, 255), font=font)

    for i, cat in enumerate(ENCROACHMENT_CATEGORIES):
        sw_y = y0 + 28 + i * line_h
        color = CATEGORY_COLORS[cat]
        draw.rectangle(
            (x0 + LEGEND_PAD_PX, sw_y, x0 + LEGEND_PAD_PX + SWATCH_PX, sw_y + SWATCH_PX),
            fill=color,
            outline=(255, 255, 255, 220),
        )
        label = f"{CATEGORY_LABELS[cat]} ({breakdown_m2.get(cat, 0.0):.1f} m²)"
        draw.text(
            (x0 + LEGEND_PAD_PX + SWATCH_PX + 8, sw_y - 1),
            label,
            fill=(240, 240, 240, 255),
            font=font,
        )


def _render_overlay(
    base: Image.Image,
    osm_px: dict[str, BaseGeometry | None],
    sliced: list[dict[str, list[Polygon]]],
    breakdown_m2: dict[str, float],
) -> str:
    overlay = base.copy().convert("RGBA")
    canvas = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas, "RGBA")

    # OSM context: roads stroked, public-space / water tinted softly underneath.
    for cat in ("water", "public_space"):
        layer = osm_px.get(cat)
        if layer is None:
            continue
        tint = (*CATEGORY_COLORS[cat][:3], 50)
        for poly in _polygon_iter(layer):
            _render_polygon(draw, poly, tint)

    roads_lines = osm_px.get("roads_lines") or []
    for line in roads_lines:
        if isinstance(line, LineString) and not line.is_empty:
            pts = [(float(x), float(y)) for x, y in line.coords]
            if len(pts) >= 2:
                draw.line(pts, fill=(255, 255, 255, 200), width=2)

    # Each YOLO building drawn in segments, color per category.
    for record in sliced:
        for cat, pieces in record.items():
            color = CATEGORY_COLORS[cat]
            for poly in pieces:
                _render_polygon(draw, poly, color)

    _draw_legend(draw, overlay.size, breakdown_m2)
    composed = Image.alpha_composite(overlay, canvas).convert("RGB")

    out_dir = Path(settings.UPLOAD_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"encroachment_{uuid4().hex}.jpg"
    out_path = out_dir / name
    composed.save(out_path, format="JPEG", quality=92)
    return f"/uploads/{name}"


def _summarize(breakdown_m2: dict[str, float], district: str) -> str:
    parts = [
        f"{CATEGORY_LABELS[c]}: {breakdown_m2.get(c, 0.0):.1f} m²"
        for c in ENCROACHMENT_CATEGORIES
        if breakdown_m2.get(c, 0.0) > 0
    ]
    if not parts:
        return f"No encroachment detected against the OSM context near {district}."
    return f"Encroachment screening for {district} — " + "; ".join(parts) + "."


async def analyze_aerial_encroachment(
    image_path: str,
    district: str,
    gps_coords: str | None,
) -> EncroachmentResult:
    """Main entry point used by `ai_service.process_aerial_image`."""
    coords = _parse_gps_string(gps_coords)
    if coords is None:
        return _manual_review(
            image_path,
            "Aerial submission missing GPS coordinates — manual encroachment review required.",
        )
    lat, lng = coords

    try:
        polygons_px, model_size = await asyncio.to_thread(detect_building_polygons, image_path)
    except FileNotFoundError as e:
        logger.warning("Encroachment model unavailable: %s", e)
        return _manual_review(
            image_path,
            "Building segmenter weights not configured — manual encroachment review required.",
        )
    except Exception as e:
        logger.exception("YOLO encroachment inference failed: %s", e)
        return _manual_review(
            image_path,
            "Building segmenter failed on this aerial image — manual encroachment review required.",
        )

    base_image = _open_aerial(image_path)
    if base_image is None:
        return _manual_review(
            image_path,
            "Aerial image could not be opened — manual encroachment review required.",
        )

    image_size = model_size if model_size != (0, 0) else base_image.size
    if image_size[0] <= 0 or image_size[1] <= 0:
        image_size = base_image.size
    if base_image.size != image_size:
        base_image = base_image.resize(image_size)

    if not polygons_px:
        evidence_path = _annotated_empty(base_image, district)
        return EncroachmentResult(
            violation_flag=False,
            violation_type=None,
            total_area_m2=0.0,
            breakdown_m2={c: 0.0 for c in ENCROACHMENT_CATEGORIES},
            image_evidence_path=evidence_path,
            notes=(
                f"Building segmenter found no candidate footprints in this aerial submission for {district}."
            ),
        )

    projector = _make_projector(image_size, lat, lng)
    half_span_m = settings.AI_ENCROACHMENT_IMAGE_SPAN_M / 2.0

    try:
        osm_context = await fetch_osm_context(lat, lng, half_span_m)
    except (httpx.HTTPError, ValueError, RuntimeError) as e:
        logger.warning("Overpass fetch failed for (%s, %s): %s", lat, lng, e)
        return _manual_review(
            image_path,
            "OpenStreetMap context unavailable — aerial report routed to manual encroachment review.",
        )

    osm_px = _project_osm(osm_context, projector)
    sliced = [_classify_building(poly, osm_px) for poly in polygons_px]
    px_to_m2 = 1.0 / (projector.px_per_m ** 2)
    breakdown = _aggregate_breakdown(sliced, px_to_m2)
    total = round(sum(breakdown.values()), 1)
    headline, flag = _pick_violation_type(breakdown)

    evidence_path = _render_overlay(base_image, osm_px, sliced, breakdown)

    return EncroachmentResult(
        violation_flag=flag,
        violation_type=headline,
        total_area_m2=total,
        breakdown_m2=breakdown,
        image_evidence_path=evidence_path,
        notes=_summarize(breakdown, district),
    )


def _annotated_empty(base_image: Image.Image, district: str) -> str:
    canvas = base_image.copy().convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    _draw_legend(draw, canvas.size, {c: 0.0 for c in ENCROACHMENT_CATEGORIES})
    composed = canvas.convert("RGB")
    out_dir = Path(settings.UPLOAD_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"encroachment_{uuid4().hex}.jpg"
    out_path = out_dir / name
    composed.save(out_path, format="JPEG", quality=92)
    return f"/uploads/{name}"
