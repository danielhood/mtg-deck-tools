"""Deck generation facades."""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mtg_deck_tools.builder.generate import run_generate
from mtg_deck_tools.builder.reload import run_generate_from_deck
from mtg_deck_tools.builder.stub import run_generate_stub
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.service.dto import GenerateFromDeckRequest, GenerateRequest, GenerateResponse


@dataclass(frozen=True)
class GenerateResult:
    json_path: Path
    md_path: Path
    deck: dict[str, Any] | None = None


def _load_deck_dict(json_path: Path) -> dict[str, Any]:
    return json.loads(json_path.read_text(encoding="utf-8"))


def _md_path_for_json(json_path: Path) -> Path:
    """Companion markdown path for a ``.deck.json`` (or legacy ``.json``) output."""
    name = json_path.name
    if name.endswith(".deck.json"):
        return json_path.with_name(f"{name[: -len('.deck.json')]}.md")
    return json_path.with_suffix(".md")


def _to_response(
    result: GenerateResult,
    *,
    include_deck: bool,
    include_markdown: bool = False,
) -> GenerateResponse:
    deck = result.deck
    if include_deck and deck is None:
        deck = _load_deck_dict(result.json_path)
    markdown = None
    if include_markdown and result.md_path.is_file():
        markdown = result.md_path.read_text(encoding="utf-8")
    return GenerateResponse(
        json_path=str(result.json_path),
        md_path=str(result.md_path),
        deck=deck if include_deck else None,
        markdown=markdown,
    )


def generate_deck(
    request: GenerateRequest,
    *,
    include_deck: bool = False,
    include_markdown: bool = False,
) -> GenerateResponse:
    db_path = Path(request.db_path) if request.db_path else None
    output_dir = Path(request.output_dir) if request.output_dir else None

    kwargs: dict = dict(
        db_path=db_path,
        seed=request.seed,
        colors=request.colors,
        themes=request.themes,
        criteria=request.criteria,
        output_dir=output_dir,
    )
    if request.stub:
        json_path = run_generate_stub(**kwargs)
    else:
        json_path = run_generate(
            **kwargs,
            strict_budget=request.strict_budget,
            strict_dependencies=request.strict_dependencies,
            repair_dependencies=request.repair_dependencies,
            prefer_available=request.prefer_available,
            commander_names=request.commander_names,
        )
    result = GenerateResult(json_path=json_path, md_path=_md_path_for_json(json_path))
    return _to_response(result, include_deck=include_deck, include_markdown=include_markdown)


def generate_deck_from_saved(
    request: GenerateFromDeckRequest,
    *,
    include_deck: bool = False,
    include_markdown: bool = False,
) -> GenerateResponse:
    deck_path, temp_input = _resolve_deck_path(request)
    db_path = Path(request.db_path) if request.db_path else None
    output_dir = Path(request.output_dir) if request.output_dir else None

    try:
        json_path = run_generate_from_deck(
            deck_path,
            db_path=db_path,
            seed=request.seed,
            output_dir=output_dir,
            refill_slot=request.refill_slot,
            strict_budget=request.strict_budget,
            strict_dependencies=request.strict_dependencies,
            repair_dependencies=request.repair_dependencies,
            prefer_available=request.prefer_available,
        )
    finally:
        if temp_input:
            deck_path.unlink(missing_ok=True)

    result = GenerateResult(json_path=json_path, md_path=_md_path_for_json(json_path))
    return _to_response(result, include_deck=include_deck, include_markdown=include_markdown)


def generate_deck_cli(
    *,
    stub: bool = False,
    db_path: Path | None = None,
    seed: int | None = None,
    colors: list[str] | None = None,
    themes: list[str] | None = None,
    criteria: DeckCriteria | None = None,
    output_dir: Path | None = None,
    strict_budget: bool = False,
    strict_dependencies: bool = False,
    repair_dependencies: bool = False,
    prefer_available: bool = False,
    commander_names: list[str] | None = None,
) -> GenerateResult:
    """CLI-oriented generate without wrapping in GenerateRequest."""
    request = GenerateRequest(
        criteria=criteria,
        colors=colors,
        themes=themes,
        seed=seed,
        db_path=str(db_path) if db_path else None,
        output_dir=str(output_dir) if output_dir else None,
        stub=stub,
        strict_budget=strict_budget,
        strict_dependencies=strict_dependencies,
        repair_dependencies=repair_dependencies,
        prefer_available=prefer_available,
        commander_names=commander_names,
    )
    response = generate_deck(request, include_deck=False)
    json_path = Path(response.json_path)
    return GenerateResult(
        json_path=json_path,
        md_path=_md_path_for_json(json_path),
    )


def _resolve_deck_path(request: GenerateFromDeckRequest) -> tuple[Path, bool]:
    """Return (path, is_temporary)."""
    if request.deck_path and request.deck:
        raise ValueError("Provide either deck_path or deck, not both.")
    if request.deck_path:
        return Path(request.deck_path), False
    if request.deck is None:
        raise ValueError("deck_path or deck is required.")

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".deck.json",
        delete=False,
        encoding="utf-8",
    )
    try:
        json.dump(request.deck, tmp)
        tmp.close()
        return Path(tmp.name), True
    except Exception:
        Path(tmp.name).unlink(missing_ok=True)
        raise
