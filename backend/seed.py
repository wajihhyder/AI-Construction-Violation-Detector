"""
Seed default admin user. Run from backend directory:
  python seed.py
"""
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine

import models  # noqa: F401 — register ORM tables on Base.metadata

from core.security import get_password_hash
from models.user import User


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if db.query(User).filter(User.username == "admin").first():
            print("Admin user already exists — skipping.")
            return
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("Admin@1234"),
            role=True,
        )
        db.add(admin)
        db.commit()
        print("Seeded admin: username=admin password=Admin@1234")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
