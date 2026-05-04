import uuid
from pathlib import Path

from fastapi import UploadFile
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from core.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def get_gps_string_for_saved_path(url_path: str) -> str | None:
    """Return 'lat,lng' for a saved upload path, or None."""
    lat, lng = _get_exif_gps(absolute_path_from_url(url_path))
    return coords_to_string(lat, lng)


def _ratio_to_float(r) -> float:
    if r is None:
        raise ValueError("ratio")
    if hasattr(r, "numerator") and hasattr(r, "denominator"):
        d = float(r.denominator) if r.denominator else 1.0
        return float(r.numerator) / d
    if getattr(r, "__len__", None) and len(r) >= 2:
        return float(r[0]) / float(r[1]) if float(r[1]) else float(r[0])
    return float(r)


def _ref_positive(ref, positive: str) -> bool:
    if ref is None:
        return True
    s = ref.decode("ascii", errors="ignore") if isinstance(ref, bytes) else str(ref)
    return s.upper().startswith(positive)


def _gps_from_exif_gpsdict(gps_data: dict) -> tuple[float | None, float | None]:
    lat_ref = gps_data.get("GPSLatitudeRef")
    lng_ref = gps_data.get("GPSLongitudeRef")
    lat_vals = gps_data.get("GPSLatitude")
    lng_vals = gps_data.get("GPSLongitude")
    if not lat_vals or not lng_vals:
        return None, None

    lat = _ratio_to_float(lat_vals[0]) + _ratio_to_float(lat_vals[1]) / 60.0
    if len(lat_vals) > 2:
        lat += _ratio_to_float(lat_vals[2]) / 3600.0
    lng = _ratio_to_float(lng_vals[0]) + _ratio_to_float(lng_vals[1]) / 60.0
    if len(lng_vals) > 2:
        lng += _ratio_to_float(lng_vals[2]) / 3600.0
    if not _ref_positive(lat_ref, "N"):
        lat = -lat
    if not _ref_positive(lng_ref, "E"):
        lng = -lng
    return lat, lng


def _get_exif_gps_pillow(image_path: str) -> tuple[float | None, float | None]:
    """Extract lat/lng from EXIF if present (IFD.GPS for Pillow 10+)."""
    try:
        img = Image.open(image_path)
        img.load()
        exif = img.getexif()
        if not exif and "exif" in img.info:
            raw = img.info["exif"]
            if isinstance(raw, bytes):
                try:
                    exif = Image.Exif()
                    payload = raw[6:] if raw.startswith(b"Exif\x00\x00") else raw
                    exif.load(payload)
                except Exception:
                    exif = None
        if not exif:
            return None, None

        gps_ifd = None
        try:
            from PIL.ExifTags import IFD

            gps_ifd = exif.get_ifd(IFD.GPSInfo)
        except Exception:
            gps_ifd = None

        if not gps_ifd:
            for tag_id, val in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo" and isinstance(val, dict):
                    gps_ifd = val
                    break

        if not gps_ifd:
            return None, None

        gps_data: dict = {}
        for k, v in gps_ifd.items():
            sub = GPSTAGS.get(k, k)
            gps_data[sub] = v

        return _gps_from_exif_gpsdict(gps_data)
    except Exception:
        return None, None


def _get_exif_gps_piexif(image_path: str) -> tuple[float | None, float | None]:
    """JPEG fallback when Pillow misses GPS (some MakerNote / segment layouts)."""
    try:
        import piexif
        from piexif import GPSIFD

        raw = piexif.load(image_path)
        gps = raw.get("GPS") or {}
        if not gps:
            return None, None

        lat_v = gps.get(GPSIFD.GPSLatitude)
        lng_v = gps.get(GPSIFD.GPSLongitude)
        if not lat_v or not lng_v:
            return None, None

        def rat_to_float(t) -> float:
            if isinstance(t, (tuple, list)) and len(t) == 2:
                num, den = t[0], t[1]
                return float(num) / float(den) if den else float(num)
            return float(t)

        def dms_to_dd(vals) -> float:
            d = rat_to_float(vals[0])
            m = rat_to_float(vals[1])
            s = rat_to_float(vals[2])
            return d + m / 60.0 + s / 3600.0

        lat = dms_to_dd(lat_v)
        lng = dms_to_dd(lng_v)

        lat_ref = gps.get(GPSIFD.GPSLatitudeRef)
        lng_ref = gps.get(GPSIFD.GPSLongitudeRef)
        if isinstance(lat_ref, bytes):
            lat_ref = lat_ref.decode("ascii", errors="ignore")
        if isinstance(lng_ref, bytes):
            lng_ref = lng_ref.decode("ascii", errors="ignore")
        if isinstance(lat_ref, str) and lat_ref.upper().startswith("S"):
            lat = -lat
        if isinstance(lng_ref, str) and lng_ref.upper().startswith("W"):
            lng = -lng
        return lat, lng
    except Exception:
        return None, None


def _get_exif_gps(image_path: str) -> tuple[float | None, float | None]:
    lat, lng = _get_exif_gps_pillow(image_path)
    if lat is not None and lng is not None:
        return lat, lng
    suffix = Path(image_path).suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return _get_exif_gps_piexif(image_path)
    return None, None


def coords_to_string(lat: float | None, lng: float | None) -> str | None:
    if lat is None or lng is None:
        return None
    return f"{lat:.6f},{lng:.6f}"


async def save_uploaded_image(file: UploadFile) -> tuple[str, str | None]:
    """
    Validate and save upload. Returns (relative_url_path_for_static, gps_coords or None).
    relative path like /uploads/report_uuid.jpg
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError("INVALID_IMAGE_TYPE")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "image.jpg").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        suffix = ".jpg"
    name = f"report_{uuid.uuid4().hex}{suffix}"
    dest = upload_dir / name

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    total = 0
    chunk_size = 1024 * 1024

    with open(dest, "wb") as out:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                out.close()
                dest.unlink(missing_ok=True)
                raise ValueError("FILE_TOO_LARGE")
            out.write(chunk)

    rel = f"/uploads/{name}"
    lat, lng = _get_exif_gps(str(dest))
    gps = coords_to_string(lat, lng)
    return rel, gps


def absolute_path_from_url(url_path: str) -> str:
    """Convert /uploads/foo.jpg to filesystem path."""
    if url_path.startswith("/uploads/"):
        filename = url_path.replace("/uploads/", "", 1)
        return str(Path(settings.UPLOAD_DIR) / filename)
    return url_path
