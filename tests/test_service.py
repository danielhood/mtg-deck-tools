"""Service layer facades."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.service import (
    GenerateFromDeckRequest,
    GenerateRequest,
    generate_deck,
    get_database_stats,
)
from mtg_deck_tools.service.generate import _resolve_deck_path


def test_get_database_stats(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "cards.db"
    monkeypatch.setattr(
        "mtg_deck_tools.service.stats.DEFAULT_DB_PATH",
        db,
    )
    assert not db.exists()
    with pytest.raises(FileNotFoundError):
        get_database_stats(db)


def test_resolve_deck_path_requires_source() -> None:
    with pytest.raises(ValueError, match="deck_path or deck"):
        _resolve_deck_path(GenerateFromDeckRequest())


def test_resolve_deck_path_from_document(tmp_path: Path) -> None:
    doc = {"schema_version": "1.0", "criteria": {"themes": []}}
    path, is_temp = _resolve_deck_path(GenerateFromDeckRequest(deck=doc))
    assert is_temp
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == "1.0"
    path.unlink()


def test_generate_request_accepts_criteria() -> None:
    req = GenerateRequest(criteria=DeckCriteria(colors=["G"], seed=1))
    assert req.criteria is not None
    assert req.criteria.colors == ["G"]


def test_generate_stub_requires_db(tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    with pytest.raises(FileNotFoundError):
        generate_deck(
            GenerateRequest(stub=True, db_path=str(missing)),
        )
