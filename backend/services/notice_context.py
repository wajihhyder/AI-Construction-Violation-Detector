"""
Build Jinja context for the printable Show Cause–style notice (neutral wording; no authority branding).
"""
from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urljoin

from models.report import ViolationsReport


def _district_slug(district: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", district.strip())
    s = s.strip("-").upper()[:24]
    return s or "KARACHI"


def _fmt_date(dt: datetime | None) -> str:
    if dt is None:
        return "_______________"
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    return dt.strftime("%d %B %Y")


def build_notice_context(report: ViolationsReport, settings) -> dict:
    ai = report.ai_result
    submitted = report.submission_date
    year = submitted.year if submitted else datetime.utcnow().year
    ref = f"VIO/{_district_slug(report.district_location)}/{year}/{report.report_id:05d}"

    vt = ai.violation_type if ai else None
    vflag = bool(ai and ai.violation_flag)

    if vt == "Extra_Floor":
        subject = (
            "UNAUTHORIZED ADDITIONAL STOREYS / EXTRA FLOOR CONSTRUCTION ALLEGEDLY IN EXCESS "
            "OF PERMITTED HEIGHT OR APPROVED PLANS."
        )
        whereas_b = [
            (
                "Whereas, a citizen/field report concerning the subject premises indicates that the "
                "standing structure may comprise additional storeys or built-up area beyond what is "
                "permitted for the zoning/plot category in the cited district."
            ),
            (
                "Whereas, visual review of the submitted evidence suggests the structure may include "
                f"approximately {ai.detected_floors if ai and ai.detected_floors is not None else '___'} "
                "storeys (indicative), subject to physical verification on site."
            ),
        ]
    elif vt == "Setback_Breach":
        subject = (
            "SETBACK / COVERAGE VIOLATION — ALLEGED NON-COMPLIANCE WITH REQUIRED YARDS OR BUILDING LINE."
        )
        err = ai.setback_error if ai else None
        whereas_b = [
            (
                "Whereas, the submitted imagery/analysis indicates a possible shortfall in front/side/rear "
                "setback or yard dimensions relative to applicable plot regulations for the district."
            ),
            (
                f"Whereas, the indicative deviation noted in the screening is on the order of "
                f"{err} metres (subject to survey), pending verification by site measurement."
                if err is not None
                else "Whereas, further measured survey is required to confirm setback compliance."
            ),
        ]
    elif vt in {
        "Encroachment",
        "Road_Encroachment",
        "Public_Space_Encroachment",
        "Water_Encroachment",
        "Unmapped_Construction",
    }:
        subject = (
            "ENCROACHMENT / UNAUTHORIZED EXTENSION — ALLEGED PROJECTION BEYOND LEGAL BOUNDARY OR PUBLIC ROW."
        )
        whereas_b = [
            (
                "Whereas, the submitted materials suggest occupation or construction projecting beyond the "
                "legal plot boundary or into public easement / street line."
            ),
            (
                "Whereas, such projection, if confirmed on inspection, would constitute unauthorized "
                "encroachment liable to regulatory action under applicable municipal provisions."
            ),
        ]
    else:
        if vflag:
            subject = "ALLEGED CONSTRUCTION / DEVELOPMENT IRREGULARITY REPORTED FOR THE SUBJECT PREMISES."
            whereas_b = [
                (
                    "Whereas, a screening report has been registered concerning potential irregularities "
                    "at the subject location within the stated district."
                ),
                (
                    "Whereas, the particulars (including coordinates and imagery on record) warrant "
                    "explanation and compliance verification before further enforcement steps are considered."
                ),
            ]
        else:
            subject = "REPORTED CONSTRUCTION ACTIVITY — INFORMATION REQUEST / VERIFICATION."
            whereas_b = [
                (
                    "Whereas, information concerning construction activity at the subject premises has "
                    "been placed on record for administrative review."
                ),
                (
                    "Whereas, it is necessary to obtain your written explanation and supporting documents "
                    "to determine conformity with applicable building and zoning requirements."
                ),
            ]

    ordinance_quote = [
        (
            "No building shall, except with the written permission of the competent authority, be used for "
            "a purpose other than that for which its plans were approved or permitted."
        ),
        (
            "No building shall be occupied before an occupancy or completion certificate is issued where "
            "such certificate is required under applicable rules."
        ),
    ]

    office1 = settings.NOTICE_OFFICE_LINE1.strip() or "_______________________________________________"
    office2 = settings.NOTICE_OFFICE_LINE2.strip() or "_______________________________________________"
    contact = settings.NOTICE_CONTACT_LINE.strip() or "Tel: _______________   Email: _______________"

    gps = ai.gps_coords if ai else "—"
    input_lbl = "Street view" if report.input_type else "Aerial / satellite" if report.input_type is False else "—"

    addressee_lines = [
        "M/s. _______________________________________________,",
        f"Site reference — Report No. {report.report_id:05d}, {report.district_location},",
        "Karachi.",
    ]

    return {
        "ref_no": ref,
        "report_id_padded": f"{report.report_id:05d}",
        "dated": _fmt_date(submitted),
        "office_line1": office1,
        "office_line2": office2,
        "contact_line": contact,
        "notice_title": "Show Cause Notice",
        "recipient_label": "(Owner / Attorney / Tenant)",
        "addressee_lines": addressee_lines,
        "subject": subject,
        "whereas_blocks": whereas_b,
        "ordinance_quote": ordinance_quote,
        "direction": (
            "In view of the foregoing, you are hereby directed to cease any continuing irregular activity "
            "forthwith (where applicable) and to show cause in writing why regulatory action — including "
            "sealing, demolition of unauthorized portions, and initiation of proceedings as permissible "
            "under law — should not be taken. Your reply must reach this office, together with supporting "
            "documents and approvals, within the period stated below."
        ),
        "reply_days": settings.NOTICE_REPLY_DAYS,
        "signature_title": "Authorized Officer",
        "report_id": report.report_id,
        "district": report.district_location,
        "gps_coords": gps,
        "input_label": input_lbl,
        "reporter_type": report.reporter_type,
        "status": report.status,
        "notes": (report.notes or "").strip(),
    }


def _fmt_violation_type_label(v: str | None) -> str:
    if not v:
        return "—"
    return str(v).replace("_", " ")


def _executive_summary(report: ViolationsReport, ai) -> str:
    d = report.district_location
    rid = report.report_id
    if not ai:
        return (
            f"This record documents report #{rid:05d} concerning premises in {d}. "
            "Automated screening output was not yet attached when this report was generated; "
            "confirm current workflow status in this system before enforcement steps."
        )
    if ai.violation_type == "Manual_Review":
        return (
            f"Report #{rid:05d} in {d} was routed for manual review. "
            "The configured automated model screens street-view floor counts only, "
            "so aerial setback or encroachment checks still require staff verification."
        )
    if ai.violation_flag:
        vt = _fmt_violation_type_label(ai.violation_type)
        return (
            f"Screening flagged a potential irregularity ({vt}) for report #{rid:05d} in {d}. "
            "Independent site verification and documentary checks are recommended prior to formal notice."
        )
    return (
        f"Screening did not flag a violation for report #{rid:05d} in {d}. "
        "Administrative confirmation may still be required where citizen complaints remain open."
    )


def _follow_up_guidance(status: str) -> str:
    return {
        "New": "Route for desk review and prioritisation; schedule field verification if screening indicates risk.",
        "Under_Review": "Continue verification; seek owner or occupier representations where applicable.",
        "Verified": "Maintain verified record; initiate regulatory steps only per competent authority approval.",
        "Invalid": "Retain audit trail; close screening thread unless new evidence is filed.",
        "Processing": "Defer formal directions until automated screening completes and record status updates.",
    }.get(
        status,
        "Proceed according to departmental standard operating procedures and supervisory instructions.",
    )


def build_authority_report_context(report: ViolationsReport, settings, base_url: str | None = None) -> dict:
    """
    Context for printable/downloadable general authority report (structured sections, tabular data).
    """
    ai = report.ai_result
    submitted = report.submission_date
    year = submitted.year if submitted else datetime.utcnow().year
    ref = f"VIO/{_district_slug(report.district_location)}/{year}/{report.report_id:05d}"

    gps = "—"
    if ai and ai.gps_coords:
        gps = str(ai.gps_coords).strip() or "—"
    elif getattr(report, "submission_gps_coords", None):
        gps = str(report.submission_gps_coords).strip() or "—"

    input_lbl = "Street view" if report.input_type else "Aerial / satellite" if report.input_type is False else "—"

    if ai:
        screening_state = "Completed"
        vflag_lbl = "Yes" if ai.violation_flag else "No"
        vtype = _fmt_violation_type_label(ai.violation_type)
        floors = str(ai.detected_floors) if ai.detected_floors is not None else "—"
        setback = f"{float(ai.setback_error):.4g}" if ai.setback_error is not None else "—"
        evidence_path = (ai.image_evidence_path or "").strip() or "—"
        if ai.violation_type == "Manual_Review":
            screening_state = "Manual review required"
            vflag_lbl = "Pending manual review"
    else:
        screening_state = "Pending"
        vflag_lbl = "Pending"
        vtype = "—"
        floors = "—"
        setback = "—"
        evidence_path = "Pending AI attachment"

    office1 = settings.NOTICE_OFFICE_LINE1.strip() or "_______________________________________________"
    office2 = settings.NOTICE_OFFICE_LINE2.strip() or "_______________________________________________"
    contact = settings.NOTICE_CONTACT_LINE.strip() or "Tel: _______________   Email: _______________"

    identification_rows = [
        ("Reference number", ref),
        ("Report number", f"{report.report_id:05d}"),
        ("Date filed", _fmt_date(submitted)),
        ("District", report.district_location),
        ("Workflow status", report.status.replace("_", " ")),
    ]

    screening_rows = [
        ("Screening run", screening_state),
        ("Violation flagged", vflag_lbl),
        ("Screening classification", vtype),
        ("Detected floors (indicative)", floors),
        ("Setback deviation (m, indicative)", setback),
    ]

    hint = ""
    evidence_image_url: str | None = None
    if evidence_path.startswith("/uploads/"):
        hint = (
            "Evidence is stored on the application server under this path; open from the authority dashboard "
            "image viewer when connected to the same deployment."
        )
        if base_url:
            evidence_image_url = urljoin(base_url.rstrip("/") + "/", evidence_path.lstrip("/"))

    return {
        "report_title": "Authority Screening Report",
        "ref_no": ref,
        "report_id_padded": f"{report.report_id:05d}",
        "dated": _fmt_date(submitted),
        "office_line1": office1,
        "office_line2": office2,
        "contact_line": contact,
        "identification_rows": identification_rows,
        "gps_coords": gps,
        "input_label": input_lbl,
        "reporter_type": report.reporter_type,
        "executive_summary": _executive_summary(report, ai),
        "screening_rows": screening_rows,
        "evidence_path": evidence_path,
        "evidence_image_url": evidence_image_url,
        "evidence_url_hint": hint,
        "notes": (report.notes or "").strip(),
        "follow_up_guidance": _follow_up_guidance(report.status),
        "signature_title": "Authorized Officer",
        "district": report.district_location,
        "report_id": report.report_id,
        "status": report.status.replace("_", " "),
    }
