"""
SBCA Rule Engine
================
Encodes Sindh Building Control Authority zoning regulations.
Floor limits and setback requirements per Karachi district.

STUB: Populate SBCA_RULES with actual regulatory values.
The check functions below are complete and functional once rules are populated.
"""

# TODO: Replace with actual SBCA zoning data per district
SBCA_RULES = {
    "Clifton": {"max_floors": 4, "min_setback_m": 3.0},
    "Defence": {"max_floors": 4, "min_setback_m": 3.0},
    "Gulshan-e-Iqbal": {"max_floors": 5, "min_setback_m": 2.0},
    "Korangi": {"max_floors": 4, "min_setback_m": 2.0},
    "Orangi Town": {"max_floors": 3, "min_setback_m": 1.5},
    "Saddar": {"max_floors": 6, "min_setback_m": 2.5},
    "Malir": {"max_floors": 3, "min_setback_m": 1.5},
    "North Nazimabad": {"max_floors": 4, "min_setback_m": 2.0},
    "Landhi": {"max_floors": 3, "min_setback_m": 1.5},
    "Baldia": {"max_floors": 3, "min_setback_m": 1.5},
    "DEFAULT": {"max_floors": 4, "min_setback_m": 2.0},
}


def get_district_rules(district_location: str) -> dict:
    """
    `district_location` is usually `Town (District)`. Match rules by full label or town name only.
    """
    if district_location in SBCA_RULES:
        return SBCA_RULES[district_location]
    if "(" in district_location:
        town = district_location.split("(")[0].strip()
        if town in SBCA_RULES:
            return SBCA_RULES[town]
    return SBCA_RULES["DEFAULT"]


def check_floor_violation(detected_floors: int, district: str) -> dict:
    """Check if detected floors exceed SBCA limit for the district."""
    rules = get_district_rules(district)
    max_allowed = rules["max_floors"]
    if detected_floors > max_allowed:
        return {
            "violation_flag": True,
            "violation_type": "Extra_Floor",
            "detail": f"Detected {detected_floors} floors; max allowed in {district} is {max_allowed}.",
        }
    return {"violation_flag": False, "violation_type": None, "detail": "Compliant"}


def check_setback_violation(measured_setback_m: float, district: str) -> dict:
    """Check if measured setback is less than SBCA minimum for the district."""
    rules = get_district_rules(district)
    min_required = rules["min_setback_m"]
    if measured_setback_m < min_required:
        error = round(min_required - measured_setback_m, 2)
        return {
            "violation_flag": True,
            "violation_type": "Setback_Breach",
            "setback_error": error,
            "detail": f"Setback {measured_setback_m}m is {error}m below required {min_required}m.",
        }
    return {
        "violation_flag": False,
        "violation_type": None,
        "setback_error": 0.0,
        "detail": "Compliant",
    }


def check_encroachment_violation(encroachment_depth_m: float, district: str) -> dict:
    """
    Encroachment = building footprint extends into the SBCA-required setback strip
    along the road / parcel boundary. `encroachment_depth_m` is the measured deficit.
    """
    if encroachment_depth_m <= 0:
        return {
            "violation_flag": False,
            "violation_type": None,
            "setback_error": 0.0,
            "detail": "Compliant",
        }
    rules = get_district_rules(district)
    min_required = rules["min_setback_m"]
    depth = round(encroachment_depth_m, 2)
    return {
        "violation_flag": True,
        "violation_type": "Encroachment",
        "setback_error": depth,
        "detail": (
            f"Building footprint extends {depth}m into the required "
            f"{min_required}m setback in {district}."
        ),
    }
