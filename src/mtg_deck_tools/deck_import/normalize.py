"""Card name normalization for deck import resolution."""

from __future__ import annotations

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^\w\s]+", re.UNICODE)
_WS = re.compile(r"\s+")


def normalize_card_name(name: str) -> str:
    """Lowercase, strip accents/punctuation, collapse whitespace."""
    text = unicodedata.normalize("NFKD", name.strip().lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = _NON_ALNUM.sub(" ", text)
    return _WS.sub(" ", text).strip()
