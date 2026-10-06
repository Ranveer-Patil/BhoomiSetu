"""Deterministic inbox rules evaluated on every inbox refresh; no outbound delivery."""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.models.enums import CaseStage

STAGE_TARGET_DAYS = {
    "notification": 30,
    "verification": 30,
    "objection": 60,
    "award": 60,
    "compensation": 30,
}
STAGE_ORDER = list(CaseStage)


def india_today(now: datetime) -> date:
    return now.astimezone(ZoneInfo("Asia/Kolkata")).date()


def build_alerts(rows, histories, documents, deadlines, *, now=None, pending_days=7):
    now = now or datetime.now(UTC)
    today = india_today(now)
    alerts = []
    by_case = {str(row[0].id): row for row in rows}
    history_by_case = {}
    for event in histories:
        history_by_case.setdefault(str(event.case_id), []).append(event)
        if event.changed_at >= now - timedelta(days=30):
            alerts.append(
                {
                    "key": f"milestone:{event.id}",
                    "case_id": str(event.case_id),
                    "kind": "milestone",
                    "severity": "info",
                    "title": f"Stage updated: {event.to_stage.value}",
                    "detail": "A workflow change was recorded in the case history.",
                    "date": event.changed_at.isoformat(),
                }
            )
    for case, _parcel, _project, compensation, _rr, _area in rows:
        history = history_by_case.get(str(case.id), [])
        entered = max((event.changed_at for event in history), default=case.created_at)
        target = STAGE_TARGET_DAYS.get(case.current_stage.value)
        elapsed = (today - india_today(entered)).days
        if target is not None and elapsed > target:
            alerts.append(
                {
                    "key": f"delay:{case.id}:{case.current_stage.value}:{entered.isoformat()}",
                    "case_id": str(case.id),
                    "kind": "delay",
                    "severity": "warning",
                    "title": "Stage review overdue",
                    "detail": (
                        f"{elapsed} days in {case.current_stage.value}; "
                        f"prototype operational target {target} days, not a legal deadline."
                    ),
                    "date": entered.isoformat(),
                }
            )
        if (
            compensation
            and compensation.due_date
            and compensation.status.value != "disbursed"
            and compensation.due_date < today
        ):
            alerts.append(
                {
                    "key": f"payment:{case.id}:{compensation.due_date}",
                    "case_id": str(case.id),
                    "kind": "compensation",
                    "severity": "urgent",
                    "title": "Compensation due date passed",
                    "detail": compensation.reference,
                    "date": compensation.due_date.isoformat(),
                }
            )
    for doc in documents:
        if (
            doc.created_at
            and doc.status.value in ("pending", "extracted")
            and doc.created_at < now - timedelta(days=pending_days)
        ):
            alerts.append(
                {
                    "key": f"approval:{doc.id}",
                    "case_id": str(doc.case_id),
                    "kind": "approval",
                    "severity": "warning",
                    "title": "Document awaiting review",
                    "detail": f"Awaiting human review for more than {pending_days} days.",
                    "date": doc.created_at.isoformat(),
                }
            )
    for deadline in deadlines:
        row = by_case.get(str(deadline.case_id))
        if row is None:
            continue
        # Completed at or before the due date counts as met; late completion remains visible.
        completed = [
            event.changed_at
            for event in history_by_case.get(str(deadline.case_id), [])
            if (
                STAGE_ORDER.index(event.to_stage) > STAGE_ORDER.index(deadline.stage)
                or event.to_stage == deadline.stage == CaseStage.POSSESSION
            )
        ]
        met = any(india_today(changed) <= deadline.due_date for changed in completed)
        if not met and deadline.due_date < today:
            alerts.append(
                {
                    "key": f"deadline:{deadline.id}",
                    "case_id": str(deadline.case_id),
                    "kind": "deadline",
                    "severity": "urgent",
                    "title": f"Recorded {deadline.basis} deadline passed",
                    "detail": deadline.reference,
                    "date": deadline.due_date.isoformat(),
                }
            )
    rank = {"urgent": 0, "warning": 1, "info": 2}
    return sorted(alerts, key=lambda alert: (rank[alert["severity"]], alert["date"], alert["key"]))
