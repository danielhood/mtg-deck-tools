"""Shared facades for CLI and HTTP API."""

from mtg_deck_tools.service.dto import (
    DatabaseStatsResponse,
    GenerateFromDeckRequest,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    ImportRequest,
    ImportResponse,
)
from mtg_deck_tools.service.generate import (
    GenerateResult,
    generate_deck,
    generate_deck_cli,
    generate_deck_from_saved,
)
from mtg_deck_tools.service.import_ import import_oracle_cards
from mtg_deck_tools.service.stats import get_database_stats
from mtg_deck_tools.service.wizard import run_interactive_wizard
from mtg_deck_tools.service.wizard_catalog import (
    get_slot_template_defaults,
    get_synergy_context,
    get_wizard_mechanics,
    get_wizard_meta,
    get_wizard_rarities,
    get_wizard_themes,
    run_wizard_preflight,
    search_wizard_commanders,
)

__all__ = [
    "DatabaseStatsResponse",
    "GenerateFromDeckRequest",
    "GenerateRequest",
    "GenerateResponse",
    "GenerateResult",
    "HealthResponse",
    "ImportRequest",
    "ImportResponse",
    "generate_deck",
    "generate_deck_cli",
    "generate_deck_from_saved",
    "get_database_stats",
    "import_oracle_cards",
    "run_interactive_wizard",
    "get_slot_template_defaults",
    "get_synergy_context",
    "get_wizard_mechanics",
    "get_wizard_meta",
    "get_wizard_rarities",
    "get_wizard_themes",
    "run_wizard_preflight",
    "search_wizard_commanders",
]
