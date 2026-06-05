"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from mtg_deck_tools import __version__
from mtg_deck_tools.service import (
    GenerateFromDeckRequest,
    GenerateRequest,
    ImportRequest,
    generate_deck,
    generate_deck_from_saved,
    get_database_stats,
    import_oracle_cards,
)
from mtg_deck_tools.service.dto import (
    DatabaseStatsResponse,
    GenerateResponse,
    HealthResponse,
    ImportResponse,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="MTG Deck Tools API",
        version=__version__,
        description=(
            "HTTP surface for the MTG Deck Tools engine. "
            "Validation and deck rules run server-side; clients send DeckCriteria "
            "and receive .deck.json-shaped documents."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["meta"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    @app.get(
        "/api/v1/stats",
        response_model=DatabaseStatsResponse,
        tags=["database"],
    )
    def stats(
        db: Annotated[str | None, Query(description="SQLite database path")] = None,
    ) -> DatabaseStatsResponse:
        try:
            return get_database_stats(Path(db) if db else None)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(
        "/api/v1/import",
        response_model=ImportResponse,
        tags=["database"],
    )
    def import_cards(body: ImportRequest) -> ImportResponse:
        try:
            return import_oracle_cards(
                json_path=Path(body.json_path) if body.json_path else None,
                db_path=Path(body.db_path) if body.db_path else None,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(
        "/api/v1/generate",
        response_model=GenerateResponse,
        tags=["deck"],
    )
    def generate(body: GenerateRequest) -> GenerateResponse:
        try:
            return generate_deck(body, include_deck=True)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/api/v1/generate/from-deck",
        response_model=GenerateResponse,
        tags=["deck"],
    )
    def generate_from_deck(body: GenerateFromDeckRequest) -> GenerateResponse:
        try:
            return generate_deck_from_saved(body, include_deck=True)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()
