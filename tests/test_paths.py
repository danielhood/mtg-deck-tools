"""Project path resolution."""

from __future__ import annotations

from pathlib import Path

from mtg_deck_tools.paths import _resolve_project_root


def test_resolve_project_root_env(monkeypatch, tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("MTG_PROJECT_ROOT", str(root))
    assert _resolve_project_root() == root
