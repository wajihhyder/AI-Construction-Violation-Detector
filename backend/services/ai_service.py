"""
AI Service — Construction Violation Detection
=============================================
This module is a STUB. The actual YOLOv8 model integration will be
connected separately. All functions below must be implemented to
call the trained model and return the result in the specified format.
"""


async def process_street_view_image(image_path: str, district: str) -> dict:
    """
    STUB: Analyze a street-view image for floor count violations.

    Expected steps when implemented:
    1. Load image from image_path
    2. Run YOLOv8 floor detection model on the image
    3. Count detected floors
    4. Call rule_engine.check_floor_violation(detected_floors, district)
    5. Return result dict

    Args:
        image_path (str): Absolute path to the stored image file
        district (str): Confirmed Karachi district name (e.g., "Gulshan-e-Iqbal")

    Returns:
        dict with keys:
            - violation_flag (bool): True if violation detected
            - violation_type (str | None): "Extra_Floor" or None
            - detected_floors (int | None): Number of floors detected
            - setback_error (float | None): Always None for street view
            - image_evidence_path (str): Path to image (annotated version if available)
    """
    # TODO: Implement YOLOv8 street view analysis
    # raise NotImplementedError("Connect YOLOv8 model here")

    # Temporary stub return — remove when model is connected
    return {
        "violation_flag": False,
        "violation_type": None,
        "detected_floors": None,
        "setback_error": None,
        "image_evidence_path": image_path,
    }


async def process_aerial_image(image_path: str, district: str) -> dict:
    """
    STUB: Analyze an aerial/satellite image for setback and encroachment violations.

    Expected steps when implemented:
    1. Load image from image_path
    2. Run YOLOv8 boundary/encroachment detection model
    3. Measure setback distances from detected boundaries
    4. Call rule_engine.check_aerial_violations(boundaries, setbacks, district)
    5. Return result dict

    Args:
        image_path (str): Absolute path to the stored image file
        district (str): Confirmed Karachi district name

    Returns:
        dict with keys:
            - violation_flag (bool): True if any violation found
            - violation_type (str | None): "Setback_Breach" | "Encroachment" | None
            - detected_floors (int | None): Always None for aerial
            - setback_error (float | None): Deviation from required setback in meters
            - image_evidence_path (str): Path to image (annotated version if available)
    """
    # TODO: Implement YOLOv8 aerial analysis
    # raise NotImplementedError("Connect YOLOv8 model here")

    # Temporary stub return — remove when model is connected
    return {
        "violation_flag": False,
        "violation_type": None,
        "detected_floors": None,
        "setback_error": None,
        "image_evidence_path": image_path,
    }
