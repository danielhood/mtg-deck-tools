"""Import pipeline facade."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from mtg_deck_tools.import_.pipeline import run_import
from mtg_deck_tools.service.dto import ImportResponse


def import_oracle_cards(
    *,
    json_path: Path | None = None,
    db_path: Path | None = None,
    progress: Callable[[str], None] | None = None,
) -> ImportResponse:
    result = run_import(json_path=json_path, db_path=db_path, progress=progress)
    return ImportResponse(
        source_file=str(result["source_file"]),
        source_count=int(result["source_count"]),
        playable_count=int(result["playable_count"]),
        tag_count=int(result["tag_count"]),
        effect_count=int(result["effect_count"]),
        db_path=str(result["db_path"]),
    )
