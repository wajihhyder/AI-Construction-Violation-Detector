from sqlalchemy.orm import Session

from core.security import decode_token
from models.user import User


def get_user_by_id_from_token(db: Session, token: str) -> User | None:
    payload = decode_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None
    return db.query(User).filter(User.id == uid).first()


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    from core.security import verify_password

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
