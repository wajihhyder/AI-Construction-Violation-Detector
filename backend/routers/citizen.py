import logging
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from core.districts import KARACHI_DISTRICTS
from core.limiter import limiter
from database import SessionLocal, get_db
from models.ai_result import AIAnalysisResult
from models.report import ViolationsReport
from schemas.report import AIResultPublic, CitizenReportPollResponse, CitizenReportSubmitResponse, DistrictPatch
from services import ai_service
from services.geocoding_service import reverse_geocode_district
from core.tracking_id import generate_tracking_id
from services.image_service import (
    absolute_path_from_url,
    get_gps_string_for_saved_path,
    save_uploaded_image,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/citizen", tags=["citizen"])

DEFAULT_GPS = "24.860700,67.001128"


async def run_ai_analysis(
    report_id: int,
    image_rel_path: str,
    input_type_street: bool,
    fallback_gps: str | None,
) -> None:
    db = SessionLocal()
    try:
        report = db.query(ViolationsReport).filter(ViolationsReport.report_id == report_id).first()
        if not report:
            return
        district = report.district_location

        abs_path = absolute_path_from_url(image_rel_path)
        if input_type_street:
            result = await ai_service.process_street_view_image(abs_path, district)
        else:
            result = await ai_service.process_aerial_image(abs_path, district)

        # Order: task arg (same as submit), DB column, EXIF re-read from disk, Karachi default.
        coords = (
            fallback_gps
            or report.submission_gps_coords
            or get_gps_string_for_saved_path(image_rel_path)
            or DEFAULT_GPS
        )
        raw_evidence = result.get("image_evidence_path") or image_rel_path
        if isinstance(raw_evidence, str) and raw_evidence.startswith("/uploads/"):
            evidence_path = raw_evidence
        else:
            evidence_path = image_rel_path
        ai_row = AIAnalysisResult(
            gps_coords=coords,
            violation_flag=bool(result.get("violation_flag")),
            violation_type=result.get("violation_type"),
            detected_floors=result.get("detected_floors"),
            setback_error=result.get("setback_error"),
            image_evidence_path=evidence_path,
        )
        db.add(ai_row)
        db.flush()

        report.ai_result_id = ai_row.result_id
        report.status = "New"
        db.commit()
    except Exception as e:
        logger.exception("AI analysis failed for report %s: %s", report_id, e)
        try:
            report = db.query(ViolationsReport).filter(ViolationsReport.report_id == report_id).first()
            if report:
                report.status = "Invalid"
                report.notes = (report.notes or "") + f" [AI error: {str(e)[:200]}]"
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


def _report_to_poll(r: ViolationsReport) -> CitizenReportPollResponse:
    ai = AIResultPublic.model_validate(r.ai_result) if r.ai_result else None
    return CitizenReportPollResponse(
        report_id=r.report_id,
        tracking_id=r.tracking_id,
        status=r.status,
        district_location=r.district_location,
        input_type=r.input_type,
        submission_date=r.submission_date,
        reporter_type=r.reporter_type,
        ai_result=ai,
    )


@router.get("/districts")
async def list_districts():
    return {"districts": KARACHI_DISTRICTS}


@router.post("/report", response_model=CitizenReportSubmitResponse)
@limiter.limit("10/minute")
async def submit_report(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    image: UploadFile = File(...),
    input_type: str = Form(...),
    reporter_type: str = Form("Citizen"),
    district_location: str = Form(...),
    gps_lat: float | None = Form(default=None),
    gps_lng: float | None = Form(default=None),
):
    it_lower = input_type.lower().strip()
    if it_lower == "street":
        input_type_bool = True
    elif it_lower == "aerial":
        input_type_bool = False
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "input_type must be street or aerial", "code": "VALIDATION_ERROR"},
        )

    try:
        rel_path, gps_from_file = await save_uploaded_image(image)
    except ValueError as e:
        code = str(e)
        if code == "FILE_TOO_LARGE":
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={"detail": "Image too large (max 10MB)", "code": "FILE_TOO_LARGE"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Invalid image file", "code": "INVALID_IMAGE"},
        )

    gps = gps_from_file
    if not gps and gps_lat is not None and gps_lng is not None:
        if -90.0 <= gps_lat <= 90.0 and -180.0 <= gps_lng <= 180.0:
            gps = f"{gps_lat:.6f},{gps_lng:.6f}"

    report = ViolationsReport(
        district_location=district_location.strip(),
        input_type=input_type_bool,
        reporter_type=reporter_type,
        status="Processing",
        submission_date=datetime.utcnow(),
        submission_gps_coords=gps,
        tracking_id=f"TMP-{uuid4().hex}",
    )
    db.add(report)
    db.flush()
    report.tracking_id = generate_tracking_id(report.report_id, report.submission_date)
    db.commit()
    db.refresh(report)

    background_tasks.add_task(
        run_ai_analysis,
        report.report_id,
        rel_path,
        input_type_bool,
        gps,
    )

    detected = district_location.strip()
    if gps:
        try:
            parts = gps.split(",")
            lat, lng = float(parts[0]), float(parts[1])
            geo = await reverse_geocode_district(lat, lng)
            lbl = geo.get("label")
            if lbl:
                detected = str(lbl)
            elif geo.get("district"):
                detected = str(geo["district"])
        except (ValueError, IndexError, TypeError):
            pass

    return CitizenReportSubmitResponse(
        report_id=report.report_id,
        tracking_id=report.tracking_id,
        status="Processing",
        message="Report submitted. Use your Tracking ID to check progress.",
        gps_coords=gps,
        detected_district=detected,
    )


@router.get("/report/{report_id}", response_model=CitizenReportPollResponse)
async def get_report(report_id: int, db: Session = Depends(get_db)):
    r = db.query(ViolationsReport).filter(ViolationsReport.report_id == report_id).first()
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Report not found", "code": "NOT_FOUND"},
        )
    return _report_to_poll(r)


@router.get("/track/{tracking_id}", response_model=CitizenReportPollResponse)
async def get_report_by_tracking_id(tracking_id: str, db: Session = Depends(get_db)):
    tid = tracking_id.strip().upper()
    r = db.query(ViolationsReport).filter(ViolationsReport.tracking_id == tid).first()
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report found for this Tracking ID.",
        )
    return _report_to_poll(r)


@router.patch("/report/{report_id}/district")
async def patch_district(report_id: int, body: DistrictPatch, db: Session = Depends(get_db)):
    r = db.query(ViolationsReport).filter(ViolationsReport.report_id == report_id).first()
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Report not found", "code": "NOT_FOUND"},
        )
    if r.status != "Processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "District can only be updated while processing", "code": "BAD_STATE"},
        )
    r.district_location = body.district_location.strip()
    db.commit()
    return {"report_id": report_id, "district_location": r.district_location}
