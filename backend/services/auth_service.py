from sqlalchemy.orm import Session

from core.security import decode_token
from models.user import ROLE_ADMIN, ROLE_AUTHORITY, ROLE_DG, User
from schemas.user import LoginResponse, UserResponse


def normalize_assigned_area(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def validate_role_assignment(role_name: str, assigned_area: str | None) -> str | None:
    area = normalize_assigned_area(assigned_area)
    if role_name == ROLE_AUTHORITY:
        if not area:
            raise ValueError("Authority users must have an assigned area.")
        return area
    return None


def effective_role_name(user: User) -> str:
    return user.effective_role_name


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.is_admin,
        role_name=user.effective_role_name,
        assigned_area=normalize_assigned_area(user.assigned_area),
        last_login=user.last_login,
    )


def serialize_login(user: User, access_token: str) -> LoginResponse:
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.is_admin,
        role_name=user.effective_role_name,
        assigned_area=normalize_assigned_area(user.assigned_area),
        username=user.username,
        user_id=user.id,
    )


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
