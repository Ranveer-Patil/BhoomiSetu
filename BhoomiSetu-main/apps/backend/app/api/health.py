import asyncio
from pathlib import Path

from alembic.script import ScriptDirectory
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])
EXPECTED_REVISION = ScriptDirectory(
    str(Path(__file__).resolve().parents[1] / "alembic")
).get_current_head()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="bhoomsetu-api")


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict:
    try:
        result = await asyncio.wait_for(
            db.execute(text("SELECT version_num, PostGIS_Version() FROM alembic_version")),
            timeout=5,
        )
        rows = result.all()
    except Exception:
        raise HTTPException(503, "Database is not ready") from None
    if len(rows) != 1 or rows[0][0] != EXPECTED_REVISION or not rows[0][1]:
        raise HTTPException(503, "Database migration is not ready")
    return {"status": "ready", "service": "bhoomsetu-api", "revision": rows[0][0]}
