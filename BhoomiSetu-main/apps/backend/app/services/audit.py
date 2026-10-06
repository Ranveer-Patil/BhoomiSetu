import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog

GENESIS_HASH = "0" * 64
AUDIT_LOCK_KEY = 26016


async def write_audit_log(db: AsyncSession, user_id: uuid.UUID, action: str) -> AuditLog:
    # A transaction-level lock prevents two concurrent requests from creating
    # competing links from the same previous hash.
    await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": AUDIT_LOCK_KEY})
    previous = await db.scalar(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(1))
    prev_hash = previous.row_hash if previous else GENESIS_HASH
    created_at = datetime.now(UTC)
    digest_input = f"{prev_hash}|{user_id}|{action}|{created_at.isoformat()}"
    row_hash = hashlib.sha256(digest_input.encode()).hexdigest()
    row = AuditLog(
        user_id=user_id,
        action=action,
        prev_hash=prev_hash,
        row_hash=row_hash,
        created_at=created_at,
    )
    db.add(row)
    return row
