import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AcquisitionCase, CaseStageHistory
from app.models.enums import CaseStage
from app.services.audit import write_audit_log

STAGE_TRANSITIONS: dict[CaseStage, set[CaseStage]] = {
    CaseStage.NOTIFICATION: {CaseStage.VERIFICATION},
    CaseStage.VERIFICATION: {CaseStage.OBJECTION},
    CaseStage.OBJECTION: {CaseStage.AWARD, CaseStage.VERIFICATION},
    CaseStage.AWARD: {CaseStage.COMPENSATION},
    CaseStage.COMPENSATION: {CaseStage.POSSESSION},
    CaseStage.POSSESSION: set(),
}


def is_valid_transition(from_stage: CaseStage, to_stage: CaseStage) -> bool:
    return to_stage in STAGE_TRANSITIONS[from_stage]


async def transition_case(
    db: AsyncSession,
    acquisition_case: AcquisitionCase,
    new_stage: CaseStage,
    actor_id: uuid.UUID,
    reason: str | None = None,
) -> AcquisitionCase:
    old_stage = acquisition_case.current_stage
    if not is_valid_transition(old_stage, new_stage):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition from {old_stage.value} to {new_stage.value}",
        )

    acquisition_case.current_stage = new_stage
    db.add(
        CaseStageHistory(
            case_id=acquisition_case.id,
            from_stage=old_stage,
            to_stage=new_stage,
            changed_by=actor_id,
            reason=reason,
        )
    )
    await write_audit_log(
        db,
        actor_id,
        f"case.transition:{acquisition_case.id}:{old_stage.value}->{new_stage.value}",
    )
    return acquisition_case
