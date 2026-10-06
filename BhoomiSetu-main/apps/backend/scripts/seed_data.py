import argparse
import asyncio
import json
import math
from dataclasses import dataclass
from pathlib import Path

from faker import Faker
from geoalchemy2.elements import WKTElement
from sqlalchemy import delete, select

from app.core.database import SessionFactory
from app.core.security import hash_password
from app.models import (
    AcquisitionCase,
    CaseStageHistory,
    CompensationStatus,
    Document,
    Grievance,
    Landowner,
    Parcel,
    Project,
    RRStatus,
    User,
)
from app.models.domain import CaseDeadline
from app.models.enums import CaseStage, ProjectStatus, UserRole
from app.services.audit import write_audit_log

fake = Faker("en_IN")
fake.seed_instance(26016)
DEMO_PASSWORD = "DemoPass123!"
DEMO_PROJECT_NAME = "Pune Ring Road Demonstration"
OSM_GEOMETRY_PATH = Path(__file__).parent / "data" / "kharadi_bypass_osm.json"


@dataclass(frozen=True)
class DemoAccount:
    name: str
    email: str
    role: UserRole


DEMO_ACCOUNTS = (
    DemoAccount("Anita Patil", "citizen@bhoomsetu.local", UserRole.LANDOWNER),
    DemoAccount("Field Officer", "officer@bhoomsetu.local", UserRole.OFFICER),
    DemoAccount("Project Authority", "authority@bhoomsetu.local", UserRole.PROJECT_AUTHORITY),
    DemoAccount("District Administrator", "district@bhoomsetu.local", UserRole.DISTRICT_ADMIN),
    DemoAccount("Senior Administrator", "senior@bhoomsetu.local", UserRole.SENIOR_ADMIN),
)

STAGE_PATH = [
    CaseStage.NOTIFICATION,
    CaseStage.VERIFICATION,
    CaseStage.OBJECTION,
    CaseStage.AWARD,
    CaseStage.COMPENSATION,
    CaseStage.POSSESSION,
]


def demo_polygon(index: int) -> WKTElement:
    """Derive a synthetic parcel boundary from a real OSM road segment."""
    source = json.loads(OSM_GEOMETRY_PATH.read_text())
    start = source["geometry"][index]
    end = source["geometry"][index + 1]
    dx = end["lon"] - start["lon"]
    dy = end["lat"] - start["lat"]
    length = math.hypot(dx, dy)
    offset = 0.00035
    perpendicular_x = (-dy / length) * offset
    perpendicular_y = (dx / length) * offset
    points = [
        (start["lon"] + perpendicular_x, start["lat"] + perpendicular_y),
        (end["lon"] + perpendicular_x, end["lat"] + perpendicular_y),
        (end["lon"] - perpendicular_x, end["lat"] - perpendicular_y),
        (start["lon"] - perpendicular_x, start["lat"] - perpendicular_y),
        (start["lon"] + perpendicular_x, start["lat"] + perpendicular_y),
    ]
    coordinates = ", ".join(f"{x} {y}" for x, y in points)
    return WKTElement(f"POLYGON(({coordinates}))", srid=4326)


