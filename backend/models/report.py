from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class ViolationsReport(Base):
    __tablename__ = "violations_report"

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    tracking_id = Column(String(40), nullable=False, unique=True, index=True)
    submission_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    district_location = Column(String, nullable=False)
    # True = Street View, False = Aerial
    input_type = Column(Boolean, nullable=True)
    ai_result_id = Column(Integer, ForeignKey("ai_analysis_result.result_id"), nullable=True)
    reporter_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="New")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(String, nullable=True)
    # GPS from EXIF or client at submit (used if file re-read fails; avoids static DEFAULT_GPS)
    submission_gps_coords = Column(String(128), nullable=True)

    reviewer = relationship("User", back_populates="reports")
    ai_result = relationship(
        "AIAnalysisResult",
        back_populates="report",
        foreign_keys=[ai_result_id],
        uselist=False,
    )
