"""Post-build card dependency validation (D2 — warn-only by default)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.paths import DEPENDENCY_PROFILES_PATH
from mtg_deck_tools.rules.dependency_scope import (
    DependencyScope,
    build_dependency_scope,
)

DependencyStatus = Literal["pass", "warn", "fail"]


@dataclass(frozen=True)
class CardEffectRow:
    oracle_id: str
    effect_kind: str
    payload: dict[str, Any]
    confidence: float
    source: str
    face_index: int = 0


@dataclass
class DependencyIssue:
    rule_id: str
    status: DependencyStatus
    message: str
    card_name: str | None = None
    card_oracle_id: str | None = None
    profile_id: str | None = None
    detail: dict[str, Any] | None = None


@dataclass
class ProfileSummary:
    profile_id: str
    counts: dict[str, int] = field(default_factory=dict)
    status: DependencyStatus = "pass"
    messages: list[str] = field(default_factory=list)


@dataclass
class DependencyReport:
    issues: list[DependencyIssue] = field(default_factory=list)
    profiles: list[ProfileSummary] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(i.status in ("warn", "fail") for i in self.issues)

    @property
    def warnings(self) -> list[DependencyIssue]:
        return [i for i in self.issues if i.status == "warn"]

    @property
    def failures(self) -> list[DependencyIssue]:
        return [i for i in self.issues if i.status == "fail"]


def load_profile_defaults(path: Path | None = None) -> dict[str, dict[str, Any]]:
    with (path or DEPENDENCY_PROFILES_PATH).open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    profiles = data.get("profiles") or {}
    if isinstance(profiles, dict):
        return {key: dict(entry.get("defaults") or {}) for key, entry in profiles.items()}
    return {
        entry["id"]: dict(entry.get("defaults") or {})
        for entry in profiles
        if isinstance(entry, dict)
    }


def fetch_card_effects(
    conn: sqlite3.Connection,
    oracle_ids: list[str],
) -> dict[str, list[CardEffectRow]]:
    if not oracle_ids:
        return {}
    placeholders = ",".join("?" * len(oracle_ids))
    rows = conn.execute(
        f"""
        SELECT oracle_id, face_index, effect_kind, payload, confidence, source
        FROM card_effects
        WHERE oracle_id IN ({placeholders})
        """,
        oracle_ids,
    ).fetchall()
    grouped: dict[str, list[CardEffectRow]] = {}
    for row in rows:
        grouped.setdefault(row["oracle_id"], []).append(
            CardEffectRow(
                oracle_id=row["oracle_id"],
                effect_kind=row["effect_kind"],
                payload=json.loads(row["payload"] or "{}"),
                confidence=float(row["confidence"]),
                source=row["source"],
                face_index=int(row["face_index"] or 0),
            )
        )
    return grouped


def payload_matches_card(
    type_line: str,
    cmc: float,
    payload: dict[str, Any],
) -> bool:
    """Whether a card's type line / CMC satisfies a search_library payload (D2/D3)."""
    tl = type_line or ""
    for supertype in payload.get("supertypes") or []:
        if supertype.lower() == "basic" and "Basic" in tl and "Land" in tl:
            continue
        if supertype not in tl:
            return False
    for card_type in payload.get("types") or []:
        if card_type.lower() == "land" and "Land" not in tl:
            return False
        if card_type.lower() == "creature" and "Creature" not in tl:
            return False
        if card_type.lower() == "artifact" and "Artifact" not in tl:
            return False
        if card_type.lower() == "enchantment" and "Enchantment" not in tl:
            return False
    for subtype in payload.get("subtypes") or []:
        if subtype not in tl:
            return False
    max_cmc = payload.get("max_cmc")
    if max_cmc is not None and "Creature" in tl:
        if cmc > float(max_cmc):
            return False
    return True


def _type_line_matches(card: DeckCard, payload: dict[str, Any]) -> bool:
    return payload_matches_card(card.type_line or "", card.cmc, payload)


def _search_targets(
    pool: list[DeckCard],
    payload: dict[str, Any],
) -> list[DeckCard]:
    if payload.get("any_card"):
        return list(pool)
    return [c for c in pool if _type_line_matches(c, payload)]


def _count_subtype(pool: list[DeckCard], subtype: str) -> int:
    return sum(1 for c in pool if subtype in (c.type_line or ""))


