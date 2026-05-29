"""Commander deck validation pass (CR 903, 702.124)."""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass, field
from typing import Protocol

from mtg_deck_tools.rules.commander import (
    color_identity_subset,
    is_commander_eligible,
    parse_color_identity,
)

COMMANDER_DECK_SIZE = 100
PARTNER_WITH_NAME = re.compile(r"(?i)partner with ([^(.\n]+)")


class MaindeckCard(Protocol):
    oracle_id: str
    name: str
    quantity: int
    type_line: str
    produced_mana: list[str]


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    message: str
    card_name: str | None = None


@dataclass
class ValidationResult:
    passed: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    def error(self, rule: str, message: str, *, card_name: str | None = None) -> None:
        self.errors.append(ValidationIssue(rule=rule, message=message, card_name=card_name))
        self.passed = False

    def warn(self, rule: str, message: str, *, card_name: str | None = None) -> None:
        self.warnings.append(ValidationIssue(rule=rule, message=message, card_name=card_name))


@dataclass(frozen=True)
class _CardRules:
    oracle_id: str
    name: str
    type_line: str
    color_identity: frozenset[str]
    commander_legal: bool
    commander_eligible: bool
    is_basic_land: bool
    produced_mana: frozenset[str]
    oracle_text: str
    partner_kind: str | None


@dataclass(frozen=True)
class _CommanderRules:
    oracle_id: str
    name: str
    type_line: str
    color_identity: frozenset[str]
    commander_eligible: bool
    oracle_text: str
    partner_kind: str | None


def mainboard_size_for_commanders(commander_count: int) -> int:
    """Cards in the 99/98 slot pile (excluding commander zone)."""
    if commander_count < 1:
        return 99
    return COMMANDER_DECK_SIZE - commander_count


def adjust_slot_template_for_commanders(
    slots: dict[str, int],
    commander_count: int,
) -> dict[str, int]:
    """Trim one card from the template when a second commander uses a deck slot."""
    from mtg_deck_tools.wizard.slots import load_slot_template_config, slot_template_total

    target = mainboard_size_for_commanders(commander_count)
    current = slot_template_total(slots)
    if current == target:
        return dict(slots)
    # Only trim the default 99-card wizard template when adding a second commander.
    if current != 99 or target != 98:
        return dict(slots)

    adjusted = dict(slots)
    config = load_slot_template_config()
    flex_bounds = config.bounds.get("flex")
    if adjusted.get("flex", 0) > (flex_bounds.min if flex_bounds else 0):
        adjusted["flex"] = adjusted.get("flex", 0) - 1
    else:
        adjusted["lands"] = max(0, adjusted.get("lands", 0) - 1)
    return adjusted


def partner_with_target_name(oracle_text: str) -> str | None:
    match = PARTNER_WITH_NAME.search(oracle_text or "")
    if not match:
        return None
    return match.group(1).strip()


def is_valid_partner_pair(
    first: _CommanderRules,
    second: _CommanderRules,
) -> str | None:
    """Return error message if the pair is invalid, else None."""
    if first.oracle_id == second.oracle_id:
        return "Partner commanders must be different cards."

    kinds = {first.partner_kind, second.partner_kind}
    if not kinds or kinds == {None}:
        return "Neither commander has a partner ability."

    if "partner_with" in kinds:
        for cmd, other in ((first, second), (second, first)):
            if cmd.partner_kind == "partner_with":
                target = partner_with_target_name(cmd.oracle_text)
                if target and target.lower() not in other.name.lower():
                    return (
                        f"{cmd.name} partners with {target}, not {other.name}."
                    )
        return None

    compatible = kinds <= {
        "partner",
        "partner_variant",
        "choose_a_background",
        "doctors_companion",
    }
    if not compatible:
        return f"Incompatible partner types: {first.partner_kind}, {second.partner_kind}."

    if "choose_a_background" in kinds and kinds != {"choose_a_background"}:
        return "Background pairs require a legendary creature with Choose a Background."

    return None


def _fetch_cards(conn: sqlite3.Connection, oracle_ids: list[str]) -> dict[str, _CardRules]:
    if not oracle_ids:
        return {}
    placeholders = ",".join("?" * len(oracle_ids))
    rows = conn.execute(
        f"""
        SELECT oracle_id, name, type_line, color_identity, commander_legal,
               commander_eligible, is_basic_land, produced_mana, oracle_text, partner_kind
        FROM cards WHERE oracle_id IN ({placeholders})
        """,
        oracle_ids,
    ).fetchall()
    result: dict[str, _CardRules] = {}
    for row in rows:
        result[row["oracle_id"]] = _CardRules(
            oracle_id=row["oracle_id"],
            name=row["name"],
            type_line=row["type_line"] or "",
            color_identity=parse_color_identity(json.loads(row["color_identity"] or "[]")),
            commander_legal=bool(row["commander_legal"]),
            commander_eligible=bool(row["commander_eligible"]),
            is_basic_land=bool(row["is_basic_land"]),
            produced_mana=parse_color_identity(json.loads(row["produced_mana"] or "[]")),
            oracle_text=row["oracle_text"] or "",
            partner_kind=row["partner_kind"],
        )
    return result


def _load_commanders(
    conn: sqlite3.Connection,
    commanders: list[dict],
) -> list[_CommanderRules]:
    ids = [c["oracle_id"] for c in commanders]
    by_id = _fetch_cards(conn, ids)
    loaded: list[_CommanderRules] = []
    for cmd in commanders:
        row = by_id.get(cmd["oracle_id"])
        if not row:
            continue
        loaded.append(
            _CommanderRules(
                oracle_id=row.oracle_id,
                name=row.name,
                type_line=row.type_line,
                color_identity=row.color_identity,
                commander_eligible=row.commander_eligible,
                oracle_text=row.oracle_text,
                partner_kind=row.partner_kind,
            )
        )
    return loaded


