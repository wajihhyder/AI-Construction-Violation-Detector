"""
YOLO building segmenter for aerial imagery.

The model is the Roboflow encroachment dataset
(https://universe.roboflow.com/encroachment/encroachment-dwic8) fine-tuned with
Ultralytics; see backend/data/encroachment_dataset.yaml.

Segmentation outputs are preferred (we get true building polygons), but the
wrapper accepts detection models too — bounding boxes are turned into
rectangular polygons so the rest of the pipeline can stay uniform.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
from shapely.validation import make_valid

from core.config import settings

logger = logging.getLogger(__name__)

_MODEL = None
_MODEL_PATH: str | None = None
_MIN_POLYGON_VERTICES = 3
_MIN_POLYGON_AREA_PX = 16.0


def _normalize_device() -> str | None:
    value = settings.AI_DEVICE.strip()
    if not value or value.lower() == "auto":
        return None
    return value


def _load_encroachment_model():
    """Lazy-load and cache the YOLO model."""
    global _MODEL, _MODEL_PATH

    model_path = settings.resolved_ai_encroachment_model_path()
    if not model_path.exists():
        raise FileNotFoundError(f"Encroachment model not found: {model_path}")

    current = str(model_path)
    if _MODEL is not None and _MODEL_PATH == current:
        return _MODEL

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "Ultralytics is not installed. Run `pip install -r backend/requirements.txt`.",
        ) from exc

    _MODEL = YOLO(current)
    _MODEL_PATH = current
    return _MODEL


def _mask_to_polygon(mask: np.ndarray) -> Polygon | None:
    """
    Convert a single binary mask (H×W uint8 / bool) into the largest valid
    Polygon. Returns None if the mask is empty or degenerate.
    """
    try:
        import cv2  # type: ignore
    except ImportError:
        cv2 = None

    if cv2 is not None:
        binary = (mask.astype(np.uint8) > 0).astype(np.uint8) * 255
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        polys: list[Polygon] = []
        for c in contours:
            if len(c) < _MIN_POLYGON_VERTICES:
                continue
            pts = [(float(p[0][0]), float(p[0][1])) for p in c]
            try:
                poly = Polygon(pts)
                if not poly.is_valid:
                    poly = make_valid(poly)
                if isinstance(poly, Polygon) and poly.area >= _MIN_POLYGON_AREA_PX:
                    polys.append(poly)
            except (ValueError, TypeError):
                continue
        if not polys:
            return None
        return max(polys, key=lambda p: p.area)

    # Fallback when OpenCV is unavailable: use the mask bounding box.
    ys, xs = np.where(mask > 0)
    if xs.size == 0 or ys.size == 0:
        return None
    x0, x1 = float(xs.min()), float(xs.max())
    y0, y1 = float(ys.min()), float(ys.max())
    if (x1 - x0) * (y1 - y0) < _MIN_POLYGON_AREA_PX:
        return None
    return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])


def _bbox_to_polygon(xyxy: np.ndarray) -> Polygon | None:
    x0, y0, x1, y1 = (float(v) for v in xyxy)
    if (x1 - x0) * (y1 - y0) < _MIN_POLYGON_AREA_PX:
        return None
    return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])


def detect_building_polygons(image_path: str) -> tuple[list[Polygon], tuple[int, int]]:
    """
    Run inference on `image_path` and return (polygons_in_pixel_space, (width, height)).

    Each polygon is in image-pixel coordinates with (0, 0) at top-left. Width and
    height come from the model's processed image so the caller can normalize.
    """
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Aerial image not found: {image_path}")

    model = _load_encroachment_model()
    predictions = model.predict(
        source=image_path,
        conf=settings.AI_ENCROACHMENT_CONFIDENCE,
        iou=settings.AI_ENCROACHMENT_IOU,
        verbose=False,
        device=_normalize_device(),
        retina_masks=True,
    )
    if not predictions:
        return [], (0, 0)

    result = predictions[0]
    orig_shape = getattr(result, "orig_shape", None) or (0, 0)
    height, width = int(orig_shape[0]), int(orig_shape[1])

    polygons: list[Polygon] = []
    masks = getattr(result, "masks", None)
    if masks is not None and getattr(masks, "data", None) is not None:
        for mask_tensor in masks.data:
            mask_np = mask_tensor.detach().cpu().numpy() if hasattr(mask_tensor, "detach") else np.asarray(mask_tensor)
            poly = _mask_to_polygon(mask_np)
            if poly is not None:
                polygons.append(poly)

    if polygons:
        return polygons, (width, height)

    boxes = getattr(result, "boxes", None)
    if boxes is not None and getattr(boxes, "xyxy", None) is not None:
        xyxy = boxes.xyxy
        xyxy_np = xyxy.detach().cpu().numpy() if hasattr(xyxy, "detach") else np.asarray(xyxy)
        for row in xyxy_np:
            poly = _bbox_to_polygon(row)
            if poly is not None:
                polygons.append(poly)

    return polygons, (width, height)
