import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from core.config import settings
from core.dependencies import require_authority
from core.districts import KARACHI_DISTRICTS
from database import get_db
from models.report import ViolationsReport
from models.user import User
from schemas.report import (
    AIResultPublic,
    AuthorityReportDetail,
    AuthorityReportListItem,
    AuthorityStatusPatch,
    MapReportPin,
    PaginatedReports,
    StatsResponse,
)
from services.notice_context import build_authority_report_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/authority", tags=["authority"])

_notice_templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

ALLOWED_TRANSITIONS = {
    ("New", "Under_Review"),
    ("Under_Review", "Verified"),
    ("Under_Review", "Invalid"),
}


def _parse_gps(coords: str | None) -> tuple[float, float] | None:
    if not coords:
        return None
    parts = coords.split(",")
    if len(parts) != 2:
        return None
    try:
        return float(parts[0].strip()), float(parts[1].strip())
    except ValueError:
        return None


def _scoped_reports_query(db: Session, current_user: User):
    """Apply authority area scoping without hiding reports by workflow state or AI outcome."""
    q = db.query(ViolationsReport).options(joinedload(ViolationsReport.ai_result))
    if current_user.can_view_all_areas:
        return q
    assigned_area = (current_user.assigned_area or "").strip()
    if not assigned_area:
        return q.filter(ViolationsReport.report_id == -1)
    return q.filter(ViolationsReport.district_location == assigned_area)


def _scoped_report_or_404(db: Session, current_user: User, report_id: int) -> ViolationsReport:
    report = (
        _scoped_reports_query(db, current_user)
        .filter(ViolationsReport.report_id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Report not found", "code": "NOT_FOUND"},
        )
    return report


@router.get("/reports/stats", response_model=StatsResponse)
async def reports_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority),
):
    rows = _scoped_reports_query(db, current_user).all()
    total = len(rows)
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    by_violation_type: dict[str, int] = {
        "Extra_Floor": 0,
        "Setback_Breach": 0,
        "Encroachment": 0,
        "Manual_Review": 0,
    }
    compliant = 0
    for r in rows:
        if r.ai_result:
            if not r.ai_result.violation_flag and r.ai_result.violation_type != "Manual_Review":
                compliant += 1
            vt = r.ai_result.violation_type
            if vt and vt in by_violation_type and (r.ai_result.violation_flag or vt == "Manual_Review"):
                by_violation_type[vt] += 1

    return StatsResponse(
        total=total,
        by_status=by_status,
        by_violation_type=by_violation_type,
        compliant=compliant,
    )


@router.get("/reports/map", response_model=list[MapReportPin])
async def reports_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority),
):
    """All reports that have a usable lat/lng (AI result GPS, else GPS captured at submit)."""
    rows = _scoped_reports_query(db, current_user).order_by(ViolationsReport.report_id.desc()).all()
    out: list[MapReportPin] = []
    for r in rows:
        parsed = None
        if r.ai_result and r.ai_result.gps_coords:
            parsed = _parse_gps(r.ai_result.gps_coords)
        if not parsed and r.submission_gps_coords:
            parsed = _parse_gps(r.submission_gps_coords)
        if not parsed:
            continue
        lat, lng = parsed
        vf = r.ai_result.violation_flag if r.ai_result else None
        vt = r.ai_result.violation_type if r.ai_result else None
        out.append(
            MapReportPin(
                report_id=r.report_id,
                lat=lat,
                lng=lng,
                district_location=r.district_location,
                status=r.status,
                violation_flag=vf,
                violation_type=vt,
            )
        )
    return out


@router.get("/reports/timeline")
async def reports_timeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority),
):
    """Reports submitted per day for last 30 days."""
    end_d = datetime.utcnow().date()
    start_d = end_d - timedelta(days=29)
    rows = _scoped_reports_query(db, current_user).all()

    counts: defaultdict[str, int] = defaultdict(int)
    for r in rows:
        if not r.submission_date:
            continue
        d = r.submission_date.date() if isinstance(r.submission_date, datetime) else r.submission_date
        if start_d <= d <= end_d:
            counts[str(d)] += 1

    series = []
    cur = start_d
    while cur <= end_d:
        key = str(cur)
        series.append({"date": key, "count": counts.get(key, 0)})
        cur += timedelta(days=1)
    return {"series": series}


@router.get("/reports/{report_id}/notice", response_class=HTMLResponse)
async def report_notice_html(
    request: Request,
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority),
):
    """Printable / downloadable structured authority screening report (HTML for print or save)."""
    r = _scoped_report_or_404(db, current_user, report_id)
    ctx = build_authority_report_context(r, settings, str(request.base_url))
    return _notice_templates.TemplateResponse(
        "authority_report.html",
        {"request": request, **ctx},
    )


@router.get("/reports", response_model=PaginatedReports)
async def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority),
    status_filter: str | None = Query(None, alias="status"),
    district: str | None = Query(None),
    input_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    q = _scoped_reports_query(db, current_user)
    if status_filter and status_filter != "All":
        q = q.filter(ViolationsReport.status == status_filter)
    if district and district != "All":
        q = q.filter(ViolationsReport.district_location == district)
    if input_type and input_type != "All":
        if input_type.lower() == "street":
            q = q.filter(ViolationsReport.input_type.is_(True))
        elif input_type.lower() == "aerial":
            q = q.filter(ViolationsReport.input_type.is_(False))

    total = q.count()
    offset = (page - 1) * limit
    rows = q.order_by(ViolationsReport.submission_date.desc()).offset(offset).limit(limit).all()

    items: list[AuthorityReportListItem] = []
    for r in rows:
        vt = r.ai_result.violation_type if r.ai_result else None
        vf = r.ai_result.violation_flag if r.ai_result else None
        items.append(
            AuthorityReportListItem(
                report_id=r.report_id,
                submission_date=r.submission_date,
                district_location=r.district_location,
                input_type=r.input_type,
                reporter_type=r.reporter_type,
                status=r.status,
                violation_type=vt,
                violation_flag=vf,
            )
        )
    return PaginatedReports(items=items, total=total, page=page, limit=limit)


@router.get("/reports/{report_id}", response_model=AuthorityReportDetail)
async def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority),
):
    r = _scoped_report_or_404(db, current_user, report_id)
    ai = AIResultPublic.model_validate(r.ai_result) if r.ai_result else None
    return AuthorityReportDetail(
        report_id=r.report_id,
        tracking_id=r.tracking_id,
        submission_date=r.submission_date,
        district_location=r.district_location,
        input_type=r.input_type,
        reporter_type=r.reporter_type,
        status=r.status,
        notes=r.notes,
        ai_result=ai,
    )


@router.patch("/reports/{report_id}/status")
async def patch_report_status(
    report_id: int,
    body: AuthorityStatusPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authority),
):
    r = _scoped_report_or_404(db, current_user, report_id)
    new_status = body.status
    key = (r.status, new_status)
    if key not in ALLOWED_TRANSITIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Invalid status transition", "code": "INVALID_TRANSITION"},
        )
    r.status = new_status
    if body.notes is not None:
        r.notes = body.notes
    r.user_id = current_user.id
    db.commit()
    return {"report_id": report_id, "status": r.status}


@router.get("/districts")
async def authority_districts(current_user: User = Depends(require_authority)):
    if current_user.can_view_all_areas:
        return {"districts": KARACHI_DISTRICTS}
    assigned_area = (current_user.assigned_area or "").strip()
    return {"districts": [assigned_area] if assigned_area else []}
