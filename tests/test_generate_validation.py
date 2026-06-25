"""Generate must reject decks that fail Commander validation."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from mtg_deck_tools.builder.generate import run_generate
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.slots import load_slot_template_config


def _minimal_deck_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known
        ) VALUES (?, ?, ?, ?, ?, ?, '[]', 1, ?, 0, 100, 1.0, 1)
        """,
        (
            "cmd-1",
            "Test Commander",
            "Legendary Creature — Elf",
            "{2}{G}",
            3.0,
            json.dumps(["G"]),
            1,
        ),
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land,
            edhrec_rank, price_usd, price_known, oracle_text
        ) VALUES (?, ?, ?, ?, ?, ?, '[]', 1, 0, 0, 1000, 1.0, 1, ?)
        """,
        (
            "ramp-1",
            "Ramp Rock",
            "Artifact",
            "{2}",
            2.0,
            json.dumps(["G"]),
            "Add {G}",
        ),
    )
    conn.execute(
        """
        INSERT INTO card_mechanic_tags (oracle_id, tag, layer, source)
        VALUES (?, 'ramp', 'theme', 'test')
        """,
        ("ramp-1",),
    )
    conn.commit()


@pytest.fixture
def deck_db_file(tmp_path: Path) -> Path:
    db_path = tmp_path / "cards.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    _minimal_deck_db(conn)
    conn.close()
    return db_path


def test_run_generate_rejects_incomplete_deck(deck_db_file: Path, tmp_path: Path) -> None:
    """Sparse pool + tight budget must not save a short maindeck."""
    slot_config = load_slot_template_config()
    criteria = DeckCriteria(
        colors=["G"],
        commander_oracle_ids=["cmd-1"],
        slot_template=dict(slot_config.default),
        budget_usd=1.0,
        seed=1,
    )
    with pytest.raises(RuntimeError, match="valid deck"):
        run_generate(
            db_path=deck_db_file,
            criteria=criteria,
            output_dir=tmp_path / "out",
        )
