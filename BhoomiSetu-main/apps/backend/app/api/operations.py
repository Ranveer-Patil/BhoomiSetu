import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from geoalchemy2 import Geography
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models import (
    AcquisitionCase,
    CaseStageHistory,
    CompensationStatus,
    Document,
    Grievance,
    Parcel,
    Project,
    RRStatus,
    User,
)
from app.models.domain import AlertReceipt, CaseDeadline
from app.models.enums import CaseStage, UserRole
from app.schemas.operations import (
    CompensationWrite,
    DeadlineWrite,
    FamilyWrite,
    GrievanceUpdate,
    PreferenceWrite,
    RRWrite,
)
from app.services.audit import write_audit_log
from app.services.case_access import accessible_case_or_404, scope_case_query
from app.services.master_data import DOCUMENT_TYPES, GRIEVANCE_CATEGORIES, PROJECT_TYPES
from app.services.monitoring import STAGE_TARGET_DAYS, build_alerts, india_today
from app.services.reporting import (
    csv_text,
    grouped_summaries,
    monthly_trend,
    reporting_rows,
    summarize,
)

router = APIRouter(tags=["operations, reporting and alerts"])
MANAGERS = (UserRole.PROJECT_AUTHORITY, UserRole.DISTRICT_ADMIN, UserRole.SENIOR_ADMIN)
STAFF = (UserRole.OFFICER, *MANAGERS)


def record(value):
    if value is None:
        return None
    return jsonable_encoder(
        {column.name: getattr(value, column.name) for column in value.__table__.columns},
        custom_encoder={Decimal: str},
    )


@router.get("/master-data")
async def master_data():
    return {
        "project_types": PROJECT_TYPES,
        "document_types": DOCUMENT_TYPES,
        "grievance_categories": GRIEVANCE_CATEGORIES,
        "stages": list(CaseStage),
        "rr_stages": ["assessment", "planned", "in_progress", "completed", "not_required"],
        "locales": ["en", "hi", "mr", "gu", "kn"],
        "operational_stage_targets_days": STAGE_TARGET_DAYS,
        "notice": (
            "Operational targets are prototype review thresholds, not statutory limits. "
            "Survey format checks do not verify ownership."
        ),
    }


@router.get("/me/preferences")
async def get_preferences(actor: User = Depends(get_current_user)):
    return {"locale": actor.locale}


@router.put("/me/preferences")
async def save_preferences(
    payload: PreferenceWrite | None = None,
    accept_language: str = Header(default="en"),
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    preferred = accept_language.split(",")[0].split(";")[0].split("-")[0].lower()
    actor.locale = (
        payload.locale
        if payload
        else preferred
        if preferred in ("en", "hi", "mr", "gu", "kn")
        else "en"
    )
    await db.commit()
    return {"locale": actor.locale}


@router.get("/cases/{case_id}/operations")
async def case_operations(
    case_id: uuid.UUID, db: AsyncSession = Depends(get_db), actor: User = Depends(get_current_user)
):
    case = await accessible_case_or_404(db, case_id, actor)
    compensation = await db.scalar(
        select(CompensationStatus).where(CompensationStatus.case_id == case_id)
    )
    rr = await db.scalar(select(RRStatus).where(RRStatus.case_id == case_id))
    documents = list(
        await db.scalars(
            select(Document).where(Document.case_id == case_id).order_by(Document.version.desc())
        )
    )
    grievances = list(
        await db.scalars(
            select(Grievance)
            .where(Grievance.case_id == case_id)
            .order_by(Grievance.created_at.desc().nulls_last())
        )
    )
    deadlines = list(
        await db.scalars(
            select(CaseDeadline)
            .where(CaseDeadline.case_id == case_id)
            .order_by(CaseDeadline.due_date)
        )
    )
    return {
        "compensation": record(compensation),
        "rr": record(rr),
        "affected_family_count": case.affected_family_count,
        "displaced_family_count": case.displaced_family_count,
        "documents": [record(row) for row in documents],
        "grievances": [record(row) for row in grievances],
        "deadlines": [record(row) for row in deadlines],
    }


@router.get("/cases/{case_id}/compensation")
async def get_compensation(
    case_id: uuid.UUID, db: AsyncSession = Depends(get_db), actor: User = Depends(get_current_user)
):
    await accessible_case_or_404(db, case_id, actor)
    return record(
        await db.scalar(select(CompensationStatus).where(CompensationStatus.case_id == case_id))
    )


@router.put("/cases/{case_id}/compensation")
async def save_compensation(
    case_id: uuid.UUID,
    payload: CompensationWrite,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*MANAGERS)),
):
    await accessible_case_or_404(db, case_id, actor, for_update=True)
    item = await db.scalar(select(CompensationStatus).where(CompensationStatus.case_id == case_id))
    if item is None:
        item = CompensationStatus(case_id=case_id)
        db.add(item)
    before = record(item) if item.id else None
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    item.updated_at = datetime.now(UTC)
    await db.flush()
    await write_audit_log(
        db,
        actor.id,
        f"compensation.save:{case_id}:"
        + json.dumps({"before": before, "after": record(item)}, sort_keys=True),
    )
    await db.commit()
    return record(item)


