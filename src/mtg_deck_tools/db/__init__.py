"""SQLite persistence."""

from mtg_deck_tools.db.connection import connect
from mtg_deck_tools.db.schema import SCHEMA_VERSION, apply_schema

__all__ = ["connect", "apply_schema", "SCHEMA_VERSION"]
