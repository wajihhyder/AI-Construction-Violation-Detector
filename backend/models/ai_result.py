from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class AIAnalysisResult(Base):
    __tablename__ = "ai_analysis_result"

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    gps_coords = Column(String, nullable=False)
    violation_flag = Column(Boolean, nullable=False, default=False)
    violation_type = Column(String, nullable=True)
    detected_floors = Column(Integer, nullable=True)
    setback_error = Column(Float, nullable=True)
    image_evidence_path = Column(String, nullable=False)
    # Aerial encroachment screening — total m² and per-category JSON breakdown.
    encroachment_total_m2 = Column(Float, nullable=True)
    encroachment_breakdown = Column(Text, nullable=True)

    report = relationship("ViolationsReport", back_populates="ai_result", uselist=False)
