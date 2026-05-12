"""
Encroachment detection package
==============================
Analyzes aerial imagery against OSM building / road footprints to detect
construction that encroaches onto the road right-of-way or beyond parcel
boundaries.
"""

from .service import (
    EncroachmentResult,
    analyze_aerial_encroachment,
)

__all__ = ["EncroachmentResult", "analyze_aerial_encroachment"]
