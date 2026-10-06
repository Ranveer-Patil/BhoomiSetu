import csv
import io
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace as Row

import pytest
from pydantic import ValidationError

from app.models.enums import CaseStage, CompensationState, DocumentStatus
from app.schemas.domain import ParcelCreate, ProjectCreate, ProjectResponse
from app.schemas.operations import CompensationWrite, FamilyWrite, RRWrite
from app.services.master_data import missing_document_fields, validate_survey_number
from app.services.monitoring import build_alerts
from app.services.reporting import csv_text, monthly_trend, summarize
from tests.test_phase_one_api import authorization, register


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "approved", "assessed_amount": "100", "disbursed_amount": "101"},
        {"status": "disbursed", "assessed_amount": "100", "disbursed_amount": "99"},
        {"status": "approved", "disbursed_amount": "10"},
        {"status": "assessed", "assessed_amount": "-1"},
    ],
)
def test_compensation_rejects_inconsistent_records(payload):
    with pytest.raises(ValidationError):
        CompensationWrite(reference="Award register 12", **payload)


def test_master_data_and_validation():
    assert validate_survey_number(" १४२/२-अ ") == "१४२/२-अ"
    with pytest.raises(ValueError):
        validate_survey_number("=SUM(A1)")
    with pytest.raises(ValidationError):
        FamilyWrite(affected_family_count=1, displaced_family_count=2)
    with pytest.raises(ValidationError):
        RRWrite(rehabilitation_stage="made_up", notes="Test")
    assert missing_document_fields("land_record", {"owner_name": "Test"}) == [
        "khasra_survey_number",
        "area_hectares",
    ]
    assert (
        ProjectCreate(name="Test", project_type="highway", state="MH", district="Pune").project_type
        == "Highway"
    )
    with pytest.raises(ValidationError):
        ParcelCreate(khasra_survey_no="S-1", polygon=[[[190, 0], [190, 1], [191, 0], [190, 0]]])


def test_reporting_distinguishes_missing_amounts_from_zero():
    case = Row(
        current_stage=CaseStage.POSSESSION, affected_family_count=3, displaced_family_count=1
    )
    project = Row(id="project-1")
    summary = summarize([(case, None, project, None, None, 2.25)])
    assert summary["disbursed_amount"] is None
    assert summary["area_acquired_hectares"] == 2.25
    assert summary["completion_pct"] == 100
    compensation = Row(
        status=CompensationState.APPROVED,
        assessed_amount=Decimal("100.25"),
        disbursed_amount=Decimal("0"),
    )
    summary = summarize([(case, None, project, compensation, None, 2.25)])
    assert summary["disbursed_amount"] == "0"
    assert summary["assessed_amount"] == "100.25"
    assert summary["payment_amounts_recorded"] == 1
    assert summarize([])["completion_pct"] == 0


def test_csv_prevents_formulas_and_preserves_commas():
    content = csv_text(
        [
            {"group": '=HYPERLINK("example")', "amount": None},
            {"group": "Pune, East", "amount": "100.20"},
        ],
        ["group", "amount"],
    )
    rows = list(csv.reader(io.StringIO(content.lstrip("\ufeff"))))
    assert rows[1] == ['\'=HYPERLINK("example")', ""]
    assert rows[2] == ["Pune, East", "100.20"]


