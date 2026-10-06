import pytest

from app.models.enums import CaseStage
from app.services.workflow import is_valid_transition


@pytest.mark.parametrize(
    ("from_stage", "to_stage"),
    [
        (CaseStage.NOTIFICATION, CaseStage.VERIFICATION),
        (CaseStage.VERIFICATION, CaseStage.OBJECTION),
        (CaseStage.OBJECTION, CaseStage.AWARD),
        (CaseStage.OBJECTION, CaseStage.VERIFICATION),
        (CaseStage.AWARD, CaseStage.COMPENSATION),
        (CaseStage.COMPENSATION, CaseStage.POSSESSION),
    ],
)
def test_allowed_transitions(from_stage: CaseStage, to_stage: CaseStage) -> None:
    assert is_valid_transition(from_stage, to_stage)


@pytest.mark.parametrize(
    ("from_stage", "to_stage"),
    [
        (CaseStage.NOTIFICATION, CaseStage.AWARD),
        (CaseStage.VERIFICATION, CaseStage.POSSESSION),
        (CaseStage.POSSESSION, CaseStage.NOTIFICATION),
    ],
)
def test_rejects_skipped_or_reversed_transitions(
    from_stage: CaseStage, to_stage: CaseStage
) -> None:
    assert not is_valid_transition(from_stage, to_stage)
