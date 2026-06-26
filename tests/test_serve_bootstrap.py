"""``serve`` startup database bootstrap."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from mtg_deck_tools.cli.main import app


def test_serve_starts_without_db_when_auto_download_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_path = tmp_path / "cards.db"
    monkeypatch.setenv("MTG_AUTO_DOWNLOAD", "0")
    monkeypatch.setenv("MTG_DB_PATH", str(db_path))
    started: list[object] = []
    monkeypatch.setattr(
        "mtg_deck_tools.cli.main.run_server",
        lambda config: started.append(config),
    )

    result = CliRunner().invoke(app, ["serve"])

    assert result.exit_code == 0
    assert started
    assert not db_path.exists()


def test_serve_bootstraps_when_auto_download_enabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_path = tmp_path / "cards.db"
    monkeypatch.setenv("MTG_AUTO_DOWNLOAD", "1")
    monkeypatch.setenv("MTG_DB_PATH", str(db_path))
    monkeypatch.setattr(
        "mtg_deck_tools.cli.main.ensure_cards_database",
        lambda **kwargs: db_path.touch(),
    )
    started: list[object] = []
    monkeypatch.setattr(
        "mtg_deck_tools.cli.main.run_server",
        lambda config: started.append(config),
    )

    result = CliRunner().invoke(app, ["serve"])

    assert result.exit_code == 0
    assert started
    assert db_path.exists()