@router.get("/cases/{case_id}/rr")
async def get_rr(
    case_id: uuid.UUID, db: AsyncSession = Depends(get_db), actor: User = Depends(get_current_user)
):
    await accessible_case_or_404(db, case_id, actor)
    return record(await db.scalar(select(RRStatus).where(RRStatus.case_id == case_id)))


@router.put("/cases/{case_id}/rr")
async def save_rr(
    case_id: uuid.UUID,
    payload: RRWrite,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*MANAGERS)),
):
    case = await accessible_case_or_404(db, case_id, actor, for_update=True)
    if payload.families_supported > case.affected_family_count:
        raise HTTPException(422, "Supported families cannot exceed affected families")
    item = await db.scalar(select(RRStatus).where(RRStatus.case_id == case_id))
    if item is None:
        item = RRStatus(case_id=case_id)
        db.add(item)
    before = record(item) if item.id else None
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    item.updated_at = datetime.now(UTC)
    await db.flush()
    await write_audit_log(
        db,
        actor.id,
        f"rr.save:{case_id}:"
        + json.dumps({"before": before, "after": record(item)}, sort_keys=True),
    )
    await db.commit()
    return record(item)


@router.delete("/cases/{case_id}/records/{kind}", status_code=204)
async def delete_status_record(
    case_id: uuid.UUID,
    kind: Literal["compensation", "rr"],
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*MANAGERS)),
):
    await accessible_case_or_404(db, case_id, actor, for_update=True)
    model = CompensationStatus if kind == "compensation" else RRStatus
    item = await db.scalar(select(model).where(model.case_id == case_id))
    if item:
        await write_audit_log(
            db, actor.id, f"{kind}.remove:{case_id}:" + json.dumps(record(item), sort_keys=True)
        )
        await db.delete(item)
        await db.commit()
    return Response(status_code=204)


@router.patch("/cases/{case_id}/families")
async def save_families(
    case_id: uuid.UUID,
    payload: FamilyWrite,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*MANAGERS)),
):
    case = await accessible_case_or_404(db, case_id, actor, for_update=True)
    rr = await db.scalar(select(RRStatus).where(RRStatus.case_id == case_id))
    if rr and rr.families_supported > payload.affected_family_count:
        raise HTTPException(422, "Affected count cannot fall below families already supported")
    before = {"affected": case.affected_family_count, "displaced": case.displaced_family_count}
    case.affected_family_count = payload.affected_family_count
    case.displaced_family_count = payload.displaced_family_count
    await write_audit_log(
        db,
        actor.id,
        f"families.save:{case_id}:"
        + json.dumps({"before": before, "after": payload.model_dump()}, sort_keys=True),
    )
    await db.commit()
    return payload


@router.post("/cases/{case_id}/deadlines", status_code=201)
async def create_deadline(
    case_id: uuid.UUID,
    payload: DeadlineWrite,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*MANAGERS)),
):
    await accessible_case_or_404(db, case_id, actor, for_update=True)
    deadline = CaseDeadline(case_id=case_id, created_by=actor.id, **payload.model_dump())
    db.add(deadline)
    await db.flush()
    await write_audit_log(
        db, actor.id, f"deadline.create:{case_id}:" + json.dumps(record(deadline), sort_keys=True)
    )
    await db.commit()
    return record(deadline)


@router.patch("/grievances/{grievance_id}")
async def update_grievance(
    grievance_id: uuid.UUID,
    payload: GrievanceUpdate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*STAFF)),
):
    item = await db.get(Grievance, grievance_id)
    if item is None:
        raise HTTPException(404, "Grievance not found")
    await accessible_case_or_404(db, item.case_id, actor, for_update=True)
    item.status, item.response = payload.status, payload.response
    await write_audit_log(
        db, actor.id, f"grievance.respond:{item.id}:{item.status.value}:{payload.response}"
    )
    await db.commit()
    return record(item)


@router.get("/gis/parcels")
async def list_map_parcels(
    db: AsyncSession = Depends(get_db), actor: User = Depends(get_current_user)
):
    query = scope_case_query(
        select(
            AcquisitionCase,
            Parcel,
            Project,
            func.ST_AsGeoJSON(Parcel.polygon),
            func.ST_Area(Parcel.polygon.cast(Geography)) / 10000,
        )
        .join(Parcel, Parcel.id == AcquisitionCase.parcel_id)
        .join(Project, Project.id == Parcel.project_id),
        actor,
    )
    rows = (await db.execute(query)).all()
    return [
        {
            "id": str(parcel.id),
            "survey_number": parcel.khasra_survey_no,
            "village": project.district,
            "area_hectares": float(area),
            "case_id": str(case.id),
            "stage": case.current_stage.value,
            "coordinates": [
                [point[1], point[0]] for point in json.loads(geometry)["coordinates"][0]
            ],
        }
        for case, parcel, project, geometry, area in rows
    ]


