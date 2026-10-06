from sqlalchemy.exc import OperationalError

from app.api.health import EXPECTED_REVISION
from app.core.database import get_db
from app.main import app


def test_readiness_checks_migrated_postgis_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["revision"] == EXPECTED_REVISION


def test_readiness_reports_unavailable_database_without_leaking_details(client):
    class UnavailableDatabase:
        async def execute(self, _statement):
            raise OperationalError("private connection detail", {}, Exception("secret"))

    async def unavailable_db():
        yield UnavailableDatabase()

    app.dependency_overrides[get_db] = unavailable_db
    try:
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database is not ready"}
        assert client.get("/health").status_code == 200
    finally:
        app.dependency_overrides.pop(get_db, None)
