import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentExtractedFields(BaseModel):
    owner_name: str | None = None
    khasra_survey_number: str | None = None
    area_hectares: float | None = Field(default=None, ge=0)
    document_type: str | None = None
    document_date: str | None = None
    confidence: float = Field(ge=0, le=1)
    extraction_method: Literal["vision_llm", "tesseract_ocr"]
    raw_text_excerpt: str = Field(max_length=500)


class DocumentExtractionResponse(BaseModel):
    document_id: uuid.UUID
    status: str
    fields: DocumentExtractedFields


class DocumentConfirmationRequest(BaseModel):
    fields: dict[str, Any]
    approved: bool = True


class GrievanceCreateRequest(BaseModel):
    description: str = Field(min_length=10, max_length=4000)


class GrievanceClassification(BaseModel):
    category: Literal["compensation", "ownership", "measurement", "rehabilitation", "process"]
    priority: Literal["low", "medium", "high", "urgent"]
    suggested_department: str
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(max_length=300)


class GrievanceResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    classification: GrievanceClassification
    human_confirmation_required: bool = True


class GrievanceConfirmationRequest(BaseModel):
    category: Literal["compensation", "ownership", "measurement", "rehabilitation", "process"]
    priority: Literal["low", "medium", "high", "urgent"]
    department: str = Field(min_length=3, max_length=120)


class FeatureContribution(BaseModel):
    feature: str
    importance: float


class PredictionResponse(BaseModel):
    predicted_days_remaining: int
    risk_band: Literal["low", "medium", "high"]
    top_features: list[FeatureContribution]
    model_version: str = "phase3-rf-v2"
    training_data: Literal["synthetic"] = "synthetic"
    validated_on_real_data: bool = False
    holdout_mae_days: float


class AggregatePredictionResponse(BaseModel):
    case_count: int
    high_risk_pct: float
    avg_disbursal_days: float
    trend: Literal["up", "stable", "down"]


class SpatialParcelResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    khasra_survey_no: str
    polygon: dict[str, Any]
