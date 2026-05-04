from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    # True = Admin, False = Authority
    role = Column(Boolean, nullable=False, default=False)
    last_login = Column(DateTime, nullable=True)

    reports = relationship("ViolationsReport", back_populates="reviewer")
