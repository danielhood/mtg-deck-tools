"""``mtg-deck-tools serve`` configuration and static UI mount."""

from __future__ import annotations

from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from mtg_deck_tools.api.app import create_app  # noqa: E402
from mtg_deck_tools.api.serve import (  # noqa: E402
    DEFAULT_HOST,
    DEFAULT_PORT,
    serve_config_from_options,
)
from mtg_deck_tools.paths import resolve_db_path, resolve_static_ui_dir  # noqa: E402


def test_serve_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("MTG_SERVE_HOST", raising=False)
    monkeypatch.delenv("MTG_SERVE_PORT", raising=False)
    config = serve_config_from_options()
    assert config.host == DEFAULT_HOST
    assert config.port == DEFAULT_PORT
    assert config.static_dir is None
    assert config.reload is False


def test_serve_config_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("MTG_SERVE_HOST", "0.0.0.0")
    monkeypatch.setenv("MTG_SERVE_PORT", "9000")
    config = serve_config_from_options()
    assert config.host == "0.0.0.0"
    assert config.port == 9000


def test_serve_config_with_ui(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    config = serve_config_from_options(with_ui=True, ui_dir=dist)
    assert config.static_dir == dist


def test_serve_config_with_ui_static_dir_env(monkeypatch, tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    monkeypatch.setenv("MTG_SERVE_STATIC_DIR", str(dist))
    config = serve_config_from_options(with_ui=True)
    assert config.static_dir == dist


def test_mtg_db_path_env(monkeypatch, tmp_path: Path) -> None:
    db = tmp_path / "cards.db"
    db.touch()
    monkeypatch.setenv("MTG_DB_PATH", str(db))
    assert resolve_db_path() == db


def test_mtg_serve_static_dir_env(monkeypatch, tmp_path: Path) -> None:
    ui = tmp_path / "dist"
    ui.mkdir()
    monkeypatch.setenv("MTG_SERVE_STATIC_DIR", str(ui))
    assert resolve_static_ui_dir() == ui


def test_static_ui_mount(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html><body>MTG Deck Tools</body></html>", encoding="utf-8")

    client = TestClient(create_app(static_dir=dist))
    health = client.get("/health")
    assert health.status_code == 200

    ui = client.get("/")
    assert ui.status_code == 200
    assert "MTG Deck Tools" in ui.text

    missing = client.get("/does-not-exist")
    assert missing.status_code == 200
    assert "MTG Deck Tools" in missing.text


def test_static_ui_mount_missing_dir(tmp_path: Path) -> None:
    missing = tmp_path / "dist"
    with pytest.raises(FileNotFoundError, match="Web UI build not found"):
        create_app(static_dir=missing)
