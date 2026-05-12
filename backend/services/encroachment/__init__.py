"""
Aerial encroachment screening
=============================
Segments buildings out of an aerial submission with a YOLO model trained on
the Roboflow encroachment dataset, then classifies each building footprint
against OpenStreetMap context (roads, public space, water, mapped parcels)
to produce a per-category area breakdown.
"""

from .service import (
    ENCROACHMENT_CATEGORIES,
    EncroachmentResult,
    analyze_aerial_encroachment,
)

__all__ = [
    "ENCROACHMENT_CATEGORIES",
    "EncroachmentResult",
    "analyze_aerial_encroachment",
]
