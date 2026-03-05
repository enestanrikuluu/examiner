from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.redis import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    db_ok = False
    redis_ok = False
    storage_ok = True  # MinIO check is sync, skip in health for speed

    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        redis = await get_redis()
        await redis.ping()
        redis_ok = True
    except Exception:
        pass

    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "db": db_ok,
        "redis": redis_ok,
        "storage": storage_ok,
    }


@router.get("/health/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    try:
        await db.execute(text("SELECT 1"))
        redis = await get_redis()
        await redis.ping()
        return {"ready": True}
    except Exception:
        return {"ready": False}
