"""Scryfall oracle bulk auto-download."""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mtg_deck_tools.import_.scryfall_bulk import (
    auto_download_enabled,
    download_oracle_cards_json,
    ensure_oracle_cards_json,
    fetch_oracle_bulk_metadata,
    oracle_bulk_filename,
)
from mtg_deck_tools.service.import_ import ensure_cards_database


def test_oracle_bulk_filename() -> None:
    assert (
        oracle_bulk_filename("2026-05-28T21:06:54.000+00:00")
        == "oracle-cards-20260528210654.json"
    )


def test_auto_download_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MTG_AUTO_DOWNLOAD", raising=False)
    assert auto_download_enabled() is True
    monkeypatch.setenv("MTG_AUTO_DOWNLOAD", "0")
    assert auto_download_enabled() is False
    monkeypatch.setenv("MTG_AUTO_DOWNLOAD", "false")
    assert auto_download_enabled() is False


def _minimal_card() -> dict[str, object]:
    return {
        "oracle_id": "test-card",
        "id": "test-card",
        "name": "Test Card",
        "layout": "normal",
        "lang": "en",
        "type_line": "Creature",
        "oracle_text": "Test.",
        "mana_cost": "{1}",
        "cmc": 1.0,
        "color_identity": ["G"],
        "legalities": {"commander": "legal"},
    }


def test_download_oracle_cards_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metadata = {
        "download_uri": "https://example.test/oracle-cards.json",
        "updated_at": "2026-05-28T21:06:54.000+00:00",
        "size": 42,
        "name": "Oracle Cards",
    }
    bulk_payload = json.dumps([_minimal_card()]).encode("utf-8")

    def fake_urlopen(request, timeout=60):
        url = request.full_url
        if "bulk-data/oracle-cards" in url:
            payload = json.dumps(metadata).encode("utf-8")
            response = MagicMock()
            response.read.return_value = payload
        else:
            response = MagicMock()
            response.read.side_effect = [
                bulk_payload[i : i + 16] for i in range(0, len(bulk_payload), 16)
            ] + [b""]
        response.__enter__.return_value = response
        response.__exit__.return_value = None
        return response

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    path = download_oracle_cards_json(directory=tmp_path)
    assert path == tmp_path / "oracle-cards-20260528210654.json"
    assert json.loads(path.read_text(encoding="utf-8")) == [_minimal_card()]


def test_ensure_oracle_cards_json_uses_existing(tmp_path: Path) -> None:
    existing = tmp_path / "oracle-cards-20260101120000.json"
    existing.write_text("[]", encoding="utf-8")

    path = ensure_oracle_cards_json(directory=tmp_path, auto_download=False)
    assert path == existing


def test_ensure_oracle_cards_json_downloads_when_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "mtg_deck_tools.import_.scryfall_bulk.download_oracle_cards_json",
        lambda **kwargs: tmp_path / "oracle-cards-20260528210654.json",
    )

    path = ensure_oracle_cards_json(directory=tmp_path, auto_download=True)
    assert path.name == "oracle-cards-20260528210654.json"


def test_ensure_oracle_cards_json_raises_when_disabled(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ensure_oracle_cards_json(directory=tmp_path, auto_download=False)


def test_fetch_oracle_bulk_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "download_uri": "https://example.test/bulk.json",
        "updated_at": "2026-05-28T21:06:54.000+00:00",
        "size": 100,
        "name": "Oracle Cards",
    }

    def fake_urlopen(request, timeout=60):
        response = io.BytesIO(json.dumps(payload).encode("utf-8"))
        response.__enter__ = lambda: response
        response.__exit__ = lambda *args: None
        return response

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    meta = fetch_oracle_bulk_metadata()
    assert meta.download_uri == payload["download_uri"]
    assert meta.size == 100


def test_ensure_cards_database_builds_from_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    json_path = tmp_path / "oracle-cards-test.json"
    json_path.write_text(json.dumps([_minimal_card()]), encoding="utf-8")
    db_path = tmp_path / "cards.db"

    monkeypatch.setattr(
        "mtg_deck_tools.import_.pipeline.ensure_oracle_cards_json",
        lambda **kwargs: json_path,
    )

    result = ensure_cards_database(db_path=db_path, auto_download=True)
    assert result == db_path
    assert db_path.exists()
