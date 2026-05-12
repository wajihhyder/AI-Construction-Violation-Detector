import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.dependencies import require_admin
from core.security import get_password_hash
from database import get_db
from models.user import ROLE_ADMIN, ROLE_AUTHORITY, ROLE_DG
from models.report import ViolationsReport
from models.user import User
from schemas.user import UserCreate, UserResponse, UserUpdate
from services.auth_service import normalize_assigned_area, serialize_user, validate_role_assignment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _singleton_role_taken(db: Session, role_name: str) -> bool:
    if role_name not in {ROLE_ADMIN, ROLE_DG}:
        return False
    return any(u.effective_role_name == role_name for u in db.query(User).all())


@router.get("/users", response_model=list[UserResponse])
async def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.query(User).order_by(User.id.asc()).all()
    return [serialize_user(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Username already exists", "code": "DUPLICATE_USERNAME"},
        )
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Email already exists", "code": "DUPLICATE_EMAIL"},
        )
    if _singleton_role_taken(db, body.role_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": f"{body.role_name} account already exists",
                "code": "ROLE_ALREADY_EXISTS",
            },
        )
    try:
        assigned_area = validate_role_assignment(body.role_name, body.assigned_area)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": str(exc), "code": "INVALID_ASSIGNED_AREA"},
        ) from exc
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=get_password_hash(body.password),
        role=body.role_name == ROLE_ADMIN,
        role_name=body.role_name,
        assigned_area=assigned_area,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "User not found", "code": "NOT_FOUND"},
        )
    return serialize_user(u)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "User not found", "code": "NOT_FOUND"},
        )
    current_role = u.effective_role_name
    if body.username is not None:
        other = db.query(User).filter(User.username == body.username, User.id != user_id).first()
        if other:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"detail": "Username already exists", "code": "DUPLICATE_USERNAME"},
            )
        u.username = body.username
    if body.email is not None:
        other = db.query(User).filter(User.email == body.email, User.id != user_id).first()
        if other:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"detail": "Email already exists", "code": "DUPLICATE_EMAIL"},
            )
        u.email = body.email
    if body.password is not None:
        u.hashed_password = get_password_hash(body.password)
    if body.role_name is not None and body.role_name != current_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "User role cannot be changed after creation", "code": "IMMUTABLE_ROLE"},
        )
    if current_role == ROLE_AUTHORITY:
        # Legacy authority users may predate assigned_area; allow unrelated edits until an admin assigns one.
        if body.assigned_area is not None:
            try:
                u.assigned_area = validate_role_assignment(current_role, body.assigned_area)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"detail": str(exc), "code": "INVALID_ASSIGNED_AREA"},
                ) from exc
        else:
            u.assigned_area = normalize_assigned_area(u.assigned_area)
    else:
        u.assigned_area = None
    db.commit()
    db.refresh(u)
    return serialize_user(u)


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "User not found", "code": "NOT_FOUND"},
        )
    if u.effective_role_name in {ROLE_ADMIN, ROLE_DG}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Admin and DG accounts cannot be deleted", "code": "PROTECTED_USER"},
        )
    linked = db.query(ViolationsReport).filter(ViolationsReport.user_id == user_id).first()
    if linked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Cannot delete user with linked reports", "code": "HAS_REPORTS"},
        )
    db.delete(u)
    db.commit()
    return {"message": "User deleted"}
