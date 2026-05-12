from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from database import Base

ROLE_ADMIN = "ADMIN"
ROLE_AUTHORITY = "AUTHORITY"
ROLE_DG = "DG"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    # True = Admin, False = Authority
    role = Column(Boolean, nullable=False, default=False)
    role_name = Column(String(32), nullable=True)
    assigned_area = Column(String(128), nullable=True)
    last_login = Column(DateTime, nullable=True)

    reports = relationship("ViolationsReport", back_populates="reviewer")

    @property
    def effective_role_name(self) -> str:
        if self.role_name in {ROLE_ADMIN, ROLE_AUTHORITY, ROLE_DG}:
            return str(self.role_name)
        return ROLE_ADMIN if self.role else ROLE_AUTHORITY

    @property
    def is_admin(self) -> bool:
        return self.effective_role_name == ROLE_ADMIN

    @property
    def is_dg(self) -> bool:
        return self.effective_role_name == ROLE_DG

    @property
    def can_view_all_areas(self) -> bool:
        return self.is_admin or self.is_dg
