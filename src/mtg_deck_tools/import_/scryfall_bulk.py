"""Download Scryfall oracle-cards bulk data when no local snapshot exists."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from mtg_deck_tools import __version__
from mtg_deck_tools.paths import SCRYFALL_DIR, find_oracle_cards_json

BULK_METADATA_URL = "https://api.scryfall.com/bulk-data/oracle-cards"
_DOWNLOAD_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True)
class OracleBulkMetadata:
    download_uri: str
    updated_at: str
    size: int
    name: str


def auto_download_enabled() -> bool:
    """Return False when ``MTG_AUTO_DOWNLOAD`` is ``0``, ``false``, ``no``, or ``off``."""
    value = os.environ.get("MTG_AUTO_DOWNLOAD", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _user_agent() -> str:
    return f"mtg-deck-tools/{__version__}"


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": _user_agent(),
            "Accept": "application/json",
        },
    )


def fetch_oracle_bulk_metadata() -> OracleBulkMetadata:
    """Fetch bulk metadata from Scryfall (``GET /bulk-data/oracle-cards``)."""
    try:
        with urllib.request.urlopen(_request(BULK_METADATA_URL), timeout=60) as response:
            payload = json.load(response)
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Failed to fetch Scryfall bulk metadata from {BULK_METADATA_URL}: {exc}"
        ) from exc

    try:
        return OracleBulkMetadata(
            download_uri=str(payload["download_uri"]),
            updated_at=str(payload["updated_at"]),
            size=int(payload["size"]),
            name=str(payload.get("name", "Oracle Cards")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Unexpected Scryfall bulk metadata response") from exc


def oracle_bulk_filename(updated_at: str) -> str:
    """Map Scryfall ``updated_at`` to ``oracle-cards-YYYYMMDDhhmmss.json``."""
    normalized = updated_at.replace("Z", "+00:00")
    stamp = datetime.fromisoformat(normalized).strftime("%Y%m%d%H%M%S")
    return f"oracle-cards-{stamp}.json"


def download_oracle_cards_json(
    *,
    directory: Path | None = None,
    progress: Callable[[str], None] | None = None,
) -> Path:
    """Download the latest oracle-cards bulk JSON into ``directory``."""
    log = progress or (lambda _msg: None)
    dest_dir = directory or SCRYFALL_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    meta = fetch_oracle_bulk_metadata()
    dest = dest_dir / oracle_bulk_filename(meta.updated_at)
    if dest.exists():
        log(f"Using existing bulk file {dest.name}")
        return dest

    log(f"Downloading {meta.name} ({meta.size:,} bytes) from Scryfall...")
    temp_path = dest.with_suffix(dest.suffix + ".part")
    downloaded = 0
    last_logged_mb = 0

    try:
        with urllib.request.urlopen(_request(meta.download_uri), timeout=300) as response:
            with temp_path.open("wb") as out:
                while True:
                    chunk = response.read(_DOWNLOAD_CHUNK_BYTES)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    logged_mb = downloaded // (10 * _DOWNLOAD_CHUNK_BYTES)
                    if logged_mb > last_logged_mb:
                        last_logged_mb = logged_mb
                        log(f"  … {downloaded:,} / {meta.size:,} bytes")
        temp_path.replace(dest)
    except urllib.error.URLError as exc:
        temp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Failed to download Scryfall oracle bulk data from {meta.download_uri}: {exc}"
        ) from exc

    log(f"Saved {dest.name}")
    return dest


def ensure_oracle_cards_json(
    *,
    directory: Path | None = None,
    auto_download: bool | None = None,
    progress: Callable[[str], None] | None = None,
) -> Path:
    """Return the newest local oracle bulk file, downloading from Scryfall when missing."""
    search_dir = directory or SCRYFALL_DIR
    try:
        return find_oracle_cards_json(search_dir)
    except FileNotFoundError:
        enabled = auto_download_enabled() if auto_download is None else auto_download
        if not enabled:
            raise
        return download_oracle_cards_json(directory=search_dir, progress=progress)
