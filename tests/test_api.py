"""HTTP API contract."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from mtg_deck_tools.api.app import create_app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_stats_missing_db(client: TestClient, monkeypatch, tmp_path) -> None:
    missing = tmp_path / "nope.db"
    monkeypatch.setenv("MTG_DB_PATH", str(missing))
    response = client.get("/api/v1/stats")
    assert response.status_code == 404


def test_openapi_schema(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "MTG Deck Tools API"
    paths = schema["paths"]
    assert "/health" in paths
    assert "/api/v1/generate" in paths
    assert "DeckCriteria" in schema["components"]["schemas"]
