"""Resolve parsed card names to database rows (IN-DECK-RESOLVE)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from mtg_deck_tools.builder.pool import CardCandidate, _row_to_candidate
from mtg_deck_tools.deck_import.parse_text import ParsedDeckList

_CARD_COLUMNS = """
    SELECT oracle_id, name, type_line, mana_cost, cmc, color_identity,
           keywords, price_usd, price_known, edhrec_rank, oracle_text,
           is_basic_land, produced_mana, scryfall_uri, image_uri,
           released_at, power, toughness, rarity, availability_score
    FROM cards
"""


@dataclass(frozen=True)
class ResolveIssue:
    name: str
    kind: str
    line_number: int | None = None


@dataclass(frozen=True)
class PreviewLineResult:
    input_name: str
    status: str
    line_number: int | None = None
    quantity: int | None = None
    name: str | None = None
    oracle_id: str | None = None


@dataclass
class PreviewDeckResolveResult:
    commanders: list[PreviewLineResult]
    maindeck: list[PreviewLineResult]


@dataclass
class ResolvedCardLine:
    candidate: CardCandidate
    quantity: int
    line_number: int


@dataclass
class ResolvedDeckList:
    commanders: list[CardCandidate]
    maindeck: list[ResolvedCardLine]


class ResolveError(ValueError):
    """Raised when one or more card names cannot be resolved."""

    def __init__(self, issues: list[ResolveIssue]) -> None:
        self.issues = issues
        unknown = [i for i in issues if i.kind == "unknown"]
        ambiguous = [i for i in issues if i.kind == "ambiguous"]
        parts: list[str] = []
        if unknown:
            lines = ", ".join(
                f"{issue.name!r}"
                + (f" (line {issue.line_number})" if issue.line_number else "")
                for issue in unknown
            )
            parts.append(f"unknown card name(s): {lines}")
        if ambiguous:
            lines = ", ".join(
                f"{issue.name!r}"
                + (f" (line {issue.line_number})" if issue.line_number else "")
                for issue in ambiguous
            )
            parts.append(f"ambiguous card name(s): {lines}")
        super().__init__("; ".join(parts))


def _lookup_by_name(
    conn: sqlite3.Connection,
    name: str,
    *,
    commander_eligible: bool | None,
) -> list[sqlite3.Row]:
    sql = f"{_CARD_COLUMNS} WHERE name = ?"
    params: list = [name.strip()]
    if commander_eligible is True:
        sql += " AND commander_eligible = 1"
    elif commander_eligible is False:
        sql += " AND commander_legal = 1"
    return conn.execute(sql, params).fetchall()


def _resolve_name(
    conn: sqlite3.Connection,
    name: str,
    *,
    commander_eligible: bool | None,
    line_number: int | None,
) -> CardCandidate:
    rows = _lookup_by_name(conn, name, commander_eligible=commander_eligible)
    if not rows:
        raise ResolveError([ResolveIssue(name=name, kind="unknown", line_number=line_number)])
    if len(rows) > 1:
        raise ResolveError([ResolveIssue(name=name, kind="ambiguous", line_number=line_number)])
    return _row_to_candidate(rows[0])


def _preview_resolve_name(
    conn: sqlite3.Connection,
    name: str,
    *,
    commander_eligible: bool | None,
    line_number: int | None,
    quantity: int | None = None,
) -> PreviewLineResult:
    rows = _lookup_by_name(conn, name, commander_eligible=commander_eligible)
    if not rows:
        return PreviewLineResult(
            input_name=name,
            status="unknown",
            line_number=line_number,
            quantity=quantity,
        )
    if len(rows) > 1:
        return PreviewLineResult(
            input_name=name,
            status="ambiguous",
            line_number=line_number,
            quantity=quantity,
        )
    candidate = _row_to_candidate(rows[0])
    return PreviewLineResult(
        input_name=name,
        status="resolved",
        line_number=line_number,
        quantity=quantity,
        name=candidate.name,
        oracle_id=candidate.oracle_id,
    )


def preview_resolve_parsed_deck(
    conn: sqlite3.Connection,
    parsed: ParsedDeckList,
    *,
    commander_names: list[str],
) -> PreviewDeckResolveResult:
    """Resolve commander and maindeck names; return per-line status without raising."""
    if not commander_names:
        raise ValueError("Commander required: add a Commander section or pass --commander.")

    commanders = [
        _preview_resolve_name(conn, name, commander_eligible=True, line_number=None)
        for name in commander_names
    ]
    maindeck = [
        _preview_resolve_name(
            conn,
            line.name,
            commander_eligible=False,
            line_number=line.line_number,
            quantity=line.quantity,
        )
        for line in parsed.maindeck
    ]
    return PreviewDeckResolveResult(commanders=commanders, maindeck=maindeck)


def resolve_parsed_deck(
    conn: sqlite3.Connection,
    parsed: ParsedDeckList,
    *,
    commander_names: list[str],
) -> ResolvedDeckList:
    """Resolve commander and maindeck names to card rows; fail on unknown or ambiguous."""
    if not commander_names:
        raise ValueError("Commander required: add a Commander section or pass --commander.")

    issues: list[ResolveIssue] = []
    commanders: list[CardCandidate] = []
    for name in commander_names:
        try:
            commanders.append(
                _resolve_name(conn, name, commander_eligible=True, line_number=None),
            )
        except ResolveError as exc:
            issues.extend(exc.issues)

    maindeck: list[ResolvedCardLine] = []
    for line in parsed.maindeck:
        try:
            candidate = _resolve_name(
                conn,
                line.name,
                commander_eligible=False,
                line_number=line.line_number,
            )
            maindeck.append(
                ResolvedCardLine(
                    candidate=candidate,
                    quantity=line.quantity,
                    line_number=line.line_number,
                ),
            )
        except ResolveError as exc:
            issues.extend(exc.issues)

    if issues:
        raise ResolveError(issues)

    return ResolvedDeckList(commanders=commanders, maindeck=maindeck)
