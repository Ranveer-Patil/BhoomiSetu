import asyncio
import uuid

import asyncpg
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import hash_password


def register(client: TestClient, role: str, suffix: str) -> dict:
    if role != "landowner":

        async def provision():
            connection = await asyncpg.connect(
                settings.database_url.replace("postgresql+asyncpg", "postgresql")
            )
            try:
                await connection.execute(
                    "INSERT INTO users (id, name, email, role, password_hash) "
                    "VALUES ($1,$2,$3,$4,$5)",
                    uuid.uuid4(),
                    f"Test {role}",
                    f"{role}-{suffix}@example.test",
                    role.upper(),
                    hash_password("SecureTest123!"),
                )
            finally:
                await connection.close()

        asyncio.run(provision())
        response = client.post(
            "/auth/login",
            json={"email": f"{role}-{suffix}@example.test", "password": "SecureTest123!"},
        )
        assert response.status_code == 200, response.text
        return response.json()
    response = client.post(
        "/auth/register",
        json={
            "name": f"Test {role}",
            "email": f"{role}-{suffix}@example.test",
            "password": "SecureTest123!",
            "role": role,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def authorization(token_response: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_response['access_token']}"}


def test_complete_phase_one_case_journey(client: TestClient) -> None:
    suffix = uuid.uuid4().hex
    accounts = {
        role: register(client, role, suffix)
        for role in (
            "landowner",
            "officer",
            "project_authority",
            "district_admin",
            "senior_admin",
        )
    }
    authority_headers = authorization(accounts["project_authority"])

    forbidden = client.post(
        "/projects",
        headers=authorization(accounts["landowner"]),
        json={
            "name": "Forbidden project",
            "project_type": "Highway",
            "state": "Maharashtra",
            "district": "Pune",
        },
    )
    assert forbidden.status_code == 403

    project_response = client.post(
        "/projects",
        headers=authority_headers,
        json={
            "name": f"Phase One Test {suffix}",
            "project_type": "Highway",
            "state": "Maharashtra",
            "district": "Pune",
            "status": "active",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    parcel_response = client.post(
        f"/projects/{project_id}/parcels",
        headers=authority_headers,
        json={
            "khasra_survey_no": f"TEST-{suffix[:8]}",
            "polygon": [
                [
                    [73.82, 18.50],
                    [73.823, 18.50],
                    [73.823, 18.503],
                    [73.82, 18.503],
                    [73.82, 18.50],
                ]
            ],
        },
    )
    assert parcel_response.status_code == 201, parcel_response.text
    parcel = parcel_response.json()
    assert parcel["polygon"]["type"] == "Polygon"

    landowner_response = client.post(
        f"/parcels/{parcel['id']}/landowners",
        headers=authority_headers,
        json={
            "name": "Test Landowner",
            "contact": "demo@example.test",
            "user_id": accounts["landowner"]["user"]["id"],
        },
    )
    assert landowner_response.status_code == 201, landowner_response.text

    case_response = client.post(
        "/cases",
        headers=authority_headers,
        json={
            "parcel_id": parcel["id"],
            "assigned_officer_id": accounts["officer"]["user"]["id"],
            "affected_family_count": 2,
        },
    )
    assert case_response.status_code == 201, case_response.text
    case_id = case_response.json()["id"]

    outsider = register(client, "landowner", f"outsider-{suffix}")
    unassigned_officer = register(client, "officer", f"unassigned-{suffix}")
    citizen_cases = client.get("/cases", headers=authorization(accounts["landowner"]))
    assert citizen_cases.status_code == 200
    assert [row["id"] for row in citizen_cases.json()] == [case_id]
    for account in (outsider, unassigned_officer):
        headers = authorization(account)
        assert client.get("/cases", headers=headers).json() == []
        assert client.get(f"/cases/{case_id}", headers=headers).status_code == 404
    forbidden_transition = client.post(
        f"/cases/{case_id}/transition",
        headers=authorization(unassigned_officer),
        json={"new_stage": "verification", "reason": "Not assigned"},
    )
    assert forbidden_transition.status_code == 404

    officer_headers = authorization(accounts["officer"])
    for stage in ("verification", "objection", "award", "compensation", "possession"):
        transition = client.post(
            f"/cases/{case_id}/transition",
            headers=officer_headers,
            json={"new_stage": stage, "reason": "Integration test"},
        )
        assert transition.status_code == 200, transition.text
        assert transition.json()["current_stage"] == stage

    invalid_transition = client.post(
        f"/cases/{case_id}/transition",
        headers=officer_headers,
        json={"new_stage": "notification"},
    )
    assert invalid_transition.status_code == 409

    case_detail = client.get(f"/cases/{case_id}", headers=authority_headers)
    assert case_detail.status_code == 200
    assert len(case_detail.json()["stage_history"]) == 5

    filtered_cases = client.get(
        f"/cases?project_id={project_id}&stage=possession",
        headers=authority_headers,
    )
    assert filtered_cases.status_code == 200
    assert [row["id"] for row in filtered_cases.json()] == [case_id]

    async def count_audit_rows() -> int:
        connection = await asyncpg.connect(
            settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        )
        try:
            return await connection.fetchval(
                "SELECT count(*) FROM audit_log WHERE action LIKE $1",
                f"case.transition:{case_id}:%",
            )
        finally:
            await connection.close()

    assert asyncio.run(count_audit_rows()) == 5
