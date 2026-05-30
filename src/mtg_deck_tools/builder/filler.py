"""Guided slot filling for Commander decks."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field

import sqlite3

from mtg_deck_tools.builder.budget_backfill import trim_deck_to_budget
from mtg_deck_tools.builder.price_filters import filter_candidates_by_price
from mtg_deck_tools.builder.rarity_filters import filter_candidates_by_rarity
from mtg_deck_tools.builder.deck import DeckBuildResult, DeckCard, slot_theme_tags
from mtg_deck_tools.builder.mana_base import (
    BASIC_NAME_BY_COLOR,
    ManaBasePlan,
    allocate_basics,
    plan_mana_base,
    score_land_candidate,
    tally_mana_sources,
    validate_mana_sources,
)
from mtg_deck_tools.builder.pool import CardCandidate, fetch_candidates, fetch_card_tags
from mtg_deck_tools.builder.scorer import score_candidate, score_land_budget
from mtg_deck_tools.builder.slot_quality import refine_slot_candidates, slot_relax_steps
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.validate import (
    adjust_slot_template_for_commanders,
    mainboard_size_for_commanders,
)
from mtg_deck_tools.wizard.slots import load_slot_template_config

# Re-export for callers that import from filler.
from mtg_deck_tools.builder.deck import DeckBuildResult, DeckCard  # noqa: F401

FILL_ORDER = ("ramp", "draw", "removal", "board_wipe", "synergy", "wincon", "flex", "lands")

TOP_POOL_SIZE = 40


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
                oracle_text=candidate.oracle_text,
                produced_mana=list(candidate.produced_mana),
                released_at=candidate.released_at,
                power=candidate.power,
                toughness=candidate.toughness,
                rarity=candidate.rarity,
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


def _type_counts(cards: list[DeckCard]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for card in cards:
        if "Land" in card.type_line:
            continue
        primary = card.type_line.split("—")[0].strip().split()
        key = primary[-1] if primary else "Other"
        counts[key] = counts.get(key, 0) + card.quantity
    return counts


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


def _fill_slot(state: _BuildState, slot: str, count: int) -> None:
    if count <= 0:
        return

    candidates: list[CardCandidate] = []
    for require_tags in slot_relax_steps(slot, state.criteria):
        pool = fetch_candidates(
            state.conn,
            identity=state.identity,
            exclude_oracle_ids=state.used_oracle_ids | state.commander_oracle_ids,
            exclude_names=state.used_names,
            avoid_mechanics=state.criteria.avoid_mechanics,
            require_theme_tags=require_tags,
            nonlands_only=True,
        )
        pool = filter_candidates_by_price(
            pool,
            state.criteria,
            state.budget_remaining(),
        )
        pool = filter_candidates_by_rarity(pool, state.criteria)
        tag_map = fetch_card_tags(state.conn, [c.oracle_id for c in pool])
        pool = refine_slot_candidates(
            slot,
            pool,
            tag_map,
            criteria=state.criteria,
            require_theme_tags=require_tags,
        )
        if pool:
            candidates = pool
        if len(candidates) >= count:
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
            budget_usd=state.criteria.budget_usd,
        )
        scored.append((candidate, score))
    scored.sort(key=lambda item: item[1], reverse=True)

    for candidate in _pick_weighted(state.rng, scored, count):
        state.register(candidate, slot)


def _fill_lands(
    state: _BuildState,
    template_lands: int,
    *,
    mainboard_size: int,
) -> ManaBasePlan:
    slot_config = load_slot_template_config()
    land_bounds = slot_config.bounds["lands"]
    plan = plan_mana_base(
        state.cards,
        identity=state.identity,
        template_lands=template_lands,
        min_lands=land_bounds.min,
        max_lands=land_bounds.max,
        mainboard_size=mainboard_size,
    )
    state.warnings.extend(plan.warnings)

    nonbasics = fetch_candidates(
        state.conn,
        identity=state.identity,
        exclude_oracle_ids=state.used_oracle_ids | state.commander_oracle_ids,
        exclude_names=state.used_names,
        avoid_mechanics=state.criteria.avoid_mechanics,
        require_theme_tags=None,
        lands_only=True,
        limit=400,
    )
    nonbasics = [c for c in nonbasics if not c.is_basic_land]
    nonbasics = filter_candidates_by_price(
        nonbasics,
        state.criteria,
        state.budget_remaining(),
    )

    tag_map = fetch_card_tags(state.conn, [c.oracle_id for c in nonbasics])
    scored: list[tuple[CardCandidate, float]] = []
    for candidate in nonbasics:
        pip_score = score_land_candidate(
            candidate,
            pip_weights=plan.pip_weights,
            identity=state.identity,
        )
        card_score = score_candidate(
            candidate,
            slot="lands",
            archetype_themes=state.criteria.themes,
            include_mechanics=state.criteria.include_mechanics,
            commander_theme_tags=state.commander_theme_tags,
            card_tags=tag_map.get(candidate.oracle_id, []),
            type_counts=_type_counts(state.cards),
            budget_remaining=state.budget_remaining(),
        )
        land_budget = score_land_budget(
            candidate,
            budget_remaining=state.budget_remaining(),
            budget_total=state.criteria.budget_usd,
        )
        scored.append((candidate, card_score + pip_score + land_budget))
    scored.sort(key=lambda item: item[1], reverse=True)

    picked_nonbasics = _pick_weighted(
        state.rng,
        scored,
        min(plan.nonbasic_target, len(scored)),
    )
    for candidate in picked_nonbasics:
        state.register(candidate, "lands")

    filled_nonbasic_qty = sum(
        c.quantity for c in state.cards if c.slot == "lands" and "Basic" not in c.type_line
    )
    remaining_basics = max(0, plan.actual_lands - filled_nonbasic_qty)

    basics_by_color = allocate_basics(
        remaining_basics,
        plan.pip_weights,
        state.identity,
    )

    sources = tally_mana_sources(
        identity=state.identity,
        basics=basics_by_color,
        nonbasic_candidates=picked_nonbasics,
        ramp_cards=[c for c in state.cards if c.slot == "ramp"],
        nonland_cards=state.cards,
    )
    state.warnings.extend(
        validate_mana_sources(sources, state.identity, num_colors=plan.num_colors)
    )

    for basic_name in basics_by_color:
        row = state.conn.execute(
            """
            SELECT oracle_id, name, cmc, type_line, mana_cost, color_identity,
                   price_usd, price_known, edhrec_rank, oracle_text, keywords,
                   is_basic_land, produced_mana, scryfall_uri, image_uri, released_at,
                   power, toughness
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
            produced_mana=json.loads(row["produced_mana"] or "[]"),
            scryfall_uri=row["scryfall_uri"],
            image_uri=row["image_uri"],
            released_at=row["released_at"],
            power=row["power"],
            toughness=row["toughness"],
        )
        state.register(candidate, "lands")

    return plan


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
    slots = dict(criteria.slot_template or slot_config.default)
    commander_count = max(1, len(commander_oracle_ids))
    slots = adjust_slot_template_for_commanders(slots, commander_count)
    mainboard_size = mainboard_size_for_commanders(commander_count)

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

    mana_plan: ManaBasePlan | None = None
    for slot in FILL_ORDER:
        count = slots.get(slot, 0)
        if slot == "lands":
            mana_plan = _fill_lands(state, count, mainboard_size=mainboard_size)
        else:
            _fill_slot(state, slot, count)

    cards, budget_spent, warnings = trim_deck_to_budget(
        conn,
        state.cards,
        state.criteria,
        identity=identity,
        commander_oracle_ids=state.commander_oracle_ids,
        commander_theme_tags=state.commander_theme_tags,
        unpriced_names=state.unpriced_names,
        warnings=state.warnings,
    )

    return DeckBuildResult(
        cards=cards,
        warnings=warnings,
        budget_spent=budget_spent,
        unpriced_names=state.unpriced_names,
        mana_base=mana_plan,
    )
