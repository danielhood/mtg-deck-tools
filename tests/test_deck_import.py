"""Integration tests for text deck import (UX13-MVP)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from mtg_deck_tools.api.app import create_app  # noqa: E402
from mtg_deck_tools.db.schema import apply_schema  # noqa: E402
from mtg_deck_tools.deck_import.resolve import ResolveError  # noqa: E402
from mtg_deck_tools.service.deck_import import import_deck_from_text  # noqa: E402


def _insert_card(
    conn: sqlite3.Connection,
    *,
    oracle_id: str,
    name: str,
    color_identity: list[str],
    type_line: str,
    commander_eligible: int = 0,
    commander_legal: int = 1,
    is_basic_land: int = 0,
    cmc: float = 2,
    price_usd: float = 1.0,
) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, color_identity, commander_legal,
            commander_eligible, is_basic_land, keywords, mana_cost, cmc,
            price_usd, price_known, produced_mana
        ) VALUES (?, ?, ?, ?, ?, ?, ?, '[]', '{1}', ?, ?, 1, '[]')
        """,
        (
            oracle_id,
            name,
            type_line,
            json.dumps(color_identity),
            commander_legal,
            commander_eligible,
            is_basic_land,
            cmc,
            price_usd,
        ),
    )


@pytest.fixture
def import_env(tmp_path: Path) -> tuple[Path, Path]:
    cards_db = tmp_path / "cards.db"
    decks_db = tmp_path / "decks.db"

    conn = sqlite3.connect(cards_db)
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    _insert_card(
        conn,
        oracle_id="cmd-meren",
        name="Meren of Clan Nel Toth",
        color_identity=["B", "G"],
        type_line="Legendary Creature — Human Shaman",
        commander_eligible=1,
        cmc=4,
        price_usd=5.0,
    )
    _insert_card(
        conn,
        oracle_id="grave-pact",
        name="Grave Pact",
        color_identity=["B"],
        type_line="Enchantment",
        cmc=3,
        price_usd=12.0,
    )
    _insert_card(
        conn,
        oracle_id="sol-ring",
        name="Sol Ring",
        color_identity=[],
        type_line="Artifact",
        cmc=1,
        price_usd=2.0,
    )
    _insert_card(
        conn,
        oracle_id="forest",
        name="Forest",
        color_identity=[],
        type_line="Basic Land — Forest",
        is_basic_land=1,
        cmc=0,
        price_usd=0.05,
    )
    conn.commit()
    conn.close()
    return cards_db, decks_db


SAMPLE_TEXT = """
Commander
Meren of Clan Nel Toth

Deck
1x Grave Pact
Sol Ring
Forest x3
"""


def test_import_deck_from_text_saves_library(import_env: tuple[Path, Path]) -> None:
    cards_db, decks_db = import_env
    result = import_deck_from_text(
        SAMPLE_TEXT,
        db_path=cards_db,
        decks_path=decks_db,
    )
    assert result.id
    assert result.name == "Meren of Clan Nel Toth"
    assert result.deck["commanders"][0]["name"] == "Meren of Clan Nel Toth"
    cards = result.deck["cards"]
    assert len(cards) == 3
    slots = {card["name"]: card["slot"] for card in cards}
    assert slots["Grave Pact"] == "imported"
    assert slots["Forest"] == "lands"
    assert result.deck.get("dependency_report") is not None
    assert result.deck.get("stats") is not None


def test_import_requires_commander(import_env: tuple[Path, Path]) -> None:
    cards_db, decks_db = import_env
    with pytest.raises(ValueError, match="Commander required"):
        import_deck_from_text("Deck\nSol Ring", db_path=cards_db, decks_path=decks_db)


def test_import_cli_commander_flag(import_env: tuple[Path, Path]) -> None:
    cards_db, decks_db = import_env
    result = import_deck_from_text(
        "Deck\nSol Ring",
        commander_names=["Meren of Clan Nel Toth"],
        db_path=cards_db,
        decks_path=decks_db,
    )
    assert result.deck["commanders"][0]["oracle_id"] == "cmd-meren"


def test_import_unknown_card_fails(import_env: tuple[Path, Path]) -> None:
    cards_db, decks_db = import_env
    text = """
    Commander
    Meren of Clan Nel Toth

    Deck
    Not A Real Card
    """
    with pytest.raises(ResolveError, match="unknown"):
        import_deck_from_text(text, db_path=cards_db, decks_path=decks_db)


def test_import_ambiguous_name_fails(import_env: tuple[Path, Path]) -> None:
    cards_db, decks_db = import_env
    conn = sqlite3.connect(cards_db)
    _insert_card(
        conn,
        oracle_id="forest-2",
        name="Forest",
        color_identity=[],
        type_line="Basic Land — Forest",
        is_basic_land=1,
        cmc=0,
    )
    conn.commit()
    conn.close()

    text = """
    Commander
    Meren of Clan Nel Toth

    Deck
    Forest
    """
    with pytest.raises(ResolveError, match="ambiguous"):
        import_deck_from_text(text, db_path=cards_db, decks_path=decks_db)


def test_api_import_deck(import_env: tuple[Path, Path]) -> None:
    cards_db, decks_db = import_env
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/decks/import",
        json={"text": SAMPLE_TEXT},
        params={"db": str(cards_db)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"]
    assert body["deck"]["cards"]
