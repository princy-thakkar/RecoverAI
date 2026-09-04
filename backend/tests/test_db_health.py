"""
Database health tests — use mocks/fakes so a live MongoDB instance is not
required to run the test suite, per the Stage 2 brief.

Covers three states:
1. MONGODB_URI not configured at all.
2. Client failed to initialize at startup (client is None).
3. Client exists — ping succeeds (connected) or fails (not connected).

Also exercises the actual GET /api/db/health endpoint via TestClient for
each of these states so the wiring (route -> check_db_health) is covered,
not just the underlying function.
"""
import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.db import mongodb as mongodb_module
from app.db.mongodb import check_db_health
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mongodb_state():
    """Ensure each test starts from a clean, disconnected state."""
    mongodb_module.mongodb.client = None
    mongodb_module.mongodb.db = None
    yield
    mongodb_module.mongodb.client = None
    mongodb_module.mongodb.db = None


def test_check_db_health_reports_not_configured_when_uri_empty(monkeypatch):
    import app.db.mongodb as m

    monkeypatch.setattr(
        m,
        "get_settings",
        lambda: type(
            "S",
            (),
            {
                "MONGODB_URI": "",
                "MONGODB_DB_NAME": "recoverai",
            },
        )(),
    )

    mongodb_module.mongodb.client = None
    mongodb_module.mongodb.db = None

    result = asyncio.run(check_db_health())

    assert result["connected"] is False
    assert "not configured" in result["detail"].lower()


def test_check_db_health_reports_disconnected_when_client_missing(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.get_settings",
        lambda: type(
            "S", (), {"MONGODB_URI": "mongodb://localhost:27017", "MONGODB_DB_NAME": "recoverai"}
        )(),
    )
    # Patch the reference used inside app.db.mongodb specifically.
    import app.db.mongodb as m

    monkeypatch.setattr(m, "get_settings", lambda: type(
        "S", (), {"MONGODB_URI": "mongodb://localhost:27017", "MONGODB_DB_NAME": "recoverai"}
    )())

    mongodb_module.mongodb.client = None
    result = asyncio.run(check_db_health())
    assert result["connected"] is False
    assert "failed to initialize" in result["detail"].lower()


def test_check_db_health_reports_connected_when_ping_succeeds(monkeypatch):
    import app.db.mongodb as m

    monkeypatch.setattr(m, "get_settings", lambda: type(
        "S", (), {"MONGODB_URI": "mongodb://localhost:27017", "MONGODB_DB_NAME": "recoverai"}
    )())

    fake_client = AsyncMock()
    fake_client.admin.command = AsyncMock(return_value={"ok": 1})
    mongodb_module.mongodb.client = fake_client

    result = asyncio.run(check_db_health())
    assert result["connected"] is True
    assert "recoverai" in result["detail"]


def test_check_db_health_reports_disconnected_when_ping_fails(monkeypatch):
    import app.db.mongodb as m

    monkeypatch.setattr(m, "get_settings", lambda: type(
        "S", (), {"MONGODB_URI": "mongodb://localhost:27017", "MONGODB_DB_NAME": "recoverai"}
    )())

    fake_client = AsyncMock()
    fake_client.admin.command = AsyncMock(side_effect=Exception("connection refused"))
    mongodb_module.mongodb.client = fake_client

    result = asyncio.run(check_db_health())
    assert result["connected"] is False
    assert "ping failed" in result["detail"].lower()


def test_db_health_endpoint_returns_200_and_disconnected_when_not_configured():
    response = client.get("/api/db/health")
    assert response.status_code == 200

    body = response.json()
    assert body["database"] == "mongodb"
    assert body["connected"] is False
    assert "detail" in body


def test_db_health_endpoint_reflects_connected_state(monkeypatch):
    import app.db.mongodb as m

    monkeypatch.setattr(m, "get_settings", lambda: type(
        "S", (), {"MONGODB_URI": "mongodb://localhost:27017", "MONGODB_DB_NAME": "recoverai"}
    )())

    fake_client = AsyncMock()
    fake_client.admin.command = AsyncMock(return_value={"ok": 1})
    mongodb_module.mongodb.client = fake_client

    response = client.get("/api/db/health")
    assert response.status_code == 200

    body = response.json()
    assert body["connected"] is True