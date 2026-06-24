"""Wizard HTTP API contract (UX7c-a)."""

from __future__ import annotations

import json

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from mtg_deck_tools.api.app import create_app  # noqa: E402
from mtg_deck_tools.db.schema import apply_schema  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def wizard_db(tmp_path, monkeypatch):
    db_path = tmp_path / "cards.db"
    monkeypatch.setenv("MTG_DB_PATH", str(db_path))
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, color_identity, commander_legal,
            commander_eligible, image_uri
        ) VALUES (?, ?, ?, ?, 1, 1, ?)
        """,
        (
            "cmd-1",
            "Test Commander",
            "Legendary Creature",
            json.dumps(["B"]),
            "https://cards.scryfall.io/normal/front/test.jpg",
        ),
    )
    conn.commit()
    conn.close()
    return db_path


def test_wizard_meta_missing_db(client: TestClient, monkeypatch, tmp_path) -> None:
    missing = tmp_path / "nope.db"
    monkeypatch.setenv("MTG_DB_PATH", str(missing))
    response = client.get("/api/v1/wizard/meta")
    assert response.status_code == 200
    body = response.json()
    assert body["db_ready"] is False
    assert len(body["steps"]) == 7


def test_wizard_meta_ready_db(client: TestClient, wizard_db) -> None:
    response = client.get("/api/v1/wizard/meta")
    assert response.status_code == 200
    body = response.json()
    assert body["db_ready"] is True
    assert body["total_cards"] == 1


def test_wizard_themes(client: TestClient) -> None:
    response = client.get("/api/v1/wizard/themes")
    assert response.status_code == 200
    themes = response.json()
    assert themes
    assert "id" in themes[0]


def test_wizard_slot_template_defaults(client: TestClient) -> None:
    response = client.get("/api/v1/wizard/slot-template/defaults")
    assert response.status_code == 200
    body = response.json()
    assert body["commander_slots"] == 1
    assert body["deck_total"] == 100


def test_wizard_mechanics(client: TestClient) -> None:
    response = client.get("/api/v1/wizard/mechanics")
    assert response.status_code == 200
    mechanics = response.json()
    assert mechanics
    assert all("partner" != row["id"] for row in mechanics)


def test_wizard_synergy_context(client: TestClient) -> None:
    response = client.post(
        "/api/v1/wizard/synergy-context",
        json={"themes": ["tokens"], "include_mechanics": []},
    )
    assert response.status_code == 200
    body = response.json()
    profile_ids = {row["profile_id"] for row in body["activated_profiles"]}
    assert "tokens" in profile_ids


def test_wizard_preflight(client: TestClient) -> None:
    response = client.post(
        "/api/v1/wizard/preflight",
        json={"themes": [], "commander_oracle_ids": []},
    )
    assert response.status_code == 200
    assert "warnings" in response.json()


def test_wizard_rarities(client: TestClient) -> None:
    response = client.get("/api/v1/wizard/rarities")
    assert response.status_code == 200
    rarities = response.json()
    assert [row["id"] for row in rarities] == ["common", "uncommon", "rare", "mythic"]


def test_wizard_commanders_search(client: TestClient, wizard_db) -> None:
    response = client.get(
        "/api/v1/wizard/commanders/search",
        params={"q": "Test", "colors": ["B"], "color_match": "exact"},
    )
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["oracle_id"] == "cmd-1"
    assert rows[0]["image_uri"].startswith("https://")


def test_generate_uses_mtg_db_path_env(client: TestClient, wizard_db, tmp_path, monkeypatch) -> None:
    """Regression: generate must honor MTG_DB_PATH when request omits db_path (Docker)."""
    monkeypatch.setenv("MTG_DECKS_PATH", str(tmp_path / "decks.db"))
    response = client.post(
        "/api/v1/generate",
        json={
            "stub": True,
            "criteria": {
                "themes": [],
                "commander_oracle_ids": ["cmd-1"],
                "seed": 42,
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"]
    assert body["deck"]["commanders"][0]["name"] == "Test Commander"


def test_generate_returns_library_entry(client: TestClient, wizard_db, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MTG_DECKS_PATH", str(tmp_path / "decks.db"))
    response = client.post(
        "/api/v1/generate",
        json={
            "stub": True,
            "db_path": str(wizard_db),
            "criteria": {
                "themes": [],
                "commander_oracle_ids": ["cmd-1"],
                "seed": 42,
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"]
    assert body["deck"] is not None
    assert body["deck"]["commanders"][0]["name"] == "Test Commander"


def test_generate_can_include_markdown(client: TestClient, wizard_db, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MTG_DECKS_PATH", str(tmp_path / "decks.db"))
    response = client.post(
        "/api/v1/generate?include_markdown=true",
        json={
            "stub": True,
            "db_path": str(wizard_db),
            "criteria": {
                "themes": [],
                "commander_oracle_ids": ["cmd-1"],
                "seed": 42,
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["markdown"]
    assert "Test Commander" in body["markdown"]


def test_openapi_includes_wizard_paths(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/api/v1/wizard/meta" in paths
    assert "/api/v1/wizard/commanders/search" in paths