def test_alert_due_boundaries_completion_and_unknown_document_dates():
    now = datetime(2026, 9, 6, 12, tzinfo=UTC)
    entered = now - timedelta(days=31)
    case = Row(id="case", current_stage=CaseStage.VERIFICATION, created_at=entered)
    compensation = Row(
        due_date=now.date() - timedelta(days=1),
        status=CompensationState.APPROVED,
        reference="Payment order",
    )
    rows = [(case, None, None, compensation, None, 1)]
    doc = Row(
        id="doc",
        case_id="case",
        created_at=now - timedelta(days=8),
        status=DocumentStatus.EXTRACTED,
    )
    unknown = Row(id="old", case_id="case", created_at=None, status=DocumentStatus.EXTRACTED)
    deadline = Row(
        id="deadline",
        case_id="case",
        stage=CaseStage.NOTIFICATION,
        due_date=now.date() - timedelta(days=20),
        basis="statutory",
        reference="Recorded authority order",
    )
    history = [Row(id="event", case_id="case", changed_at=entered, to_stage=CaseStage.VERIFICATION)]
    alerts = build_alerts(rows, history, [doc, unknown], [deadline], now=now)
    assert {item["kind"] for item in alerts} == {"delay", "compensation", "approval"}
    assert "not a legal deadline" in next(
        item["detail"] for item in alerts if item["kind"] == "delay"
    )
    deadline.due_date = entered.date() - timedelta(days=1)
    assert "deadline" in {
        item["kind"] for item in build_alerts(rows, history, [doc], [deadline], now=now)
    }
    compensation.status = CompensationState.DISBURSED
    doc.status = DocumentStatus.VERIFIED
    case.current_stage = CaseStage.POSSESSION
    assert not any(
        item["kind"] in ("delay", "compensation", "approval")
        for item in build_alerts(rows, history, [doc], [], now=now)
    )


def test_monthly_comparison_uses_equal_elapsed_windows():
    now = datetime(2026, 9, 6, 12, tzinfo=UTC)
    history = [
        Row(changed_at=datetime(2026, month, day, tzinfo=UTC))
        for month, day in [(9, 2), (9, 3), (8, 2), (8, 20)]
    ]
    trend = monthly_trend(history, now=now)
    assert (trend["current_transitions"], trend["previous_transitions"], trend["difference"]) == (
        2,
        1,
        1,
    )