def _count_type(pool: list[DeckCard], card_type: str) -> int:
    needle = card_type.capitalize()
    return sum(1 for c in pool if needle in (c.type_line or ""))


def _issue_status(*, strict: bool) -> DependencyStatus:
    return "fail" if strict else "warn"


def _payload_searches_auras(payload: dict[str, Any]) -> bool:
    subtypes = [s.lower() for s in (payload.get("subtypes") or [])]
    if "aura" in subtypes:
        return True
    types = [t.lower() for t in (payload.get("types") or [])]
    return "enchantment" in types and "aura" in subtypes


def _deck_has_aura_payoff(effects_map: dict[str, list[CardEffectRow]]) -> bool:
    for effects in effects_map.values():
        for effect in effects:
            if effect.effect_kind == "whenever_cast_aura":
                return True
    return False


def _deck_has_aura_tutor(
    maindeck: list[DeckCard],
    effects_map: dict[str, list[CardEffectRow]],
) -> bool:
    for card in maindeck:
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind == "search_library" and _payload_searches_auras(
                effect.payload
            ):
                return True
    return False


def _should_check_aura_support_min(
    *,
    scope: DependencyScope,
    aura_spells: int,
    effects_map: dict[str, list[CardEffectRow]],
    maindeck: list[DeckCard],
) -> bool:
    if scope.aura_support_min:
        return True
    if _deck_has_aura_payoff(effects_map):
        return True
    if _deck_has_aura_tutor(maindeck, effects_map):
        return True
    return False


def _should_warn_energy_imbalance(
    *,
    scope: DependencyScope,
    producer_count: int,
    consumer_count: int,
) -> bool:
    if producer_count == 0 and consumer_count == 0:
        return False
    if producer_count > 0 and consumer_count > 0:
        return False
    if scope.energy_user_intent:
        return True
    dominant = max(producer_count, consumer_count)
    return dominant >= 2


def _should_warn_sacrifice_imbalance(
    *,
    scope: DependencyScope,
    outlet_count: int,
    payoff_count: int,
) -> bool:
    if outlet_count == 0 and payoff_count == 0:
        return False
    if outlet_count > 0 and payoff_count > 0:
        return False
    if scope.sacrifice_user_intent:
        return True
    dominant = max(outlet_count, payoff_count)
    return dominant >= 2


