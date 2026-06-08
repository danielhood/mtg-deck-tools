"""Saved deck library HTTP API (UX7f)."""

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
def library_env(tmp_path, monkeypatch):
    cards_db = tmp_path / "cards.db"
    decks_db = tmp_path / "decks.db"
    monkeypatch.setenv("MTG_DB_PATH", str(cards_db))
    monkeypatch.setenv("MTG_DECKS_PATH", str(decks_db))

    import sqlite3

    conn = sqlite3.connect(cards_db)
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
    return cards_db, decks_db


def _stub_deck() -> dict:
    return {
        "commanders": [{"name": "Test Commander", "color_identity": ["B"]}],
        "criteria": {"colors": ["B"], "themes": ["tokens"]},
        "stats": {"estimated_price_usd": 42.5},
        "cards": [],
    }


def test_library_requires_db(client: TestClient, tmp_path, monkeypatch) -> None:
    missing = tmp_path / "nope.db"
    monkeypatch.setenv("MTG_DB_PATH", str(missing))
    response = client.get("/api/v1/decks")
    assert response.status_code == 404


def test_generate_auto_saves_and_returns_id(client: TestClient, library_env) -> None:
    cards_db, _ = library_env
    response = client.post(
        "/api/v1/generate",
        json={
            "stub": True,
            "db_path": str(cards_db),
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
    assert "json_path" not in body or body["json_path"] is None


def test_library_crud(client: TestClient, library_env) -> None:
    cards_db, decks_db = library_env
    generated = client.post(
        "/api/v1/generate",
        json={
            "stub": True,
            "db_path": str(cards_db),
            "criteria": {
                "themes": ["tokens"],
                "commander_oracle_ids": ["cmd-1"],
            },
        },
    ).json()
    deck_id = generated["id"]

    listed = client.get("/api/v1/decks", params={"decks": str(decks_db)}).json()
    assert len(listed) == 1
    assert listed[0]["id"] == deck_id
    assert listed[0]["commander_names"] == ["Test Commander"]
    assert listed[0]["themes"] == ["tokens"]

    detail = client.get(f"/api/v1/decks/{deck_id}", params={"decks": str(decks_db)}).json()
    assert detail["deck"]["commanders"][0]["name"] == "Test Commander"

    renamed = client.patch(
        f"/api/v1/decks/{deck_id}",
        params={"decks": str(decks_db)},
        json={"name": "Simic tokens"},
    ).json()
    assert renamed["name"] == "Simic tokens"

    delete = client.delete(f"/api/v1/decks/{deck_id}", params={"decks": str(decks_db)})
    assert delete.status_code == 204
    assert client.get(f"/api/v1/decks/{deck_id}", params={"decks": str(decks_db)}).status_code == 404


def test_library_search_and_sort(client: TestClient, library_env, monkeypatch) -> None:
    _, decks_db = library_env
    monkeypatch.setenv("MTG_DECKS_PATH", str(decks_db))

    from mtg_deck_tools.service.library import save_deck_to_library

    save_deck_to_library(_stub_deck(), deck_id="a", name="Alpha")
    save_deck_to_library(_stub_deck(), deck_id="b", name="Bravo")

    by_name = client.get("/api/v1/decks", params={"sort": "name"}).json()
    assert [row["name"] for row in by_name] == ["Alpha", "Bravo"]

    filtered = client.get("/api/v1/decks", params={"q": "alpha"}).json()
    assert len(filtered) == 1
    assert filtered[0]["id"] == "a"