def test_operations_reports_alerts_and_access_boundaries(client):
    suffix = uuid.uuid4().hex
    accounts = {
        role: register(client, role, suffix)
        for role in ("project_authority", "officer", "landowner", "senior_admin")
    }
    manager, officer, citizen = [
        authorization(accounts[role]) for role in ("project_authority", "officer", "landowner")
    ]
    outsider = authorization(register(client, "landowner", f"outside-{suffix}"))
    project = client.post(
        "/projects",
        headers=manager,
        json={
            "name": f"Operations {suffix}",
            "project_type": "Highway",
            "state": "Maharashtra",
            "district": "Pune",
        },
    ).json()
    parcel_response = client.post(
        f"/projects/{project['id']}/parcels",
        headers=manager,
        json={
            "khasra_survey_no": "गट-१४२/२",
            "polygon": [[[73, 18], [73.001, 18], [73.001, 18.001], [73, 18.001], [73, 18]]],
        },
    )
    assert parcel_response.status_code == 201, parcel_response.text
    parcel = parcel_response.json()
    client.post(
        f"/parcels/{parcel['id']}/landowners",
        headers=manager,
        json={
            "name": "Synthetic Owner",
            "contact": "test@example.test",
            "user_id": accounts["landowner"]["user"]["id"],
        },
    )
    case = client.post(
        "/cases",
        headers=manager,
        json={
            "parcel_id": parcel["id"],
            "assigned_officer_id": accounts["officer"]["user"]["id"],
            "affected_family_count": 3,
        },
    ).json()
    case_id = case["id"]
    assert (
        client.get(f"/cases/{case_id}/operations", headers=citizen).json()["compensation"] is None
    )
    payment = {
        "status": "approved",
        "assessed_amount": "10000.25",
        "disbursed_amount": "2000.10",
        "due_date": (datetime.now(UTC).date() - timedelta(days=2)).isoformat(),
        "reference": "Synthetic award register 14",
    }
    for unauthorized in (citizen, officer):
        assert (
            client.put(
                f"/cases/{case_id}/compensation", headers=unauthorized, json=payment
            ).status_code
            == 403
        )
    response = client.put(f"/cases/{case_id}/compensation", headers=manager, json=payment)
    assert response.status_code == 200, response.text
    assert response.json()["assessed_amount"] == "10000.25"
    rr = client.put(
        f"/cases/{case_id}/rr",
        headers=manager,
        json={
            "rehabilitation_stage": "in_progress",
            "families_supported": 2,
            "notes": "Synthetic R&R register",
        },
    )
    assert rr.status_code == 200, rr.text
    assert (
        client.patch(
            f"/cases/{case_id}/families",
            headers=manager,
            json={"affected_family_count": 1, "displaced_family_count": 0},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            f"/cases/{case_id}/families",
            headers=manager,
            json={"affected_family_count": 3, "displaced_family_count": 2},
        ).status_code
        == 200
    )
    deadline = client.post(
        f"/cases/{case_id}/deadlines",
        headers=manager,
        json={
            "stage": "verification",
            "basis": "operational",
            "due_date": payment["due_date"],
            "reference": "Synthetic review target",
        },
    )
    assert deadline.status_code == 201, deadline.text
    summary = client.get(f"/dashboard/summary?project_id={project['id']}", headers=manager)
    assert summary.status_code == 200, summary.text
    data = summary.json()
    assert (
        data["affected_families"],
        data["displaced_families"],
        data["rr_families_supported"],
        data["deadline_breaches"],
    ) == (3, 2, 2, 1)
    assert data["disbursed_amount"] == "2000.10"
    assert data["area_notified_hectares"] > 0
    for kind in ("project", "state", "district", "compensation"):
        report = client.get(
            f"/reports/{kind}?project_id={project['id']}&columns=group,case_count,disbursed_amount",
            headers=manager,
        )
        assert report.status_code == 200, report.text
        assert "2000.10" in report.text
    assert client.get("/reports/project", headers=citizen).status_code == 403
    assert client.get("/reports/project?columns=password_hash", headers=manager).status_code == 422
    inbox = client.get("/alerts", headers=citizen)
    assert inbox.status_code == 200, inbox.text
    assert {item["kind"] for item in inbox.json()["items"]} == {"compensation", "deadline"}
    key = inbox.json()["items"][0]["key"]
    assert client.put("/alerts/read", params={"key": key}, headers=outsider).status_code == 404
    for _ in range(2):
        assert client.put("/alerts/read", params={"key": key}, headers=citizen).status_code == 200
    assert any(item["read"] for item in client.get("/alerts", headers=citizen).json()["items"])
    assert client.get("/alerts", headers=outsider).json()["items"] == []
    for path in (
        f"/cases/{case_id}/operations",
        f"/cases/{case_id}/compensation",
        f"/cases/{case_id}/rr",
        f"/parcels/{parcel['id']}",
        f"/projects/{project['id']}",
    ):
        assert client.get(path, headers=outsider).status_code == 404
    assert client.get("/gis/parcels", headers=outsider).json() == []
    geometry = client.get("/gis/parcels", headers=citizen)
    assert geometry.status_code == 200, geometry.text
    assert [row["case_id"] for row in geometry.json()] == [case_id]
    assert client.put("/me/preferences", json={"locale": "mr"}, headers=citizen).json() == {
        "locale": "mr"
    }
    assert client.get("/me/preferences", headers=citizen).json()["locale"] == "mr"
    grievance = client.post(
        f"/cases/{case_id}/grievances",
        headers=citizen,
        json={"description": "My compensation payment is delayed"},
    ).json()
    response = client.patch(
        f"/grievances/{grievance['id']}",
        headers=officer,
        json={"status": "resolved", "response": "Synthetic payment record reviewed"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["description"] == "My compensation payment is delayed"
    assert (
        client.get(f"/dashboard/summary?project_id={project['id']}", headers=manager).json()[
            "open_grievances"
        ]
        == 0
    )
    assert client.delete(f"/cases/{case_id}/records/rr", headers=citizen).status_code == 403
    assert client.delete(f"/cases/{case_id}/records/rr", headers=manager).status_code == 204
    assert client.get(f"/cases/{case_id}/rr", headers=citizen).json() is None
    staff = client.post(
        "/auth/users",
        headers=authorization(accounts["senior_admin"]),
        json={
            "name": "Provisioned Officer",
            "email": f"staff-{suffix}@example.test",
            "password": "SecureTest123!",
            "role": "officer",
        },
    )
    assert staff.status_code == 201, staff.text


def test_new_master_rules_do_not_block_reading_legacy_projects():
    legacy = ProjectResponse(
        id=uuid.uuid4(),
        name="Legacy project",
        project_type="Road widening",
        state="Maharashtra",
        district="Pune",
        status="active",
        created_at=datetime.now(UTC),
    )
    assert legacy.project_type == "Road widening"
    with pytest.raises(ValidationError):
        CompensationWrite(status="assessed", reference="   ")