def validate_dependencies(
    conn: sqlite3.Connection,
    *,
    maindeck: list[DeckCard],
    commanders: list[dict[str, Any]],
    profiles: dict[str, dict[str, Any]] | None = None,
    criteria: DeckCriteria | None = None,
    scope: DependencyScope | None = None,
    strict: bool = False,
) -> DependencyReport:
    """
    Evaluate v1 dependency rules. Default severity is warn; with strict=True, issues are fail.
    """
    profile_cfg = profiles or load_profile_defaults()
    dep_scope = scope if scope is not None else build_dependency_scope(criteria)
    report = DependencyReport()
    severity = _issue_status(strict=strict)

    commander_cards = [
        DeckCard(
            oracle_id=c["oracle_id"],
            name=c["name"],
            slot="commander",
            quantity=1,
            cmc=float(c.get("cmc") or 0),
            mana_cost=c.get("mana_cost") or "",
            type_line=c.get("type_line") or "",
            price_usd=None,
            price_known=True,
            scryfall_uri=c.get("scryfall_uri"),
            image_uri=c.get("image_uri"),
        )
        for c in commanders
    ]
    search_pool = list(maindeck) + commander_cards
    all_oracle_ids = list({c.oracle_id for c in search_pool})
    effects_map = fetch_card_effects(conn, all_oracle_ids)

    energy_producers: list[str] = []
    energy_consumers: list[str] = []
    sacrifice_outlets: list[str] = []
    sacrifice_payoffs: list[str] = []
    sacrifice_fodder: list[str] = []
    aura_spells = _count_type(maindeck, "enchantment")  # refined below for Aura subtype

    for card in maindeck:
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind == "energy_produce":
                energy_producers.append(card.name)
            elif effect.effect_kind == "energy_consume":
                energy_consumers.append(card.name)
            elif effect.effect_kind == "sacrifice_outlet":
                sacrifice_outlets.append(card.name)
            elif effect.effect_kind == "sacrifice_payoff":
                sacrifice_payoffs.append(card.name)
            elif effect.effect_kind == "sacrifice_fodder":
                sacrifice_fodder.append(card.name)
            elif effect.effect_kind == "type_line_aura":
                pass

    aura_spells = sum(1 for c in maindeck if "Aura" in (c.type_line or ""))

    for card in maindeck:
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind != "search_library":
                continue
            if effect.confidence < 0.6 and effect.payload.get("any_card"):
                continue
            targets = _search_targets(search_pool, effect.payload)
            if targets:
                continue
            detail = {"payload": effect.payload, "tutor": card.name}
            report.issues.append(
                DependencyIssue(
                    rule_id="TUTOR_TARGET_EXISTS",
                    status=severity,
                    message=(
                        f"{card.name} searches your library but no card in the deck "
                        f"matches { _describe_payload(effect.payload) }."
                    ),
                    card_name=card.name,
                    card_oracle_id=card.oracle_id,
                    detail=detail,
                )
            )

    energy_imbalanced = (energy_producers and not energy_consumers) or (
        energy_consumers and not energy_producers
    )
    energy_warn = energy_imbalanced and _should_warn_energy_imbalance(
        scope=dep_scope,
        producer_count=len(energy_producers),
        consumer_count=len(energy_consumers),
    )
    if energy_warn and energy_producers and not energy_consumers:
        report.issues.append(
            DependencyIssue(
                rule_id="ENERGY_BALANCE",
                status=severity,
                message=(
                    f"Deck has {len(energy_producers)} energy producer(s) "
                    f"({', '.join(energy_producers[:5])}"
                    f"{', …' if len(energy_producers) > 5 else ''}) but no cards that pay {{E}}."
                ),
                profile_id="energy",
                detail={"producers": energy_producers, "consumers": []},
            )
        )
    elif energy_warn and energy_consumers and not energy_producers:
        report.issues.append(
            DependencyIssue(
                rule_id="ENERGY_BALANCE",
                status=severity,
                message=(
                    f"Deck has {len(energy_consumers)} card(s) that pay {{E}} but no energy producers."
                ),
                profile_id="energy",
                detail={"producers": [], "consumers": energy_consumers},
            )
        )

    report.profiles.append(
        ProfileSummary(
            profile_id="energy",
            counts={"producer": len(energy_producers), "consumer": len(energy_consumers)},
            status=severity if strict and energy_warn else ("warn" if energy_warn else "pass"),
            messages=[],
        )
    )

    sacrifice_imbalanced = (sacrifice_outlets and not sacrifice_payoffs) or (
        sacrifice_payoffs and not sacrifice_outlets
    )
    sacrifice_warn = sacrifice_imbalanced and _should_warn_sacrifice_imbalance(
        scope=dep_scope,
        outlet_count=len(sacrifice_outlets),
        payoff_count=len(sacrifice_payoffs),
    )
    if sacrifice_warn and sacrifice_outlets and not sacrifice_payoffs:
        report.issues.append(
            DependencyIssue(
                rule_id="SACRIFICE_BALANCE",
                status=severity,
                message=(
                    f"Deck has {len(sacrifice_outlets)} sacrifice outlet(s) "
                    f"({', '.join(sacrifice_outlets[:5])}"
                    f"{', …' if len(sacrifice_outlets) > 5 else ''}) but no sacrifice payoffs "
                    f"(e.g. \"whenever a creature dies\")."
                ),
                profile_id="sacrifice",
                detail={"outlets": sacrifice_outlets, "payoffs": []},
            )
        )
    elif sacrifice_warn and sacrifice_payoffs and not sacrifice_outlets:
        report.issues.append(
            DependencyIssue(
                rule_id="SACRIFICE_BALANCE",
                status=severity,
                message=(
                    f"Deck has {len(sacrifice_payoffs)} sacrifice payoff(s) but no cards that "
                    f"let you sacrifice creatures or permanents."
                ),
                profile_id="sacrifice",
                detail={"outlets": [], "payoffs": sacrifice_payoffs},
            )
        )
    report.profiles.append(
        ProfileSummary(
            profile_id="sacrifice",
            counts={
                "outlet": len(sacrifice_outlets),
                "payoff": len(sacrifice_payoffs),
                "fodder": len(sacrifice_fodder),
            },
            status=severity if strict and sacrifice_warn else ("warn" if sacrifice_warn else "pass"),
            messages=[],
        )
    )

    from mtg_deck_tools.rules.dependency_profiles import subtype_lord_minimum

    for card in maindeck:
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind != "buff_subtype":
                continue
            subtypes = effect.payload.get("subtypes") or []
            if not subtypes:
                continue
            subtype = subtypes[0]
            minimum = subtype_lord_minimum(subtype, profile_cfg)
            total = _count_subtype(search_pool, subtype)
            others = total - (1 if subtype in (card.type_line or "") else 0)
            if others < minimum:
                report.issues.append(
                    DependencyIssue(
                        rule_id="TYPE_SYNERGY_MIN",
                        status=severity,
                        message=(
                            f"{card.name} benefits from other {subtype}s, but the deck has "
                            f"only {others} other {subtype}(s) (suggested minimum {minimum})."
                        ),
                        card_name=card.name,
                        card_oracle_id=card.oracle_id,
                        profile_id="subtype_lords",
                        detail={"subtype": subtype, "count": others, "minimum": minimum},
                    )
                )

    for card in maindeck:
        for effect in effects_map.get(card.oracle_id, []):
            if effect.effect_kind != "whenever_cast_type":
                continue
            types = effect.payload.get("types") or []
            if not types:
                continue
            card_type = types[0]
            artifact_min = int(profile_cfg.get("artifacts", {}).get("artifact_min", 8))
            count = _count_type(maindeck, card_type)
            if card_type == "artifact" and count < artifact_min:
                report.issues.append(
                    DependencyIssue(
                        rule_id="TYPE_SYNERGY_MIN",
                        status=severity,
                        message=(
                            f"{card.name} cares about {card_type} spells, but the deck has "
                            f"only {count} {card_type} cards (suggested minimum {artifact_min})."
                        ),
                        card_name=card.name,
                        card_oracle_id=card.oracle_id,
                        profile_id="artifacts",
                        detail={"type": card_type, "count": count, "minimum": artifact_min},
                    )
                )

    aura_cfg = profile_cfg.get("aura_support", {})
    aura_min = int(aura_cfg.get("aura_spell_min", 6))
    aura_status = "pass"
    aura_messages: list[str] = []
    check_aura_floor = _should_check_aura_support_min(
        scope=dep_scope,
        aura_spells=aura_spells,
        effects_map=effects_map,
        maindeck=maindeck,
    )
    if check_aura_floor and aura_spells < aura_min:
        aura_status = severity
        msg = (
            f"Only {aura_spells} Aura card(s) in the deck "
            f"(suggested minimum {aura_min} for aura support)."
        )
        aura_messages.append(msg)
        report.issues.append(
            DependencyIssue(
                rule_id="AURA_SUPPORT_MIN",
                status=severity,
                message=msg,
                profile_id="aura_support",
                detail={"aura_count": aura_spells, "minimum": aura_min},
            )
        )
    report.profiles.append(
        ProfileSummary(
            profile_id="aura_support",
            counts={"aura_spell": aura_spells},
            status=aura_status,
            messages=aura_messages,
        )
    )

    return report


