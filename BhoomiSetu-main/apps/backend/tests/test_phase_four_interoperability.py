import time
import uuid

from fastapi.testclient import TestClient

from tests.test_phase_one_api import authorization, register


def test_phase_four_fixtures_and_audit_verification(client: TestClient) -> None:
    suffix = uuid.uuid4().hex
    authority = register(client, "project_authority", suffix)
    senior = register(client, "senior_admin", suffix)
    authority_headers = authorization(authority)
    senior_headers = authorization(senior)

    started = time.monotonic()
    record = client.get(
        "/integrations/apisetu/land-records/KH-101",
        headers=authority_headers,
    )
    elapsed = time.monotonic() - started
    assert record.status_code == 200, record.text
    assert elapsed >= 0.35
    assert record.json()["source"]["is_fixture"] is True
    assert "not live government data" in record.json()["source"]["notice"]
    assert record.json()["survey_number"] == "KH-101"

    deed = client.get(
        "/integrations/apisetu/deeds/MH-PUN-2021-8122",
        headers=authority_headers,
    )
    assert deed.status_code == 200, deed.text
    assert deed.json()["source"]["intended_provider"] == "API Setu / NGDRS"

    project = client.post(
        "/projects",
        headers=authority_headers,
        json={
            "name": f"Audited Project {suffix}",
            "project_type": "Highway",
            "state": "Maharashtra",
            "district": "Pune",
            "status": "active",
        },
    )
    assert project.status_code == 201, project.text

    audit_rows = client.get(
        "/audit-log?action=project.create",
        headers=senior_headers,
    )
    assert audit_rows.status_code == 200, audit_rows.text
    assert any(project.json()["id"] in row["action"] for row in audit_rows.json())

    verified = client.get("/audit-log/verify", headers=senior_headers)
    assert verified.status_code == 200, verified.text
    assert verified.json()["valid"] is True
    assert verified.json()["checked_rows"] > 0
