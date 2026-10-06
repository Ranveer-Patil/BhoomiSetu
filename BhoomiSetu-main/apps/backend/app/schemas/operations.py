from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import CaseStage, CompensationState, GrievanceStatus

Locale = Literal["en", "hi", "mr", "gu", "kn"]
RRStage = Literal["assessment", "planned", "in_progress", "completed", "not_required"]


class CompensationWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    status: CompensationState
    assessed_amount: Decimal | None = Field(default=None, ge=0, max_digits=16, decimal_places=2)
    disbursed_amount: Decimal | None = Field(default=None, ge=0, max_digits=16, decimal_places=2)
    due_date: date | None = None
    reference: str = Field(min_length=3, max_length=500)

    @model_validator(mode="after")
    def validate_amounts(self):
        if self.disbursed_amount is not None and (
            self.assessed_amount is None or self.disbursed_amount > self.assessed_amount
        ):
            raise ValueError("Disbursed amount cannot exceed the recorded assessed amount")
        if self.status == CompensationState.DISBURSED and (
            self.assessed_amount is None or self.disbursed_amount != self.assessed_amount
        ):
            raise ValueError("Disbursed status requires matching assessed and paid amounts")
        return self


class RRWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    rehabilitation_stage: RRStage
    resettlement_site_assigned: bool = False
    families_supported: int = Field(default=0, ge=0, le=1_000_000)
    notes: str = Field(min_length=3, max_length=500)


class FamilyWrite(BaseModel):
    affected_family_count: int = Field(ge=0, le=1_000_000)
    displaced_family_count: int = Field(ge=0, le=1_000_000)

    @model_validator(mode="after")
    def validate_counts(self):
        if self.displaced_family_count > self.affected_family_count:
            raise ValueError("Displaced families cannot exceed affected families")
        return self


class DeadlineWrite(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    stage: CaseStage
    due_date: date
    basis: Literal["operational", "statutory"]
    reference: str = Field(min_length=5, max_length=500)


class PreferenceWrite(BaseModel):
    locale: Locale


class GrievanceUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    status: GrievanceStatus
    response: str = Field(min_length=3, max_length=4000)
