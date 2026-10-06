import uuid
from datetime import datetime

from pydantic import BaseModel


class FixtureDisclosure(BaseModel):
    is_fixture: bool = True
    notice: str = "Prototype fixture — not live government data"
    intended_provider: str


class LandRecordResponse(BaseModel):
    request_id: uuid.UUID
    source: FixtureDisclosure
    state_code: str
    district: str
    village: str
    survey_number: str
    owner: dict[str, str]
    area: dict[str, float | str]
    land_use_classification: str
    encumbrance: dict[str, str | bool]
    record_updated_on: str


class DeedResponse(BaseModel):
    request_id: uuid.UUID
    source: FixtureDisclosure
    registration_number: str
    registration_date: str
    office: str
    deed_type: str
    parties: list[dict[str, str]]
    property_reference: str
    status: str


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    prev_hash: str
    row_hash: str
    created_at: datetime


class AuditVerificationResponse(BaseModel):
    valid: bool
    checked_rows: int
    broken_at_id: uuid.UUID | None = None
    message: str
