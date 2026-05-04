import logging
import time

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.convertors import Convertor, register_url_convertor
from pathlib import Path
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import models  # noqa: F401 — register SQLAlchemy models for create_all

from core.config import settings
from core.limiter import limiter
from database import Base, SessionLocal, engine
from routers import admin, auth, authority, citizen, geocoding
from sqlalchemy import inspect, or_, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("construction_violation.access")


class SpaPathConvertor(Convertor[str]):
    """
    SPA history fallback must not match /api/* or /uploads/*.
    Otherwise unknown API paths hit the catch-all and return a misleading JSON 404.
    """

    regex = r"(?!api(?:/|$))(?!uploads(?:/|$)).*"

    def convert(self, value: str) -> str:
        return str(value)

    def to_string(self, value: str) -> str:
        return str(value)


register_url_convertor("spa_path", SpaPathConvertor())


Base.metadata.create_all(bind=engine)


def _ensure_submission_gps_column() -> None:
    """Add submission_gps_coords if missing (SQLAlchemy create_all does not alter existing tables)."""
    try:
        insp = inspect(engine)
        if "violations_report" not in insp.get_table_names():
            return
        names = {c["name"] for c in insp.get_columns("violations_report")}
        if "submission_gps_coords" in names:
            return
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE violations_report ADD COLUMN submission_gps_coords VARCHAR(128)"),
            )
    except Exception as e:
        logger.warning("Schema ensure submission_gps_coords: %s", e)


_ensure_submission_gps_column()


def _ensure_tracking_id_column() -> None:
    """Add tracking_id and backfill if missing (create_all does not alter existing tables)."""
    try:
        from models.report import ViolationsReport

        from core.tracking_id import generate_tracking_id

        insp = inspect(engine)
        if "violations_report" not in insp.get_table_names():
            return
        col_names = {c["name"] for c in insp.get_columns("violations_report")}
        if "tracking_id" not in col_names:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE violations_report ADD COLUMN tracking_id VARCHAR(40)"))
        with SessionLocal() as db:
            for r in (
                db.query(ViolationsReport)
                .filter(
                    or_(
                        ViolationsReport.tracking_id.is_(None),
                        ViolationsReport.tracking_id == "",
                    )
                )
                .all()
            ):
                r.tracking_id = generate_tracking_id(r.report_id, r.submission_date)
            db.commit()
        with engine.begin() as conn:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_violations_report_tracking_id "
                    "ON violations_report (tracking_id)"
                )
            )
    except Exception as e:
        logger.warning("Schema ensure tracking_id: %s", e)


_ensure_tracking_id_column()

app = FastAPI(title="AI Powered Construction Violation Detection API", version="1.0.0")

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.2fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "code": "VALIDATION_ERROR", "errors": exc.errors()},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

app.include_router(auth.router)
app.include_router(citizen.router)
app.include_router(geocoding.router)
app.include_router(authority.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


def _register_spa() -> None:
    if settings.DISABLE_SPA_ON_API:
        return
    dist = settings.resolved_frontend_dist()
    if not dist:
        return
    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="spa_assets")

    @app.get("/")
    async def spa_index():
        return FileResponse(dist / "index.html")

    @app.get("/{full_path:spa_path}")
    async def spa_nested(full_path: str):
        safe_root = dist.resolve()
        candidate = (dist / full_path).resolve()
        try:
            candidate.relative_to(safe_root)
        except ValueError:
            raise HTTPException(status_code=404, detail="Not Found") from None
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist / "index.html")


_register_spa()
