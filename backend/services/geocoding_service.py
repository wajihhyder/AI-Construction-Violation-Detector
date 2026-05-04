import logging

import httpx

from core.config import settings
from services.admin_areas_service import lookup_karachi_admin

logger = logging.getLogger(__name__)


async def reverse_geocode_district(lat: float, lng: float) -> dict:
    """
    Resolve GPS to Karachi admin district + town using packaged geometries first,
    then optional Geoapify text hints.

    Returns keys: district, town, label, city, confidence, source, fallback,
    inside_karachi_bounds (and Geoapify-specific fields when used).
    """
    admin = lookup_karachi_admin(lat, lng)
    inside = admin.get("inside_karachi_bounds", False)

    if admin.get("label"):
        return {
            "district": admin["district"],
            "town": admin["town"],
            "label": admin["label"],
            "city": "Karachi",
            "confidence": "admin_map",
            "source": "karachi_admin",
            "fallback": False,
            "inside_karachi_bounds": inside,
        }

    if not settings.GEOAPIFY_API_KEY:
        return {
            "district": None,
            "town": None,
            "label": None,
            "city": "Karachi" if inside else None,
            "confidence": "none",
            "source": "none",
            "fallback": True,
            "inside_karachi_bounds": inside,
        }

    url = "https://api.geoapify.com/v1/geocode/reverse"
    params = {
        "lat": lat,
        "lon": lng,
        "apiKey": settings.GEOAPIFY_API_KEY,
        "lang": "en",
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning("Geoapify reverse geocode failed: %s", e)
        return {
            "district": None,
            "town": None,
            "label": None,
            "city": "Karachi" if inside else None,
            "confidence": "none",
            "source": "geoapify_error",
            "fallback": True,
            "inside_karachi_bounds": inside,
        }

    features = data.get("features") or []
    if not features:
        return {
            "district": None,
            "town": None,
            "label": None,
            "city": "Karachi" if inside else None,
            "confidence": "none",
            "source": "geoapify",
            "fallback": True,
            "inside_karachi_bounds": inside,
        }

    props = features[0].get("properties") or {}
    city = props.get("city") or props.get("county") or "Karachi"
    locality = (
        props.get("suburb")
        or props.get("district")
        or props.get("neighbourhood")
        or props.get("quarter")
        or props.get("county")
    )
    confidence = "high" if locality else "low"
    return {
        "district": locality,
        "town": None,
        "label": locality,
        "city": city,
        "confidence": confidence,
        "source": "geoapify",
        "fallback": not locality,
        "inside_karachi_bounds": inside,
    }