async def seed(*, reset_existing: bool = True) -> None:
    async with SessionFactory() as db:
        existing = await db.scalar(select(Project).where(Project.name == DEMO_PROJECT_NAME))
        if existing:
            if not reset_existing:
                print("Demo project already exists; leaving persisted demo interactions unchanged.")
                return
            account_rows = list(
                await db.scalars(
                    select(User).where(User.email.in_([account.email for account in DEMO_ACCOUNTS]))
                )
            )
            accounts = {user.role: user for user in account_rows}
            for account in DEMO_ACCOUNTS:
                user = next(
                    (candidate for candidate in account_rows if candidate.email == account.email),
                    None,
                )
                if user is None:
                    user = User(
                        name=account.name,
                        email=account.email,
                        role=account.role,
                        password_hash=hash_password(DEMO_PASSWORD),
                    )
                    db.add(user)
                    await db.flush()
                user.name = account.name
                user.role = account.role
                user.password_hash = hash_password(DEMO_PASSWORD)
                accounts[account.role] = user

            existing.project_type = "Highway"
            existing.state = "Maharashtra"
            existing.district = "Pune"
            existing.status = ProjectStatus.ACTIVE
            parcels = list(
                await db.scalars(
                    select(Parcel)
                    .where(Parcel.project_id == existing.id)
                    .order_by(Parcel.khasra_survey_no)
                )
            )
            case_ids = [
                case_id
                for case_id in await db.scalars(
                    select(AcquisitionCase.id).join(Parcel).where(Parcel.project_id == existing.id)
                )
            ]
            if case_ids:
                for model in (
                    Document,
                    Grievance,
                    CompensationStatus,
                    RRStatus,
                    CaseDeadline,
                    CaseStageHistory,
                ):
                    await db.execute(delete(model).where(model.case_id.in_(case_ids)))

            officer = accounts[UserRole.OFFICER]
            citizen = accounts[UserRole.LANDOWNER]
            for index, parcel in enumerate(parcels[:20]):
                parcel.polygon = demo_polygon(index)
                landowners = list(
                    await db.scalars(select(Landowner).where(Landowner.parcel_id == parcel.id))
                )
                if landowners:
                    landowner = landowners[0]
                    landowner.user_id = citizen.id if index == 0 else None
                    landowner.name = citizen.name if index == 0 else fake.name()
                    landowner.contact = (
                        "demo-only@example.invalid" if index == 0 else fake.phone_number()
                    )

                acquisition_case = await db.scalar(
                    select(AcquisitionCase).where(AcquisitionCase.parcel_id == parcel.id)
                )
                if acquisition_case is None:
                    continue
                current_stage = STAGE_PATH[index % len(STAGE_PATH)]
                acquisition_case.current_stage = current_stage
                acquisition_case.assigned_officer_id = officer.id
                acquisition_case.displaced_family_count = 0
                acquisition_case.affected_family_count = (index % 4) + 1
                for from_stage, to_stage in zip(
                    STAGE_PATH[: STAGE_PATH.index(current_stage)],
                    STAGE_PATH[1 : STAGE_PATH.index(current_stage) + 1],
                    strict=True,
                ):
                    db.add(
                        CaseStageHistory(
                            case_id=acquisition_case.id,
                            from_stage=from_stage,
                            to_stage=to_stage,
                            changed_by=officer.id,
                            reason="Synthetic demonstration history",
                        )
                    )
            await write_audit_log(
                db, accounts[UserRole.PROJECT_AUTHORITY].id, f"seed.reset:{existing.id}"
            )
            await db.commit()
            print("Restored the existing demo project, accounts, cases, histories and parcels.")
            return

        accounts: dict[UserRole, User] = {}
        for account in DEMO_ACCOUNTS:
            user = User(
                name=account.name,
                email=account.email,
                role=account.role,
                password_hash=hash_password(DEMO_PASSWORD),
            )
            db.add(user)
            await db.flush()
            accounts[account.role] = user
            await write_audit_log(db, user.id, f"seed.user:{user.id}:{user.role.value}")

        project = Project(
            name=DEMO_PROJECT_NAME,
            project_type="Highway",
            state="Maharashtra",
            district="Pune",
            status=ProjectStatus.ACTIVE,
        )
        db.add(project)
        await db.flush()

        authority = accounts[UserRole.PROJECT_AUTHORITY]
        officer = accounts[UserRole.OFFICER]
        citizen = accounts[UserRole.LANDOWNER]
        await write_audit_log(db, authority.id, f"seed.project:{project.id}")

        for index in range(20):
            parcel = Parcel(
                project_id=project.id,
                khasra_survey_no=f"PRR-{1001 + index}",
                polygon=demo_polygon(index),
            )
            db.add(parcel)
            await db.flush()

            landowner = Landowner(
                parcel_id=parcel.id,
                user_id=citizen.id if index == 0 else None,
                name=citizen.name if index == 0 else fake.name(),
                contact="demo-only@example.invalid" if index == 0 else fake.phone_number(),
            )
            db.add(landowner)

            current_stage = STAGE_PATH[index % len(STAGE_PATH)]
            acquisition_case = AcquisitionCase(
                parcel_id=parcel.id,
                current_stage=current_stage,
                assigned_officer_id=officer.id,
                affected_family_count=(index % 4) + 1,
            )
            db.add(acquisition_case)
            await db.flush()

            for from_stage, to_stage in zip(
                STAGE_PATH[: STAGE_PATH.index(current_stage)],
                STAGE_PATH[1 : STAGE_PATH.index(current_stage) + 1],
                strict=True,
            ):
                db.add(
                    CaseStageHistory(
                        case_id=acquisition_case.id,
                        from_stage=from_stage,
                        to_stage=to_stage,
                        changed_by=officer.id,
                        reason="Synthetic demonstration history",
                    )
                )
            await write_audit_log(db, authority.id, f"seed.case:{acquisition_case.id}")

        await db.commit()
        print("Created 5 demo accounts, 1 project, 20 parcels, landowners, and cases.")
        print(f"All demo accounts use password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed BhoomiSetu's synthetic showcase data.")
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help="Create the showcase only when it does not exist; never reset persisted interactions.",
    )
    arguments = parser.parse_args()
    asyncio.run(seed(reset_existing=not arguments.if_empty))
