from enum import StrEnum


class UserRole(StrEnum):
    LANDOWNER = "landowner"
    OFFICER = "officer"
    PROJECT_AUTHORITY = "project_authority"
    DISTRICT_ADMIN = "district_admin"
    SENIOR_ADMIN = "senior_admin"


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class CaseStage(StrEnum):
    NOTIFICATION = "notification"
    VERIFICATION = "verification"
    OBJECTION = "objection"
    AWARD = "award"
    COMPENSATION = "compensation"
    POSSESSION = "possession"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    EXTRACTED = "extracted"
    VERIFIED = "verified"
    REJECTED = "rejected"


class GrievanceStatus(StrEnum):
    OPEN = "open"
    ASSIGNED = "assigned"
    RESOLVED = "resolved"


class CompensationState(StrEnum):
    ASSESSED = "assessed"
    APPROVED = "approved"
    DISBURSED = "disbursed"
