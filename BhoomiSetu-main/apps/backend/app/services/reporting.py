"""Reporting from scoped database rows. Missing amounts remain distinguishable from zero."""

import csv
import io
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select

from app.models import AcquisitionCase, CompensationStatus, Parcel, Project, RRStatus
from app.services.case_access import scope_case_query


async def reporting_rows(db, actor, *, state=None, district=None, project_id=None):
    query = (
        select(
            AcquisitionCase,
            Parcel,
            Project,
            CompensationStatus,
            RRStatus,
            (func.ST_Area(cast(Parcel.polygon, Geography)) / 10000).label("area_hectares"),
        )
        .join(Parcel, Parcel.id == AcquisitionCase.parcel_id)
        .join(Project, Project.id == Parcel.project_id)
        .outerjoin(CompensationStatus, CompensationStatus.case_id == AcquisitionCase.id)
        .outerjoin(RRStatus, RRStatus.case_id == AcquisitionCase.id)
    )
    query = scope_case_query(query, actor)
    if state:
        query = query.where(Project.state == state)
    if district:
        query = query.where(Project.district == district)
    if project_id:
        query = query.where(Project.id == project_id)
    return list((await db.execute(query.order_by(Project.name, AcquisitionCase.id))).all())


def summarize(rows):
    amounts = [row[3] for row in rows if row[3] is not None]
    assessed = [item.assessed_amount for item in amounts if item.assessed_amount is not None]
    paid = [item.disbursed_amount for item in amounts if item.disbursed_amount is not None]
    stages = Counter(row[0].current_stage.value for row in rows)
    return {
        "case_count": len(rows),
        "project_count": len({row[2].id for row in rows}),
        "affected_families": sum(row[0].affected_family_count for row in rows),
        "displaced_families": sum(row[0].displaced_family_count for row in rows),
        "area_notified_hectares": round(sum(float(row[5] or 0) for row in rows), 4),
        "area_acquired_hectares": round(
            sum(float(row[5] or 0) for row in rows if row[0].current_stage.value == "possession"), 4
        ),
        "assessed_amount": str(sum(assessed, Decimal(0))) if assessed else None,
        "disbursed_amount": str(sum(paid, Decimal(0))) if paid else None,
        "compensation_recorded": len(amounts),
        "compensation_disbursed": sum(item.status.value == "disbursed" for item in amounts),
        "amounts_recorded": len(assessed),
        "payment_amounts_recorded": len(paid),
        "rr_recorded": sum(row[4] is not None for row in rows),
        "rr_completed": sum(
            row[4] is not None and row[4].rehabilitation_stage == "completed" for row in rows
        ),
        "rr_families_supported": sum(row[4].families_supported for row in rows if row[4]),
        "possession_cases": stages["possession"],
        "completion_pct": round(stages["possession"] * 100 / len(rows), 1) if rows else 0,
        "stages": dict(stages),
    }


def grouped_summaries(rows, report_type):
    groups = defaultdict(list)
    for row in rows:
        project = row[2]
        key = (
            (str(project.id), project.name, project.state, project.district)
            if report_type in ("project", "compensation")
            else (project.state, project.district)
            if report_type == "district"
            else (project.state,)
        )
        groups[key].append(row)
    result = []
    for key, members in groups.items():
        project = members[0][2]
        result.append(
            {
                "group": " / ".join(key[1:] if report_type in ("project", "compensation") else key),
                "project_id": str(project.id) if report_type in ("project", "compensation") else "",
                "state": project.state,
                "district": project.district if report_type != "state" else "",
                **summarize(members),
            }
        )
    return result


def monthly_trend(histories, now=None):
    now = now or datetime.now(UTC)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous = (start - timedelta(days=1)).replace(day=1)
    # Equal month-to-date windows avoid comparing a partial month with a full month.
    previous_end = min(previous + (now - start), start)
    current = sum(start <= event.changed_at <= now for event in histories)
    prior = sum(previous <= event.changed_at <= previous_end for event in histories)
    return {
        "current_transitions": current,
        "previous_transitions": prior,
        "difference": current - prior,
        "current_start": start.isoformat(),
        "previous_start": previous.isoformat(),
        "previous_end": previous_end.isoformat(),
        "label": "Workflow changes: month to date vs equal elapsed time in previous month (UTC)",
    }


def csv_text(rows, columns):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(columns)
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column)
            value = "" if value is None else str(value)
            # Prevent spreadsheet formulas in names and other user-entered text.
            if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(
                ("\t", "\r", "\n")
            ):
                value = "'" + value
            values.append(value)
        writer.writerow(values)
    return "\ufeff" + output.getvalue()
