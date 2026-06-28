"""Resolve parsed card names to database rows (IN-DECK-RESOLVE)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from mtg_deck_tools.builder.pool import CardCandidate, _row_to_candidate
from mtg_deck_tools.deck_import.normalize import normalize_card_name
from mtg_deck_tools.deck_import.parse_text import ParsedDeckList

_CARD_COLUMNS = """
    SELECT oracle_id, name, type_line, mana_cost, cmc, color_identity,
           keywords, price_usd, price_known, edhrec_rank, oracle_text,
           is_basic_land, produced_mana, scryfall_uri, image_uri,
           released_at, power, toughness, rarity, availability_score
    FROM cards
"""

FUZZY_AUTO_THRESHOLD = 0.92
FUZZY_AMBIGUOUS_THRESHOLD = 0.85
FUZZY_SUGGESTION_THRESHOLD = 0.65
MAX_CANDIDATES = 8
LIKE_CANDIDATE_LIMIT = 80

ResolutionMap = dict[tuple[str, int], str]


@dataclass(frozen=True)
class ResolveIssue:
    name: str
    kind: str
    line_number: int | None = None


@dataclass(frozen=True)
class ResolveCandidate:
    oracle_id: str
    name: str
    type_line: str = ""
    score: float | None = None


@dataclass(frozen=True)
class PreviewLineResult:
    input_name: str
    status: str
    line_number: int | None = None
    quantity: int | None = None
    name: str | None = None
    oracle_id: str | None = None
    match_method: str | None = None
    candidates: list[ResolveCandidate] = field(default_factory=list)


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


def build_resolution_map(
    resolutions: list[tuple[str, int, str]] | None,
) -> ResolutionMap:
    """Build a lookup from (section, index) to oracle_id."""
    mapping: ResolutionMap = {}
    for section, index, oracle_id in resolutions or []:
        mapping[(section, index)] = oracle_id
    return mapping


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _eligibility_filter(commander_eligible: bool | None) -> tuple[str, list]:
    if commander_eligible is True:
        return " AND commander_eligible = 1", []
    if commander_eligible is False:
        return " AND commander_legal = 1", []
    return "", []


def _lookup_by_name(
    conn: sqlite3.Connection,
    name: str,
    *,
    commander_eligible: bool | None,
) -> list[sqlite3.Row]:
    sql = f"{_CARD_COLUMNS} WHERE name = ?"
    params: list = [name.strip()]
    extra, extra_params = _eligibility_filter(commander_eligible)
    sql += extra
    params.extend(extra_params)
    return conn.execute(sql, params).fetchall()


def _lookup_by_name_case_insensitive(
    conn: sqlite3.Connection,
    name: str,
    *,
    commander_eligible: bool | None,
) -> list[sqlite3.Row]:
    sql = f"{_CARD_COLUMNS} WHERE lower(trim(name)) = lower(trim(?))"
    params: list = [name.strip()]
    extra, extra_params = _eligibility_filter(commander_eligible)
    sql += extra
    params.extend(extra_params)
    return conn.execute(sql, params).fetchall()


def _lookup_like_candidates(
    conn: sqlite3.Connection,
    name: str,
    *,
    commander_eligible: bool | None,
    limit: int = LIKE_CANDIDATE_LIMIT,
) -> list[sqlite3.Row]:
    normalized = normalize_card_name(name)
    words = [word for word in normalized.split() if len(word) >= 2]
    if not words:
        return []

    def _query(word: str) -> list[sqlite3.Row]:
        sql = f"{_CARD_COLUMNS} WHERE lower(name) LIKE ? ESCAPE '\\'"
        params: list = [f"%{_escape_like(word.lower())}%"]
        extra, extra_params = _eligibility_filter(commander_eligible)
        sql += extra
        params.extend(extra_params)
        sql += " LIMIT ?"
        params.append(limit)
        return conn.execute(sql, params).fetchall()

    rows = _query(max(words, key=len))
    if len(rows) < 5 and len(words) > 1:
        seen = {row["oracle_id"] for row in rows}
        for word in sorted(words, key=len, reverse=True):
            for row in _query(word):
                if row["oracle_id"] not in seen:
                    rows.append(row)
                    seen.add(row["oracle_id"])
            if len(rows) >= limit:
                break
    return rows[:limit]


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def _rows_to_scored_candidates(
    rows: list[sqlite3.Row],
    query_name: str,
) -> list[ResolveCandidate]:
    normalized_query = normalize_card_name(query_name)
    scored: list[ResolveCandidate] = []
    seen: set[str] = set()
    for row in rows:
        oracle_id = row["oracle_id"]
        if oracle_id in seen:
            continue
        seen.add(oracle_id)
        card_name = row["name"]
        score = _similarity(normalized_query, normalize_card_name(card_name))
        scored.append(
            ResolveCandidate(
                oracle_id=oracle_id,
                name=card_name,
                type_line=row["type_line"] or "",
                score=round(score, 4),
            ),
        )
    scored.sort(key=lambda candidate: (-(candidate.score or 0.0), candidate.name))
    return scored


def _lookup_by_oracle_id(
    conn: sqlite3.Connection,
    oracle_id: str,
    *,
    commander_eligible: bool | None,
) -> sqlite3.Row | None:
    sql = f"{_CARD_COLUMNS} WHERE oracle_id = ?"
    params: list = [oracle_id]
    extra, extra_params = _eligibility_filter(commander_eligible)
    sql += extra
    params.extend(extra_params)
    return conn.execute(sql, params).fetchone()


def _resolved_preview_line(
    *,
    input_name: str,
    candidate: CardCandidate,
    line_number: int | None,
    quantity: int | None,
    match_method: str,
) -> PreviewLineResult:
    return PreviewLineResult(
        input_name=input_name,
        status="resolved",
        line_number=line_number,
        quantity=quantity,
        name=candidate.name,
        oracle_id=candidate.oracle_id,
        match_method=match_method,
    )


def _match_preview_line(
    conn: sqlite3.Connection,
    name: str,
    *,
    commander_eligible: bool | None,
    line_number: int | None,
    quantity: int | None,
    resolution_oracle_id: str | None,
) -> PreviewLineResult:
    if resolution_oracle_id:
        row = _lookup_by_oracle_id(
            conn,
            resolution_oracle_id,
            commander_eligible=commander_eligible,
        )
        if row is None:
            return PreviewLineResult(
                input_name=name,
                status="unknown",
                line_number=line_number,
                quantity=quantity,
            )
        candidate = _row_to_candidate(row)
        return _resolved_preview_line(
            input_name=name,
            candidate=candidate,
            line_number=line_number,
            quantity=quantity,
            match_method="manual",
        )

    exact_rows = _lookup_by_name(conn, name, commander_eligible=commander_eligible)
    if len(exact_rows) == 1:
        candidate = _row_to_candidate(exact_rows[0])
        return _resolved_preview_line(
            input_name=name,
            candidate=candidate,
            line_number=line_number,
            quantity=quantity,
            match_method="exact",
        )
    if len(exact_rows) > 1:
        candidates = _rows_to_scored_candidates(exact_rows, name)[:MAX_CANDIDATES]
        return PreviewLineResult(
            input_name=name,
            status="ambiguous",
            line_number=line_number,
            quantity=quantity,
            candidates=candidates,
        )

    case_rows = _lookup_by_name_case_insensitive(
        conn,
        name,
        commander_eligible=commander_eligible,
    )
    if len(case_rows) == 1:
        candidate = _row_to_candidate(case_rows[0])
        return _resolved_preview_line(
            input_name=name,
            candidate=candidate,
            line_number=line_number,
            quantity=quantity,
            match_method="case_insensitive",
        )
    if len(case_rows) > 1:
        candidates = _rows_to_scored_candidates(case_rows, name)[:MAX_CANDIDATES]
        return PreviewLineResult(
            input_name=name,
            status="ambiguous",
            line_number=line_number,
            quantity=quantity,
            candidates=candidates,
        )

    like_rows = _lookup_like_candidates(conn, name, commander_eligible=commander_eligible)
    candidates = [
        candidate
        for candidate in _rows_to_scored_candidates(like_rows, name)
        if (candidate.score or 0.0) >= FUZZY_SUGGESTION_THRESHOLD
    ][:MAX_CANDIDATES]

    strong = [candidate for candidate in candidates if (candidate.score or 0.0) >= FUZZY_AUTO_THRESHOLD]
    if len(strong) == 1:
        row = next(row for row in like_rows if row["oracle_id"] == strong[0].oracle_id)
        candidate = _row_to_candidate(row)
        return _resolved_preview_line(
            input_name=name,
            candidate=candidate,
            line_number=line_number,
            quantity=quantity,
            match_method="fuzzy",
        )

    ambiguous = [
        candidate for candidate in candidates if (candidate.score or 0.0) >= FUZZY_AMBIGUOUS_THRESHOLD
    ]
    if len(ambiguous) > 1:
        return PreviewLineResult(
            input_name=name,
            status="ambiguous",
            line_number=line_number,
            quantity=quantity,
            candidates=ambiguous[:MAX_CANDIDATES],
        )
    if len(ambiguous) == 1:
        row = next(row for row in like_rows if row["oracle_id"] == ambiguous[0].oracle_id)
        candidate = _row_to_candidate(row)
        return _resolved_preview_line(
            input_name=name,
            candidate=candidate,
            line_number=line_number,
            quantity=quantity,
            match_method="fuzzy",
        )

    return PreviewLineResult(
        input_name=name,
        status="unknown",
        line_number=line_number,
        quantity=quantity,
        candidates=candidates,
    )


def _resolve_name(
    conn: sqlite3.Connection,
    name: str,
    *,
    commander_eligible: bool | None,
    line_number: int | None,
    resolution_oracle_id: str | None = None,
) -> CardCandidate:
    preview = _match_preview_line(
        conn,
        name,
        commander_eligible=commander_eligible,
        line_number=line_number,
        quantity=None,
        resolution_oracle_id=resolution_oracle_id,
    )
    if preview.status == "resolved" and preview.oracle_id:
        row = _lookup_by_oracle_id(
            conn,
            preview.oracle_id,
            commander_eligible=commander_eligible,
        )
        if row is not None:
            return _row_to_candidate(row)
    if preview.status == "ambiguous":
        raise ResolveError([ResolveIssue(name=name, kind="ambiguous", line_number=line_number)])
    raise ResolveError([ResolveIssue(name=name, kind="unknown", line_number=line_number)])


def preview_resolve_parsed_deck(
    conn: sqlite3.Connection,
    parsed: ParsedDeckList,
    *,
    commander_names: list[str],
    resolutions: ResolutionMap | None = None,
) -> PreviewDeckResolveResult:
    """Resolve commander and maindeck names; return per-line status without raising."""
    if not commander_names:
        raise ValueError("Commander required: add a Commander section or pass --commander.")

    resolution_map = resolutions or {}
    commanders = [
        _match_preview_line(
            conn,
            name,
            commander_eligible=True,
            line_number=None,
            quantity=None,
            resolution_oracle_id=resolution_map.get(("commander", index)),
        )
        for index, name in enumerate(commander_names)
    ]
    maindeck = [
        _match_preview_line(
            conn,
            line.name,
            commander_eligible=False,
            line_number=line.line_number,
            quantity=line.quantity,
            resolution_oracle_id=resolution_map.get(("maindeck", line.line_number)),
        )
        for line in parsed.maindeck
    ]
    return PreviewDeckResolveResult(commanders=commanders, maindeck=maindeck)


def resolve_parsed_deck(
    conn: sqlite3.Connection,
    parsed: ParsedDeckList,
    *,
    commander_names: list[str],
    resolutions: ResolutionMap | None = None,
) -> ResolvedDeckList:
    """Resolve commander and maindeck names to card rows; fail on unknown or ambiguous."""
    if not commander_names:
        raise ValueError("Commander required: add a Commander section or pass --commander.")

    resolution_map = resolutions or {}
    issues: list[ResolveIssue] = []
    commanders: list[CardCandidate] = []
    for index, name in enumerate(commander_names):
        try:
            commanders.append(
                _resolve_name(
                    conn,
                    name,
                    commander_eligible=True,
                    line_number=None,
                    resolution_oracle_id=resolution_map.get(("commander", index)),
                ),
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
                resolution_oracle_id=resolution_map.get(("maindeck", line.line_number)),
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
