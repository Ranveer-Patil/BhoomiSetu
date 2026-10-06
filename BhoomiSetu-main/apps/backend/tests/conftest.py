# ruff: noqa: E402, I001
import os

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://punit@localhost:5432/bhoomsetu_test",
)

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
