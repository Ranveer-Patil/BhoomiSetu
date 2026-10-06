import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import (
    CaseStage,
    CompensationState,
    DocumentStatus,
    GrievanceStatus,
    ProjectStatus,
    UserRole,
)


class UUIDPrimaryKey:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class User(UUIDPrimaryKey, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    locale: Mapped[str] = mapped_column(String(10), default="en", server_default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Project(UUIDPrimaryKey, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200))
    project_type: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100), index=True)
    district: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"), default=ProjectStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcels: Mapped[list["Parcel"]] = relationship(back_populates="project")


class Parcel(UUIDPrimaryKey, Base):
    __tablename__ = "parcels"
    __table_args__ = (UniqueConstraint("project_id", "khasra_survey_no"),)

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    khasra_survey_no: Mapped[str] = mapped_column(String(100), index=True)
    polygon: Mapped[Any] = mapped_column(Geometry("POLYGON", srid=4326, spatial_index=True))

    project: Mapped[Project] = relationship(back_populates="parcels")
    landowners: Mapped[list["Landowner"]] = relationship(back_populates="parcel")
    acquisition_case: Mapped["AcquisitionCase | None"] = relationship(back_populates="parcel")


class Landowner(UUIDPrimaryKey, Base):
    __tablename__ = "landowners"

    parcel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("parcels.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120))
    contact: Mapped[str] = mapped_column(String(120))

    parcel: Mapped[Parcel] = relationship(back_populates="landowners")


class AcquisitionCase(UUIDPrimaryKey, Base):
    __tablename__ = "cases"

    parcel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("parcels.id", ondelete="CASCADE"), unique=True
    )
    current_stage: Mapped[CaseStage] = mapped_column(
        Enum(CaseStage, name="case_stage"), default=CaseStage.NOTIFICATION, index=True
    )
    assigned_officer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    affected_family_count: Mapped[int] = mapped_column(Integer, default=0)
    displaced_family_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcel: Mapped[Parcel] = relationship(back_populates="acquisition_case")
    stage_history: Mapped[list["CaseStageHistory"]] = relationship(
        back_populates="acquisition_case", order_by="CaseStageHistory.changed_at"
    )


class CaseStageHistory(UUIDPrimaryKey, Base):
    __tablename__ = "case_stage_history"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    from_stage: Mapped[CaseStage] = mapped_column(Enum(CaseStage, name="case_stage"))
    to_stage: Mapped[CaseStage] = mapped_column(Enum(CaseStage, name="case_stage"))
    changed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    acquisition_case: Mapped[AcquisitionCase] = relationship(back_populates="stage_history")


class Document(UUIDPrimaryKey, Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("case_id", "version"),)

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )
    file_url: Mapped[str] = mapped_column(String(500))
    document_type: Mapped[str] = mapped_column(
        String(50), default="land_record", server_default="land_record"
    )
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    extracted_fields: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"), default=DocumentStatus.PENDING
    )


class Grievance(UUIDPrimaryKey, Base):
    __tablename__ = "grievances"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(100))
    priority: Mapped[str] = mapped_column(String(30))
    department: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[GrievanceStatus] = mapped_column(
        Enum(GrievanceStatus, name="grievance_status"), default=GrievanceStatus.OPEN
    )


class CompensationStatus(UUIDPrimaryKey, Base):
    __tablename__ = "compensation_status"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), unique=True
    )
    status: Mapped[CompensationState] = mapped_column(
        Enum(CompensationState, name="compensation_state"), default=CompensationState.ASSESSED
    )
    assessed_amount: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), nullable=True)
    disbursed_amount: Mapped[Decimal | None] = mapped_column(Numeric(16, 2), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reference: Mapped[str] = mapped_column(String(500), default="", server_default="")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RRStatus(UUIDPrimaryKey, Base):
    __tablename__ = "rr_status"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), unique=True
    )
    rehabilitation_stage: Mapped[str] = mapped_column(String(100))
    resettlement_site_assigned: Mapped[bool] = mapped_column(Boolean, default=False)
    families_supported: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    notes: Mapped[str] = mapped_column(String(500), default="", server_default="")
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CaseDeadline(UUIDPrimaryKey, Base):
    __tablename__ = "case_deadlines"
    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[CaseStage] = mapped_column(Enum(CaseStage, name="case_stage"))
    due_date: Mapped[date] = mapped_column(Date)
    basis: Mapped[str] = mapped_column(String(30))
    reference: Mapped[str] = mapped_column(String(500))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlertReceipt(UUIDPrimaryKey, Base):
    __tablename__ = "alert_receipts"
    __table_args__ = (UniqueConstraint("user_id", "alert_key"),)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    alert_key: Mapped[str] = mapped_column(String(200))
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(UUIDPrimaryKey, Base):
    __tablename__ = "audit_log"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(Text)
    prev_hash: Mapped[str] = mapped_column(String(64))
    row_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
