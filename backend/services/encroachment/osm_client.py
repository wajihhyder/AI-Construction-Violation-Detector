"""
Overpass-API helper for the encroachment service.

Each aerial submission needs a local rendering of the OSM context (roads,
public-space, water polygons, and known building footprints) so we can decide
which slice of every YOLO-detected building is encroaching on what.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

import httpx
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union
from shapely.validation import make_valid

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT_S = 15.0

# Tag-set definitions for each context layer. Keep these conservative — false
# positives in "public space" or "water" would create phantom encroachments.
PUBLIC_SPACE_TAGS = (
    'leisure~"park|playground|garden|pitch|recreation_ground|sports_centre"',
    'landuse~"recreation_ground|grass|village_green|cemetery"',
    'amenity~"school|hospital|place_of_worship|university|college"',
)
WATER_TAGS = (
    'natural~"water|wetland|coastline"',
    'water',
    'waterway',
)


@dataclass(frozen=True)
class OSMContext:
    roads: list[LineString] = field(default_factory=list)
    public_space: list[Polygon] = field(default_factory=list)
    water: list[Polygon] = field(default_factory=list)
    buildings: list[Polygon] = field(default_factory=list)


def _bbox_around(lat: float, lng: float, half_span_m: float) -> tuple[float, float, float, float]:
    lat_delta = half_span_m / 111_320.0
    lng_delta = half_span_m / (111_320.0 * max(math.cos(math.radians(lat)), 1e-6))
    return (lat - lat_delta, lng - lng_delta, lat + lat_delta, lng + lng_delta)


def _build_query(south: float, west: float, north: float, east: float) -> str:
    bbox = f"({south},{west},{north},{east})"
    public_filters = "\n      ".join(f'way[{tag}]{bbox};' for tag in PUBLIC_SPACE_TAGS)
    public_rel_filters = "\n      ".join(f'relation[{tag}]{bbox};' for tag in PUBLIC_SPACE_TAGS)
    water_filters = "\n      ".join(f'way[{tag}]{bbox};' for tag in WATER_TAGS)
    water_rel_filters = "\n      ".join(f'relation[{tag}]{bbox};' for tag in WATER_TAGS)
    return f"""
    [out:json][timeout:{int(OVERPASS_TIMEOUT_S)}];
    (
      way[highway]{bbox};
      way[building]{bbox};
      {public_filters}
      {public_rel_filters}
      {water_filters}
      {water_rel_filters}
    );
    out geom;
    """


def _coords(geom: list[dict]) -> list[tuple[float, float]]:
    return [(pt["lon"], pt["lat"]) for pt in geom if "lon" in pt and "lat" in pt]


def _closed_polygon(coords: list[tuple[float, float]]) -> Polygon | None:
    if len(coords) < 4:
        return None
    if coords[0] != coords[-1]:
        coords = coords + [coords[0]]
    try:
        poly = Polygon(coords)
        if not poly.is_valid:
            fixed = make_valid(poly)
            if isinstance(fixed, Polygon):
                poly = fixed
            elif isinstance(fixed, MultiPolygon) and not fixed.is_empty:
                poly = max(fixed.geoms, key=lambda g: g.area)
            else:
                return None
        if poly.is_empty or poly.area <= 0:
            return None
        return poly
    except (ValueError, TypeError):
        return None


def _classify_way(
    el: dict,
    ctx: dict[str, list],
) -> None:
    geom = el.get("geometry") or []
    coords = _coords(geom)
    if len(coords) < 2:
        return
    tags = el.get("tags") or {}

    if "highway" in tags:
        try:
            ctx["roads"].append(LineString(coords))
        except (ValueError, TypeError):
            pass
        return

    poly = _closed_polygon(coords)
    if poly is None:
        return
    if "building" in tags:
        ctx["buildings"].append(poly)
    elif _tag_matches(tags, PUBLIC_SPACE_TAGS):
        ctx["public_space"].append(poly)
    elif _tag_matches(tags, WATER_TAGS):
        ctx["water"].append(poly)


def _tag_matches(tags: dict[str, str], patterns: tuple[str, ...]) -> bool:
    for raw in patterns:
        if "~" in raw:
            key, regex = raw.split("~", 1)
            value = tags.get(key.strip())
            if value is None:
                continue
            regex = regex.strip().strip('"')
            for option in regex.split("|"):
                if option and option in value:
                    return True
        else:
            if tags.get(raw.strip()) is not None:
                return True
    return False


def _classify_relation(el: dict, ctx: dict[str, list]) -> None:
    tags = el.get("tags") or {}
    members = el.get("members") or []
    outer_rings: list[list[tuple[float, float]]] = []
    for m in members:
        if m.get("role") != "outer":
            continue
        coords = _coords(m.get("geometry") or [])
        if len(coords) >= 3:
            outer_rings.append(coords)
    if not outer_rings:
        return
    polys = [p for p in (_closed_polygon(r) for r in outer_rings) if p is not None]
    if not polys:
        return
    bucket = "public_space" if _tag_matches(tags, PUBLIC_SPACE_TAGS) else (
        "water" if _tag_matches(tags, WATER_TAGS) else None
    )
    if bucket is None:
        return
    for p in polys:
        ctx[bucket].append(p)


def _dedupe_polygons(polys: list[Polygon]) -> list[Polygon]:
    if not polys:
        return []
    try:
        merged = unary_union(polys)
    except Exception as e:
        logger.debug("Polygon union failed, keeping raw list: %s", e)
        return polys
    if isinstance(merged, Polygon):
        return [merged]
    if isinstance(merged, MultiPolygon):
        return [g for g in merged.geoms if not g.is_empty]
    return polys


async def fetch_osm_context(
    lat: float,
    lng: float,
    half_span_m: float,
) -> OSMContext:
    """Pull roads, public space, water, and known building polygons around `(lat, lng)`."""
    south, west, north, east = _bbox_around(lat, lng, half_span_m)
    query = _build_query(south, west, north, east)
    async with httpx.AsyncClient(timeout=OVERPASS_TIMEOUT_S) as client:
        response = await client.post(OVERPASS_URL, data={"data": query})
        response.raise_for_status()
        payload = response.json()

    ctx: dict[str, list] = {
        "roads": [],
        "public_space": [],
        "water": [],
        "buildings": [],
    }
    for el in payload.get("elements") or []:
        kind = el.get("type")
        if kind == "way":
            _classify_way(el, ctx)
        elif kind == "relation":
            _classify_relation(el, ctx)

    return OSMContext(
        roads=ctx["roads"],
        public_space=_dedupe_polygons(ctx["public_space"]),
        water=_dedupe_polygons(ctx["water"]),
        buildings=_dedupe_polygons(ctx["buildings"]),
    )
