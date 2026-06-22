"""Import pipeline facade."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from mtg_deck_tools.import_.pipeline import run_import
from mtg_deck_tools.import_.scryfall_bulk import auto_download_enabled
from mtg_deck_tools.paths import resolve_db_path
from mtg_deck_tools.service.dto import ImportResponse


def import_oracle_cards(
    *,
    json_path: Path | None = None,
    db_path: Path | None = None,
    progress: Callable[[str], None] | None = None,
    auto_download: bool | None = None,
) -> ImportResponse:
    result = run_import(
        json_path=json_path,
        db_path=db_path,
        progress=progress,
        auto_download=auto_download,
    )
    return ImportResponse(
        source_file=str(result["source_file"]),
        source_count=int(result["source_count"]),
        playable_count=int(result["playable_count"]),
        tag_count=int(result["tag_count"]),
        effect_count=int(result["effect_count"]),
        db_path=str(result["db_path"]),
    )


def ensure_cards_database(
    *,
    db_path: Path | None = None,
    json_path: Path | None = None,
    progress: Callable[[str], None] | None = None,
    auto_download: bool | None = None,
) -> Path:
    """Ensure ``cards.db`` exists, downloading oracle bulk data and importing when needed."""
    path = resolve_db_path(db_path)
    if path.exists():
        return path

    enabled = auto_download_enabled() if auto_download is None else auto_download
    if not enabled:
        raise FileNotFoundError(
            f"Database not found: {path}. Run: mtg-deck-tools import "
            "(or set MTG_AUTO_DOWNLOAD=1 to download from Scryfall automatically)."
        )

    log = progress or (lambda _msg: None)
    log(f"Building card database at {path}...")
    run_import(json_path=json_path, db_path=path, progress=progress, auto_download=enabled)
    return path
