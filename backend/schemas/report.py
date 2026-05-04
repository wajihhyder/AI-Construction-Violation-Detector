from datetime import datetime

from pydantic import BaseModel, Field


class AIResultPublic(BaseModel):
    violation_flag: bool
    violation_type: str | None
    detected_floors: int | None
    setback_error: float | None
    gps_coords: str
    image_evidence_path: str

    model_config = {"from_attributes": True}


class CitizenReportSubmitResponse(BaseModel):
    report_id: int
    tracking_id: str
    status: str
    message: str
    gps_coords: str | None = None
    detected_district: str | None = None


class CitizenReportPollResponse(BaseModel):
    report_id: int
    tracking_id: str
    status: str
    district_location: str | None = None
    input_type: bool | None = None
    submission_date: datetime | None = None
    reporter_type: str
    ai_result: AIResultPublic | None = None


class DistrictPatch(BaseModel):
    district_location: str = Field(min_length=1)


class AuthorityStatusPatch(BaseModel):
    status: str
    notes: str | None = None


class AuthorityReportListItem(BaseModel):
    report_id: int
    submission_date: datetime
    district_location: str
    input_type: bool | None
    reporter_type: str
    status: str
    violation_type: str | None
    violation_flag: bool | None


class AuthorityReportDetail(BaseModel):
    report_id: int
    submission_date: datetime
    district_location: str
    input_type: bool | None
    reporter_type: str
    status: str
    notes: str | None
    ai_result: AIResultPublic | None

    model_config = {"from_attributes": True}


class StatsResponse(BaseModel):
    total: int
    by_status: dict[str, int]
    by_violation_type: dict[str, int]
    compliant: int


class MapReportPin(BaseModel):
    report_id: int
    lat: float
    lng: float
    district_location: str
    status: str
    violation_flag: bool | None
    violation_type: str | None


class PaginatedReports(BaseModel):
    items: list[AuthorityReportListItem]
    total: int
    page: int
    limit: int
