import asyncio
import hashlib
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models import AuditLog, User
from app.models.enums import UserRole
from app.schemas.interoperability import (
    AuditLogResponse,
    AuditVerificationResponse,
    DeedResponse,
    FixtureDisclosure,
    LandRecordResponse,
)
from app.services.audit import GENESIS_HASH

router = APIRouter(tags=["interoperability and audit"])
ADMIN_ROLES = (UserRole.DISTRICT_ADMIN, UserRole.SENIOR_ADMIN)


def _fixture_index(value: str) -> int:
    return int(hashlib.sha256(value.encode()).hexdigest()[:4], 16)


@router.get(
    "/integrations/apisetu/land-records/{survey_number}",
    response_model=LandRecordResponse,
)
async def apisetu_land_record(
    survey_number: str,
    _: User = Depends(get_current_user),
) -> LandRecordResponse:
    """API Setu-shaped fixture. This endpoint never returns live government data."""
    await asyncio.sleep(0.4)
    index = _fixture_index(survey_number)
    owners = ["Asha Dattatray Patil", "Vijay Shankar Jadhav", "Meera Sunil Pawar"]
    area = round(0.62 + (index % 70) / 100, 2)
    return LandRecordResponse(
        request_id=uuid.uuid4(),
        source=FixtureDisclosure(intended_provider="API Setu / Maharashtra Bhulekh"),
        state_code="MH",
        district="Pune",
        village="Kharadi",
        survey_number=survey_number.upper(),
        owner={"name": owners[index % len(owners)], "relationship": "recorded holder"},
        area={"value": area, "unit": "hectare"},
        land_use_classification="Agricultural - Jirayat",
        encumbrance={"has_encumbrance": index % 4 == 0, "status": "verified fixture"},
        record_updated_on="2026-08-15",
    )


@router.get("/integrations/apisetu/deeds/{registration_number}", response_model=DeedResponse)
async def apisetu_deed(
    registration_number: str,
    _: User = Depends(get_current_user),
) -> DeedResponse:
    """NGDRS-shaped registration fixture, deliberately and visibly labelled."""
    await asyncio.sleep(0.55)
    return DeedResponse(
        request_id=uuid.uuid4(),
        source=FixtureDisclosure(intended_provider="API Setu / NGDRS"),
        registration_number=registration_number.upper(),
        registration_date="2021-06-18",
        office="Haveli Sub-Registrar Office No. 7, Pune",
        deed_type="Sale Deed",
        parties=[
            {"role": "transferor", "name": "Fixture Person A"},
            {"role": "transferee", "name": "Fixture Person B"},
        ],
        property_reference="Village Kharadi, Taluka Haveli, Pune",
        status="registered_fixture",
    )


@router.get("/audit-log", response_model=list[AuditLogResponse])
async def list_audit_log(
    case_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ROLES)),
) -> list[AuditLog]:
    query = select(AuditLog)
    if case_id:
        query = query.where(AuditLog.action.contains(str(case_id)))
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    return list(await db.scalars(query.order_by(AuditLog.created_at.desc()).limit(limit)))


@router.get("/audit-log/verify", response_model=AuditVerificationResponse)
async def verify_audit_log(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ROLES)),
) -> AuditVerificationResponse:
    rows = list(await db.scalars(select(AuditLog).order_by(AuditLog.created_at, AuditLog.id)))
    previous = GENESIS_HASH
    for index, row in enumerate(rows, start=1):
        material = f"{row.prev_hash}|{row.user_id}|{row.action}|{row.created_at.isoformat()}"
        expected = hashlib.sha256(material.encode()).hexdigest()
        if row.prev_hash != previous or row.row_hash != expected:
            return AuditVerificationResponse(
                valid=False,
                checked_rows=index,
                broken_at_id=row.id,
                message="Hash-chain verification failed",
            )
        previous = row.row_hash
    return AuditVerificationResponse(
        valid=True, checked_rows=len(rows), message="Every audit row and link is intact"
    )
