"""Guided slot filling for Commander decks."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field

import sqlite3

from mtg_deck_tools.builder.pool import CardCandidate, fetch_candidates, fetch_card_tags
from mtg_deck_tools.builder.scorer import score_candidate
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.wizard.slots import SLOT_FILLER_THEME_TAGS, load_slot_template_config

FILL_ORDER = ("ramp", "draw", "removal", "board_wipe", "synergy", "wincon", "flex", "lands")

BASIC_NAME_BY_COLOR = {
    "W": "Plains",
    "U": "Island",
    "B": "Swamp",
    "R": "Mountain",
    "G": "Forest",
}

TOP_POOL_SIZE = 40


@dataclass
class DeckCard:
    oracle_id: str
    name: str
    slot: str
    quantity: int
    cmc: float
    mana_cost: str
    type_line: str
    price_usd: float | None
    price_known: bool
    scryfall_uri: str | None
    image_uri: str | None
    mechanic_tags: list[str] = field(default_factory=list)


@dataclass
class DeckBuildResult:
    cards: list[DeckCard]
    warnings: list[str]
    budget_spent: float
    unpriced_names: list[str]


@dataclass
class _BuildState:
    conn: sqlite3.Connection
    criteria: DeckCriteria
    identity: list[str]
    commander_oracle_ids: set[str]
    commander_theme_tags: set[str]
    rng: random.Random
    cards: list[DeckCard] = field(default_factory=list)
    used_oracle_ids: set[str] = field(default_factory=set)
    used_names: set[str] = field(default_factory=set)
    budget_spent: float = 0.0
    warnings: list[str] = field(default_factory=list)
    unpriced_names: list[str] = field(default_factory=list)

    def budget_remaining(self) -> float | None:
        if self.criteria.budget_usd is None:
            return None
        return max(0.0, self.criteria.budget_usd - self.budget_spent)

    def register(self, candidate: CardCandidate, slot: str, *, quantity: int = 1) -> None:
        if candidate.is_basic_land:
            for card in self.cards:
                if card.oracle_id == candidate.oracle_id and card.slot == slot:
                    card.quantity += quantity
                    if candidate.price_known and candidate.price_usd is not None:
                        self.budget_spent += candidate.price_usd * quantity
                    return

        tags = fetch_card_tags(self.conn, [candidate.oracle_id]).get(candidate.oracle_id, [])
        self.cards.append(
            DeckCard(
                oracle_id=candidate.oracle_id,
                name=candidate.name,
                slot=slot,
                quantity=quantity,
                cmc=candidate.cmc,
                mana_cost=candidate.mana_cost,
                type_line=candidate.type_line,
                price_usd=candidate.price_usd,
                price_known=candidate.price_known,
                scryfall_uri=candidate.scryfall_uri,
                image_uri=candidate.image_uri,
                mechanic_tags=tags,
            )
        )
        if not candidate.is_basic_land:
            self.used_oracle_ids.add(candidate.oracle_id)
            self.used_names.add(candidate.name)
        if candidate.price_known and candidate.price_usd is not None:
            self.budget_spent += candidate.price_usd * quantity
        elif self.criteria.budget_usd is not None and candidate.name not in self.unpriced_names:
            self.unpriced_names.append(candidate.name)
            self.warnings.append(f"No USD price for {candidate.name}; not counted toward budget.")


def _slot_theme_tags(slot: str, criteria: DeckCriteria) -> list[str] | None:
    if slot in SLOT_FILLER_THEME_TAGS:
        return [slot]
    if slot == "synergy" and criteria.themes:
        return list(criteria.themes)
    return None


def _type_counts(cards: list[DeckCard]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for card in cards:
        if "Land" in card.type_line:
            continue
        primary = card.type_line.split("—")[0].strip().split()
        key = primary[-1] if primary else "Other"
        counts[key] = counts.get(key, 0) + card.quantity
    return counts


def _pip_weights(cards: list[DeckCard], identity: list[str]) -> dict[str, int]:
    weights = {c: 1 for c in identity}
    for card in cards:
        if "Land" in card.type_line:
            continue
        for match in re.findall(r"\{([WUBRG])\}", card.mana_cost):
            if match in weights:
                weights[match] += 1
    return weights


def _pick_weighted(
    rng: random.Random,
    scored: list[tuple[CardCandidate, float]],
    count: int,
) -> list[CardCandidate]:
    pool = list(scored[:TOP_POOL_SIZE])
    picked: list[CardCandidate] = []
    while pool and len(picked) < count:
        weights = [max(score, 0.01) for _, score in pool]
        idx = rng.choices(range(len(pool)), weights=weights, k=1)[0]
        candidate, _ = pool.pop(idx)
        picked.append(candidate)
    return picked


def _filter_budget(
    candidates: list[CardCandidate],
    budget_remaining: float | None,
    *,
    strict: bool,
) -> list[CardCandidate]:
    if budget_remaining is None:
        return candidates
    if not strict:
        return candidates
    return [
        c
        for c in candidates
        if not c.price_known
        or c.price_usd is None
        or c.price_usd <= budget_remaining
    ]


def _fill_slot(state: _BuildState, slot: str, count: int) -> None:
    if count <= 0:
        return

    theme_tags = _slot_theme_tags(slot, state.criteria)
    relax_steps: list[list[str] | None] = [theme_tags]
    if theme_tags is not None:
        relax_steps.append(None)

    candidates: list[CardCandidate] = []
    for require_tags in relax_steps:
        candidates = fetch_candidates(
            state.conn,
            identity=state.identity,
            exclude_oracle_ids=state.used_oracle_ids | state.commander_oracle_ids,
            exclude_names=state.used_names,
            avoid_mechanics=state.criteria.avoid_mechanics,
            require_theme_tags=require_tags,
            nonlands_only=True,
        )
        candidates = _filter_budget(candidates, state.budget_remaining(), strict=False)
        if len(candidates) >= count:
            break
        if require_tags is None:
            break

    if len(candidates) < count:
        state.warnings.append(
            f"Slot '{slot}': only {len(candidates)} candidates available (wanted {count})."
        )

    tag_map = fetch_card_tags(state.conn, [c.oracle_id for c in candidates])
    scored: list[tuple[CardCandidate, float]] = []
    type_counts = _type_counts(state.cards)
    for candidate in candidates:
        score = score_candidate(
            candidate,
            slot=slot,
            archetype_themes=state.criteria.themes,
            include_mechanics=state.criteria.include_mechanics,
            commander_theme_tags=state.commander_theme_tags,
            card_tags=tag_map.get(candidate.oracle_id, []),
            type_counts=type_counts,
            budget_remaining=state.budget_remaining(),
        )
        scored.append((candidate, score))
    scored.sort(key=lambda item: item[1], reverse=True)

    for candidate in _pick_weighted(state.rng, scored, count):
        state.register(candidate, slot)


def _fill_lands(state: _BuildState, count: int) -> None:
    if count <= 0:
        return

    nonbasic_target = max(0, count - len(state.identity))
    basics_target = count - nonbasic_target

    nonbasics = fetch_candidates(
        state.conn,
        identity=state.identity,
        exclude_oracle_ids=state.used_oracle_ids | state.commander_oracle_ids,
        exclude_names=state.used_names,
        avoid_mechanics=state.criteria.avoid_mechanics,
        require_theme_tags=None,
        lands_only=True,
        limit=300,
    )
    nonbasics = [c for c in nonbasics if not c.is_basic_land]
    nonbasics = _filter_budget(nonbasics, state.budget_remaining(), strict=False)

    tag_map = fetch_card_tags(state.conn, [c.oracle_id for c in nonbasics])
    scored = [
        (
            c,
            score_candidate(
                c,
                slot="lands",
                archetype_themes=state.criteria.themes,
                include_mechanics=state.criteria.include_mechanics,
                commander_theme_tags=state.commander_theme_tags,
                card_tags=tag_map.get(c.oracle_id, []),
                type_counts=_type_counts(state.cards),
                budget_remaining=state.budget_remaining(),
            ),
        )
        for c in nonbasics
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    for candidate in _pick_weighted(state.rng, scored, min(nonbasic_target, len(scored))):
        state.register(candidate, "lands")

    remaining = count - sum(c.quantity for c in state.cards if c.slot == "lands")
    if remaining <= 0:
        return

    pip_weights = _pip_weights(state.cards, state.identity)
    total_pips = sum(pip_weights.values()) or 1
    basics_by_color: list[str] = []
    for color in state.identity:
        name = BASIC_NAME_BY_COLOR[color]
        share = max(1, round(remaining * pip_weights[color] / total_pips))
        basics_by_color.extend([name] * share)

    while len(basics_by_color) < remaining:
        color = state.rng.choice(state.identity)
        basics_by_color.append(BASIC_NAME_BY_COLOR[color])
    basics_by_color = basics_by_color[:remaining]

    for basic_name in basics_by_color:
        row = state.conn.execute(
            """
            SELECT oracle_id, name, cmc, type_line, mana_cost, color_identity,
                   price_usd, price_known, edhrec_rank, oracle_text, keywords,
                   is_basic_land, scryfall_uri, image_uri
            FROM cards
            WHERE is_basic_land = 1 AND name = ?
            LIMIT 1
            """,
            (basic_name,),
        ).fetchone()
        if not row:
            state.warnings.append(f"Basic land '{basic_name}' not found in database.")
            continue
        candidate = CardCandidate(
            oracle_id=row["oracle_id"],
            name=row["name"],
            cmc=float(row["cmc"] or 0),
            type_line=row["type_line"] or "",
            mana_cost=row["mana_cost"] or "",
            color_identity=json.loads(row["color_identity"] or "[]"),
            price_usd=row["price_usd"],
            price_known=bool(row["price_known"]),
            edhrec_rank=row["edhrec_rank"],
            oracle_text=row["oracle_text"] or "",
            keywords=json.loads(row["keywords"] or "[]"),
            is_basic_land=True,
            scryfall_uri=row["scryfall_uri"],
            image_uri=row["image_uri"],
        )
        state.register(candidate, "lands")


def fill_deck(
    conn: sqlite3.Connection,
    criteria: DeckCriteria,
    *,
    identity: list[str],
    commander_oracle_ids: list[str],
    seed: int | None = None,
) -> DeckBuildResult:
    """Fill all slots from criteria and return the 99-card maindeck."""
    slot_config = load_slot_template_config()
    slots = criteria.slot_template or dict(slot_config.default)

    commander_tags: set[str] = set()
    if commander_oracle_ids:
        tag_rows = conn.execute(
            """
            SELECT tag FROM card_mechanic_tags
            WHERE oracle_id IN ({})
            """.format(",".join("?" * len(commander_oracle_ids))),
            commander_oracle_ids,
        ).fetchall()
        commander_tags = {row["tag"] for row in tag_rows}

    state = _BuildState(
        conn=conn,
        criteria=criteria,
        identity=identity,
        commander_oracle_ids=set(commander_oracle_ids),
        commander_theme_tags=commander_tags,
        rng=random.Random(seed if seed is not None else criteria.seed),
    )

    for slot in FILL_ORDER:
        count = slots.get(slot, 0)
        if slot == "lands":
            _fill_lands(state, count)
        else:
            _fill_slot(state, slot, count)

    return DeckBuildResult(
        cards=state.cards,
        warnings=state.warnings,
        budget_spent=state.budget_spent,
        unpriced_names=state.unpriced_names,
    )
