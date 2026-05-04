"""
Karachi administrative areas: district (CDGK-style) + town / sub-division.
`district_location` on reports stores `"{town} ({district})"` for a unique, filterable label.
"""

from __future__ import annotations

# (district name, town name) — aligned with Sindh local government structure for Karachi.
KARACHI_ADMIN_ROWS: list[tuple[str, str]] = [
    ("District Central", "Gulberg"),
    ("District Central", "Liaquatabad"),
    ("District Central", "Nazimabad"),
    ("District Central", "New Karachi"),
    ("District Central", "New Nazimabad"),
    ("District East", "Ferozabad"),
    ("District East", "Gulshan-e-Iqbal"),
    ("District East", "Gulzar-e-Hijri"),
    ("District East", "Jamshed Quarters"),
    ("Karachi South", "Arambagh"),
    ("Karachi South", "Civil Lines"),
    ("Karachi South", "Garden"),
    ("Karachi South", "Lyari"),
    ("Karachi South", "Saddar"),
    ("Karachi West", "Mango Pir"),
    ("Karachi West", "Mominabad"),
    ("Karachi West", "Orangi Town"),
    ("Keamari", "Baldia"),
    ("Keamari", "Harbor"),
    ("Keamari", "Maripur"),
    ("Keamari", "SITE"),
    ("Korangi", "Korangi"),
    ("Korangi", "Landhi"),
    ("Korangi", "Model Colony"),
    ("Korangi", "Shah Faisal"),
    ("Malir", "Airport"),
    ("Malir", "Bin Qasim"),
    ("Malir", "Gadap"),
    ("Malir", "Ibrahim Hyderi"),
    ("Malir", "Murad Memon"),
    ("Malir", "Shah Mureed"),
]


def format_area_label(district: str, town: str) -> str:
    return f"{town} ({district})"


# Sorted unique labels for dropdowns (citizen + authority filters).
KARACHI_DISTRICTS: list[str] = sorted(
    {format_area_label(d, t) for d, t in KARACHI_ADMIN_ROWS},
    key=str.casefold,
)
