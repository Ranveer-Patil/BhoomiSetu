import uuid

from fastapi import HTTPException
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AcquisitionCase, Landowner, User
from app.models.enums import UserRole


def scope_case_query(query, actor: User):
    """Apply row-level visibility without leaking whether another role's case exists."""
    if actor.role == UserRole.LANDOWNER:
        query = query.where(
            exists(
                select(Landowner.id).where(
                    Landowner.parcel_id == AcquisitionCase.parcel_id,
                    Landowner.user_id == actor.id,
                )
            )
        )
    elif actor.role == UserRole.OFFICER:
        query = query.where(AcquisitionCase.assigned_officer_id == actor.id)
    return query


async def accessible_case_or_404(
    db: AsyncSession,
    case_id: uuid.UUID,
    actor: User,
    *,
    for_update: bool = False,
) -> AcquisitionCase:
    query = scope_case_query(
        select(AcquisitionCase).where(AcquisitionCase.id == case_id), actor
    )
    if for_update:
        query = query.with_for_update()
    acquisition_case = await db.scalar(query)
    if acquisition_case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return acquisition_case
