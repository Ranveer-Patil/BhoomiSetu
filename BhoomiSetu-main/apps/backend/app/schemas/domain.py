import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import CaseStage, ProjectStatus
from app.services.master_data import PROJECT_TYPES, validate_survey_number


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    project_type: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    district: str = Field(min_length=2, max_length=100)
    status: ProjectStatus = ProjectStatus.DRAFT

    @field_validator("project_type")
    @classmethod
    def standard_project_type(cls, value: str) -> str:
        canonical = next(
            (item for item in PROJECT_TYPES if item.lower() == value.strip().lower()), None
        )
        if canonical is None:
            raise ValueError("Choose a project type from master data")
        return canonical


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    project_type: str
    state: str
    district: str
    status: ProjectStatus
    created_at: datetime


class ParcelCreate(BaseModel):
    khasra_survey_no: str = Field(min_length=1, max_length=100)
    polygon: list[list[list[float]]]

    _survey_validator = field_validator("khasra_survey_no")(validate_survey_number)

    @field_validator("polygon")
    @classmethod
    def validate_polygon(cls, value: list[list[list[float]]]) -> list[list[list[float]]]:
        if not value or len(value[0]) < 4:
            raise ValueError("A polygon needs at least four coordinate points")
        for ring in value:
            if len(ring) < 4:
                raise ValueError("Every ring needs at least four points")
            if any(len(point) != 2 for point in ring):
                raise ValueError("Each coordinate must contain longitude and latitude")
            if any(not (-180 <= p[0] <= 180 and -90 <= p[1] <= 90) for p in ring):
                raise ValueError("Coordinates must be valid longitude and latitude")
            if len({tuple(p) for p in ring}) < 3:
                raise ValueError("A polygon needs three distinct points")
            if ring[0] != ring[-1]:
                raise ValueError("Each polygon ring must be closed")
        return value


class ParcelResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    khasra_survey_no: str
    polygon: dict[str, Any]


class LandownerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    contact: str = Field(min_length=3, max_length=120)
    user_id: uuid.UUID | None = None


class LandownerResponse(LandownerCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parcel_id: uuid.UUID


class CaseCreate(BaseModel):
    parcel_id: uuid.UUID
    assigned_officer_id: uuid.UUID | None = None
    affected_family_count: int = Field(default=0, ge=0, le=1_000_000)


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parcel_id: uuid.UUID
    current_stage: CaseStage
    assigned_officer_id: uuid.UUID | None
    affected_family_count: int
    displaced_family_count: int = 0
    created_at: datetime


class StageHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_stage: CaseStage
    to_stage: CaseStage
    changed_by: uuid.UUID
    reason: str | None
    changed_at: datetime


class CaseDetailResponse(CaseResponse):
    stage_history: list[StageHistoryResponse] = []


class CaseTransitionRequest(BaseModel):
    new_stage: CaseStage
    reason: str | None = Field(default=None, max_length=500)