def _describe_payload(payload: dict[str, Any]) -> str:
    if payload.get("any_card"):
        return "any card"
    parts: list[str] = []
    for supertype in payload.get("supertypes") or []:
        parts.append(supertype)
    for card_type in payload.get("types") or []:
        parts.append(card_type)
    for subtype in payload.get("subtypes") or []:
        parts.append(subtype)
    if payload.get("max_cmc") is not None:
        parts.append(f"mana value {payload['max_cmc']} or less")
    return " / ".join(parts) if parts else "the search criteria"


def dependency_report_to_dict(report: DependencyReport) -> dict[str, Any]:
    return {
        "passed": report.passed,
        "issues": [
            {
                "rule_id": i.rule_id,
                "status": i.status,
                "message": i.message,
                "card_name": i.card_name,
                "card_oracle_id": i.card_oracle_id,
                "profile_id": i.profile_id,
                "detail": i.detail,
            }
            for i in report.issues
        ],
        "profiles": [
            {
                "profile_id": p.profile_id,
                "counts": p.counts,
                "status": p.status,
                "messages": p.messages,
            }
            for p in report.profiles
        ],
    }


def dependency_messages(report: DependencyReport) -> list[str]:
    """Flatten dependency issues into build warning strings."""
    messages: list[str] = []
    for issue in report.issues:
        if issue.status == "warn":
            messages.append(f"Dependency: {issue.message}")
        elif issue.status == "fail":
            messages.append(f"Dependency (strict): {issue.message}")
    return messages
