from pydantic import BaseModel


class AIResultInternal(BaseModel):
    violation_flag: bool
    violation_type: str | None
    detected_floors: int | None
    setback_error: float | None
    image_evidence_path: str