def _is_basic_land(card: MaindeckCard, rules: _CardRules | None) -> bool:
    if rules and rules.is_basic_land:
        return True
    return card.type_line.startswith("Basic Land")


def validate_commander_deck(
    conn: sqlite3.Connection,
    *,
    commanders: list[dict],
    maindeck: list[MaindeckCard],
    identity: list[str],
    budget_usd: float | None = None,
    budget_spent: float = 0.0,
    unpriced_count: int = 0,
) -> ValidationResult:
    """Run Commander format checks on a generated deck."""
    result = ValidationResult(passed=True)
    commander_identity = parse_color_identity(identity)
    commander_rows = _load_commanders(conn, commanders)
    commander_ids = {c.oracle_id for c in commander_rows}

    if not commander_rows:
        result.error("903.3", "No commander selected.")
        return result

    if len(commander_rows) > 2:
        result.error("702.124", "At most two commanders allowed.")
        return result

    expected_mainboard = mainboard_size_for_commanders(len(commander_rows))
    maindeck_qty = sum(c.quantity for c in maindeck)

    # 903.5a — deck size
    total_cards = maindeck_qty + len(commander_rows)
    if total_cards != COMMANDER_DECK_SIZE:
        result.error(
            "903.5a",
            f"Deck has {total_cards} cards ({maindeck_qty} maindeck + "
            f"{len(commander_rows)} commander(s)); must be {COMMANDER_DECK_SIZE}.",
        )
    elif maindeck_qty != expected_mainboard:
        result.error(
            "903.5a",
            f"Maindeck has {maindeck_qty} cards; expected {expected_mainboard} "
            f"with {len(commander_rows)} commander(s).",
        )

    # 903.3 — commander eligibility
    for cmd in commander_rows:
        if not cmd.commander_eligible and not is_commander_eligible(
            cmd.type_line, cmd.oracle_text
        ):
            result.error("903.3", f"{cmd.name} cannot be your commander.", card_name=cmd.name)

    # 702.124 — partner pairs
    if len(commander_rows) == 2:
        partner_err = is_valid_partner_pair(commander_rows[0], commander_rows[1])
        if partner_err:
            result.error("702.124", partner_err)
    elif len(commander_rows) == 1 and commander_rows[0].partner_kind:
        result.warn(
            "702.124",
            f"{commander_rows[0].name} has a partner ability but no second commander.",
            card_name=commander_rows[0].name,
        )

    oracle_ids = [c.oracle_id for c in maindeck]
    rules_by_id = _fetch_cards(conn, oracle_ids)

    # Commander must not appear in maindeck
    for card in maindeck:
        if card.oracle_id in commander_ids:
            result.error(
                "903.3",
                f"{card.name} is the commander and cannot be in the maindeck.",
                card_name=card.name,
            )

    # 903.5b — singleton
    name_counts: dict[str, int] = {}
    for card in maindeck:
        row = rules_by_id.get(card.oracle_id)
        if _is_basic_land(card, row):
            continue
        name_counts[card.name] = name_counts.get(card.name, 0) + card.quantity

    for name, count in name_counts.items():
        if count > 1:
            result.error(
                "903.5b",
                f"Singleton violated: {name} appears {count} times.",
                card_name=name,
            )

    # 903.5c / commander_legal — card legality and color identity
    for card in maindeck:
        row = rules_by_id.get(card.oracle_id)
        if not row:
            result.error("903.5c", f"{card.name} not found in card database.", card_name=card.name)
            continue
        if not row.commander_legal:
            result.error(
                "903.5c",
                f"{card.name} is not Commander-legal.",
                card_name=card.name,
            )
        if not color_identity_subset(row.color_identity, commander_identity):
            extra = sorted(row.color_identity - commander_identity)
            result.error(
                "903.5c",
                f"{card.name} color identity {extra} exceeds commander identity.",
                card_name=card.name,
            )

    # 903.5d — land mana production
    for card in maindeck:
        row = rules_by_id.get(card.oracle_id)
        if not row or row.is_basic_land or "Land" not in card.type_line:
            continue
        produced = row.produced_mana or parse_color_identity(card.produced_mana)
        illegal = sorted(produced - commander_identity)
        if illegal:
            result.error(
                "903.5d",
                f"{card.name} produces {illegal} outside commander color identity.",
                card_name=card.name,
            )

    # Budget (planning policy — warning only)
    if budget_usd is not None and budget_spent > budget_usd:
        result.warn(
            "budget",
            f"Estimated maindeck ${budget_spent:.2f} exceeds cap ${budget_usd:.2f}.",
        )
    if budget_usd is not None and unpriced_count:
        result.warn(
            "budget",
            f"{unpriced_count} card(s) had no USD price and may push the deck over budget.",
        )

    return result


def validation_messages(result: ValidationResult) -> list[str]:
    """Flatten errors and warnings for deck output notes."""
    lines: list[str] = []
    for issue in result.errors:
        prefix = f"[{issue.rule}]"
        name = f" ({issue.card_name})" if issue.card_name else ""
        lines.append(f"{prefix}{name} {issue.message}")
    for issue in result.warnings:
        prefix = f"[{issue.rule}]"
        name = f" ({issue.card_name})" if issue.card_name else ""
        lines.append(f"{prefix}{name} {issue.message}")
    return lines
