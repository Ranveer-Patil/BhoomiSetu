import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models import AcquisitionCase, Landowner, Parcel, Project, User
from app.models.enums import CaseStage, UserRole
from app.schemas.domain import (
    CaseCreate,
    CaseDetailResponse,
    CaseResponse,
    CaseTransitionRequest,
    LandownerCreate,
    LandownerResponse,
    ParcelCreate,
    ParcelResponse,
    ProjectCreate,
    ProjectResponse,
    StageHistoryResponse,
)
from app.services.audit import write_audit_log
from app.services.case_access import accessible_case_or_404, scope_case_query
from app.services.workflow import transition_case

router = APIRouter(tags=["projects and cases"])

MANAGER_ROLES = (
    UserRole.PROJECT_AUTHORITY,
    UserRole.DISTRICT_ADMIN,
    UserRole.SENIOR_ADMIN,
)
TRANSITION_ROLES = (
    UserRole.OFFICER,
    UserRole.PROJECT_AUTHORITY,
    UserRole.DISTRICT_ADMIN,
    UserRole.SENIOR_ADMIN,
)


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*MANAGER_ROLES)),
) -> Project:
    project = Project(**payload.model_dump())
    db.add(project)
    await db.flush()
    await write_audit_log(db, actor.id, f"project.create:{project.id}")
    await db.commit()
    return project


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> list[Project]:
    query = select(Project).order_by(Project.created_at.desc())
    if actor.role in (UserRole.LANDOWNER, UserRole.OFFICER):
        visible_projects = scope_case_query(
            select(Parcel.project_id).join(AcquisitionCase, AcquisitionCase.parcel_id == Parcel.id),
            actor,
        )
        query = query.where(Project.id.in_(visible_projects))
    return list(await db.scalars(query))


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> Project:
    if actor.role in (UserRole.LANDOWNER, UserRole.OFFICER):
        visible = scope_case_query(
            select(AcquisitionCase.id).join(Parcel).where(Parcel.project_id == project_id), actor
        )
        if await db.scalar(visible.limit(1)) is None:
            raise HTTPException(status_code=404, detail="Project not found")
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post(
    "/projects/{project_id}/parcels",
    response_model=ParcelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_parcel(
    project_id: uuid.UUID,
    payload: ParcelCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*MANAGER_ROLES)),
) -> ParcelResponse:
    if await db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    geojson = json.dumps({"type": "Polygon", "coordinates": payload.polygon})
    valid = await db.scalar(select(func.ST_IsValid(func.ST_GeomFromGeoJSON(geojson))))
    if not valid:
        raise HTTPException(422, "Parcel boundary must be a valid, non-self-intersecting polygon")
    parcel = Parcel(
        project_id=project_id,
        khasra_survey_no=payload.khasra_survey_no,
        polygon=func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson), 4326),
    )
    db.add(parcel)
    try:
        await db.flush()
        await write_audit_log(db, actor.id, f"parcel.create:{parcel.id}:project:{project_id}")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This project already contains that khasra/survey number",
        ) from None
    return ParcelResponse(
        id=parcel.id,
        project_id=parcel.project_id,
        khasra_survey_no=parcel.khasra_survey_no,
        polygon=json.loads(geojson),
    )


@router.get("/parcels/{parcel_id}", response_model=ParcelResponse)
async def get_parcel(
    parcel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> ParcelResponse:
    if actor.role in (UserRole.LANDOWNER, UserRole.OFFICER):
        visible = scope_case_query(
            select(AcquisitionCase.id).where(AcquisitionCase.parcel_id == parcel_id), actor
        )
        if await db.scalar(visible.limit(1)) is None:
            raise HTTPException(404, "Parcel not found")
    row = (
        await db.execute(
            select(Parcel, func.ST_AsGeoJSON(Parcel.polygon)).where(Parcel.id == parcel_id)
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    parcel, polygon_json = row
    return ParcelResponse(
        id=parcel.id,
        project_id=parcel.project_id,
        khasra_survey_no=parcel.khasra_survey_no,
        polygon=json.loads(polygon_json),
    )


@router.post(
    "/parcels/{parcel_id}/landowners",
    response_model=LandownerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_landowner(
    parcel_id: uuid.UUID,
    payload: LandownerCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*MANAGER_ROLES)),
) -> Landowner:
    if await db.get(Parcel, parcel_id) is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    if payload.user_id is not None:
        linked_user = await db.get(User, payload.user_id)
        if linked_user is None or linked_user.role != UserRole.LANDOWNER:
            raise HTTPException(status_code=422, detail="Linked user must be a landowner account")
    landowner = Landowner(parcel_id=parcel_id, **payload.model_dump())
    db.add(landowner)
    await db.flush()
    await write_audit_log(db, actor.id, f"landowner.create:{landowner.id}:parcel:{parcel_id}")
    await db.commit()
    return landowner


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*MANAGER_ROLES)),
) -> AcquisitionCase:
    if await db.get(Parcel, payload.parcel_id) is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    if payload.assigned_officer_id is not None:
        officer = await db.get(User, payload.assigned_officer_id)
        if officer is None or officer.role != UserRole.OFFICER:
            raise HTTPException(status_code=422, detail="Assigned user must be an officer")
    acquisition_case = AcquisitionCase(**payload.model_dump())
    db.add(acquisition_case)
    try:
        await db.flush()
        await write_audit_log(db, actor.id, f"case.create:{acquisition_case.id}")
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="This parcel already has a case") from None
    return acquisition_case


@router.get("/cases", response_model=list[CaseResponse])
async def list_cases(
    project_id: uuid.UUID | None = None,
    state: str | None = None,
    stage: CaseStage | None = None,
    officer_id: uuid.UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> list[AcquisitionCase]:
    query = select(AcquisitionCase).join(Parcel).join(Project)
    query = scope_case_query(query, actor)
    if project_id:
        query = query.where(Project.id == project_id)
    if state:
        query = query.where(Project.state.ilike(state))
    if stage:
        query = query.where(AcquisitionCase.current_stage == stage)
    if officer_id:
        query = query.where(AcquisitionCase.assigned_officer_id == officer_id)
    query = query.order_by(AcquisitionCase.created_at.desc()).limit(limit)
    return list(await db.scalars(query))


@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
async def get_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> CaseDetailResponse:
    acquisition_case = await accessible_case_or_404(db, case_id, actor)
    await db.refresh(acquisition_case, attribute_names=["stage_history"])
    response = CaseResponse.model_validate(acquisition_case).model_dump()
    return CaseDetailResponse(
        **response,
        stage_history=[
            StageHistoryResponse.model_validate(row) for row in acquisition_case.stage_history
        ],
    )


@router.post("/cases/{case_id}/transition", response_model=CaseResponse)
async def change_case_stage(
    case_id: uuid.UUID,
    payload: CaseTransitionRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_roles(*TRANSITION_ROLES)),
) -> AcquisitionCase:
    acquisition_case = await accessible_case_or_404(db, case_id, actor, for_update=True)
    await transition_case(db, acquisition_case, payload.new_stage, actor.id, payload.reason)
    await db.commit()
    return acquisition_case