async def inbox_data(db, actor, rows=None):
    rows = rows if rows is not None else await reporting_rows(db, actor)
    ids = [row[0].id for row in rows]
    histories = list(
        await db.scalars(select(CaseStageHistory).where(CaseStageHistory.case_id.in_(ids)))
    )
    documents = list(await db.scalars(select(Document).where(Document.case_id.in_(ids))))
    deadlines = list(await db.scalars(select(CaseDeadline).where(CaseDeadline.case_id.in_(ids))))
    return build_alerts(rows, histories, documents, deadlines), histories, deadlines


@router.get("/alerts")
async def inbox(db: AsyncSession = Depends(get_db), actor: User = Depends(get_current_user)):
    alerts, _, _ = await inbox_data(db, actor)
    receipts = set(
        await db.scalars(select(AlertReceipt.alert_key).where(AlertReceipt.user_id == actor.id))
    )
    return {
        "items": [{**alert, "read": alert["key"] in receipts} for alert in alerts],
        "generated_at": datetime.now(UTC),
        "delivery": "in_app",
        "evaluation": "on_refresh",
    }


@router.put("/alerts/read")
async def mark_read(
    key: str = Query(max_length=200),
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    alerts, _, _ = await inbox_data(db, actor)
    if key not in {alert["key"] for alert in alerts}:
        raise HTTPException(404, "Alert not found")
    await db.execute(
        insert(AlertReceipt)
        .values(id=uuid.uuid4(), user_id=actor.id, alert_key=key)
        .on_conflict_do_nothing(index_elements=["user_id", "alert_key"])
    )
    await db.commit()
    return {"read": True}


@router.get("/dashboard/summary")
async def dashboard(
    state: str | None = None,
    district: str | None = None,
    project_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    rows = await reporting_rows(db, actor, state=state, district=district, project_id=project_id)
    alerts, history, deadlines = await inbox_data(db, actor, rows)
    today = india_today(datetime.now(UTC))
    due = [item for item in deadlines if item.due_date < today]
    breaches = {alert["key"] for alert in alerts if alert["kind"] == "deadline"}
    ids = [row[0].id for row in rows]
    open_grievances = await db.scalar(
        select(func.count())
        .select_from(Grievance)
        .where(Grievance.case_id.in_(ids), Grievance.status != "resolved")
    )
    return {
        **summarize(rows),
        "open_grievances": open_grievances,
        "alerts_requiring_attention": sum(alert["severity"] != "info" for alert in alerts),
        "recorded_deadlines_due": len(due),
        "deadline_breaches": len(breaches),
        "timeline_adherence_pct": round((len(due) - len(breaches)) * 100 / len(due), 1)
        if due
        else None,
        "projects": grouped_summaries(rows, "project"),
        "districts": grouped_summaries(rows, "district"),
        "states": grouped_summaries(rows, "state"),
        "trend": monthly_trend(history),
        "generated_at": datetime.now(UTC),
        "notice": (
            "Live database aggregates. Seeded showcase records and parcel boundaries "
            "are synthetic. Acquired area means possession-stage parcels; amounts are recorded, "
            "never predicted. Timeline adherence covers recorded deadlines only."
        ),
    }


REPORT_COLUMNS = [
    "group",
    "state",
    "district",
    "case_count",
    "area_notified_hectares",
    "area_acquired_hectares",
    "affected_families",
    "displaced_families",
    "assessed_amount",
    "disbursed_amount",
    "compensation_recorded",
    "amounts_recorded",
    "payment_amounts_recorded",
    "compensation_disbursed",
    "rr_recorded",
    "rr_completed",
    "rr_families_supported",
    "possession_cases",
    "completion_pct",
]


@router.get("/reports/{report_type}")
async def report(
    report_type: Literal["project", "state", "district", "compensation"],
    format: Literal["json", "csv"] = "csv",
    columns: str | None = None,
    state: str | None = None,
    district: str | None = None,
    project_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*MANAGERS)),
):
    selected = columns.split(",") if columns else REPORT_COLUMNS
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(column not in REPORT_COLUMNS for column in selected)
    ):
        raise HTTPException(422, "Choose unique columns from the standard report template")
    rows = grouped_summaries(
        await reporting_rows(db, actor, state=state, district=district, project_id=project_id),
        report_type,
    )
    if format == "json":
        return {
            "columns": selected,
            "rows": [{key: row[key] for key in selected} for row in rows],
            "generated_at": datetime.now(UTC),
        }
    return Response(
        csv_text(rows, selected),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="bhoomisetu-{report_type}-{datetime.now(UTC):%Y-%m-%d}.csv"'
            ),
            "Cache-Control": "no-store",
        },
    )
