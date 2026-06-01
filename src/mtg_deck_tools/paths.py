"""Project path resolution."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RESOURCES_DIR = PROJECT_ROOT / "resources"
SCRYFALL_DIR = RESOURCES_DIR / "scryfall"
DEFAULT_DB_PATH = DATA_DIR / "cards.db"
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
