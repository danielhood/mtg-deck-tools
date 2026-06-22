"""Project path resolution."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent


def _resolve_project_root() -> Path:
    """Resolve repo root: ``MTG_PROJECT_ROOT`` env, else editable/source layout."""
    env = os.environ.get("MTG_PROJECT_ROOT")
    if env:
        return Path(env)
    return PACKAGE_ROOT.parent.parent


PROJECT_ROOT = _resolve_project_root()
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RESOURCES_DIR = PROJECT_ROOT / "resources"
SCRYFALL_DIR = RESOURCES_DIR / "scryfall"
DEFAULT_DB_PATH = DATA_DIR / "cards.db"
DEFAULT_DECKS_PATH = DATA_DIR / "decks.db"
WEB_UI_DIST_DIR = PROJECT_ROOT / "packages" / "web" / "dist"
TAXONOMY_PATH = CONFIG_DIR / "mechanic-taxonomy.yaml"
EFFECT_PATTERNS_PATH = CONFIG_DIR / "effect-patterns.yaml"
DEPENDENCY_PROFILES_PATH = CONFIG_DIR / "dependency-profiles.yaml"
DOGFOOD_MATRIX_PATH = CONFIG_DIR / "dogfood-matrix.yaml"
SLOT_TEMPLATES_PATH = CONFIG_DIR / "slot-templates.yaml"
DEPENDENCY_RESOURCES_DIR = RESOURCES_DIR / "dependency"
OUTPUT_DIR = PROJECT_ROOT / "output"

NON_DECKABLE_LAYOUTS = frozenset(
    {
        "token",
        "double_faced_token",
        "emblem",
        "art_series",
        "planar",
        "scheme",
        "vanguard",
    }
)


def resolve_decks_path(decks_path: Path | None = None) -> Path:
    """Resolve saved-deck library SQLite path: arg, then ``MTG_DECKS_PATH``, then default."""
    if decks_path is not None:
        return decks_path
    env = os.environ.get("MTG_DECKS_PATH")
    if env:
        return Path(env)
    return DEFAULT_DECKS_PATH


def resolve_db_path(db_path: Path | None = None) -> Path:
    """Resolve SQLite path: explicit arg, then ``MTG_DB_PATH`` env, then default."""
    if db_path is not None:
        return db_path
    env = os.environ.get("MTG_DB_PATH")
    if env:
        return Path(env)
    return DEFAULT_DB_PATH


def resolve_static_ui_dir(static_dir: Path | None = None) -> Path | None:
    """Resolve SPA static root: explicit arg, then ``MTG_SERVE_STATIC_DIR`` env."""
    if static_dir is not None:
        return static_dir
    env = os.environ.get("MTG_SERVE_STATIC_DIR")
    if env:
        return Path(env)
    return None


def find_oracle_cards_json(directory: Path | None = None) -> Path:
    """Locate the newest oracle-cards bulk JSON in resources/scryfall."""
    search_dir = directory or SCRYFALL_DIR
    matches = sorted(search_dir.glob("oracle-cards-*.json"), reverse=True)
    if not matches:
        raise FileNotFoundError(
            f"No oracle-cards-*.json found in {search_dir}. "
            "Download Oracle Cards bulk data — see README.md."
        )
    return matches[0]
