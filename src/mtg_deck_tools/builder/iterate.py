"""User-driven deck iteration: swap selected maindeck cards."""

from __future__ import annotations

import random
from collections import Counter, defaultdict, deque
from dataclasses import dataclass

import sqlite3

from mtg_deck_tools.builder.budget_backfill import trim_deck_to_budget
from mtg_deck_tools.builder.commander_resolve import commander_theme_tags
from mtg_deck_tools.builder.deck import DeckBuildResult, DeckCard
from mtg_deck_tools.builder.filler import (
    _BuildState,
    _fill_lands,
    _init_state_from_cards,
)
from mtg_deck_tools.builder.mana_base import plan_mana_base
from mtg_deck_tools.builder.swap_constraints import (
    SwapPreviewPosition,
    add_candidate_to_state,
    pick_swap_replacement,
    preview_swap_candidates,
)
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.models.swap_constraints import SwapConstraints, SwapPreferredReplacement
from mtg_deck_tools.rules.validate import (
    adjust_slot_template_for_commanders,
    mainboard_size_for_commanders,
)
from mtg_deck_tools.wizard.slots import load_slot_template_config


@dataclass(frozen=True)
class SwapRecord:
    slot: str
    from_oracle_id: str
    from_name: str
    to_oracle_id: str
    to_name: str


@dataclass(frozen=True)
class SwapFailure:
    slot: str
    from_oracle_id: str
    from_name: str
    message: str


def _single_quantity_card(card: DeckCard) -> DeckCard:
    if card.quantity == 1:
        return card
    return DeckCard(
        oracle_id=card.oracle_id,
        name=card.name,
        slot=card.slot,
        quantity=1,
        cmc=card.cmc,
        mana_cost=card.mana_cost,
        type_line=card.type_line,
        price_usd=card.price_usd,
        price_known=card.price_known,
        scryfall_uri=card.scryfall_uri,
        image_uri=card.image_uri,
        mechanic_tags=list(card.mechanic_tags),
        oracle_text=card.oracle_text,
        color_identity=list(card.color_identity),
        produced_mana=list(card.produced_mana),
        released_at=card.released_at,
        power=card.power,
        toughness=card.toughness,
        rarity=card.rarity,
        unpriced_classification=card.unpriced_classification,
        locked=card.locked,
    )


def _restore_removed_card(state: _BuildState, card: DeckCard) -> None:
    state.cards.append(card)
    if "Basic" not in card.type_line:
        state.used_oracle_ids.add(card.oracle_id)
        state.used_names.add(card.name)


def _remove_cards_for_swap(
    cards: list[DeckCard],
    oracle_ids: list[str],
    *,
    commander_oracle_ids: set[str],
) -> tuple[list[DeckCard], list[DeckCard]]:
    """Return remaining cards and ordered single-quantity removals."""
    if not oracle_ids:
        raise ValueError("oracle_ids must not be empty.")

    for oid in oracle_ids:
        if oid in commander_oracle_ids:
            raise ValueError(f"Cannot swap commander card: {oid}")

    to_remove = Counter(oracle_ids)
    remaining: list[DeckCard] = []
    removed: list[DeckCard] = []

    for card in cards:
        pending = to_remove.get(card.oracle_id, 0)
        if pending <= 0:
            remaining.append(card)
            continue
        if card.locked:
            raise ValueError(f"Cannot swap locked card: {card.name}")

        qty_to_remove = min(card.quantity, pending)
        to_remove[card.oracle_id] -= qty_to_remove
        for _ in range(qty_to_remove):
            removed.append(_single_quantity_card(card))

        leftover = card.quantity - qty_to_remove
        if leftover > 0:
            remaining.append(
                DeckCard(
                    oracle_id=card.oracle_id,
                    name=card.name,
                    slot=card.slot,
                    quantity=leftover,
                    cmc=card.cmc,
                    mana_cost=card.mana_cost,
                    type_line=card.type_line,
                    price_usd=card.price_usd,
                    price_known=card.price_known,
                    scryfall_uri=card.scryfall_uri,
                    image_uri=card.image_uri,
                    mechanic_tags=list(card.mechanic_tags),
                    oracle_text=card.oracle_text,
                    color_identity=list(card.color_identity),
                    produced_mana=list(card.produced_mana),
                    released_at=card.released_at,
                    power=card.power,
                    toughness=card.toughness,
                    rarity=card.rarity,
                    unpriced_classification=card.unpriced_classification,
                    locked=card.locked,
                )
            )

    leftover_ids = [oid for oid, count in to_remove.items() if count > 0]
    if leftover_ids:
        raise ValueError(f"oracle_id(s) not found in maindeck: {', '.join(leftover_ids)}")

    return remaining, removed


def _preferred_replacement_queues(
    preferred: list[SwapPreferredReplacement] | None,
) -> dict[str, deque[str]]:
    queues: dict[str, deque[str]] = defaultdict(deque)
    for item in preferred or []:
        queues[item.from_oracle_id].append(item.replacement_oracle_id)
    return queues


def _constraints_for_position(
    base: SwapConstraints | None,
    replacement_oracle_id: str | None,
) -> SwapConstraints | None:
    if not replacement_oracle_id:
        return base
    if base is None:
        return SwapConstraints(replacement_oracle_id=replacement_oracle_id)
    return base.model_copy(update={"replacement_oracle_id": replacement_oracle_id})


def _build_swap_state(
    conn: sqlite3.Connection,
    criteria: DeckCriteria,
    *,
    identity: list[str],
    commander_oracle_ids: list[str],
    fixed_cards: list[DeckCard],
    seed: int | None,
) -> _BuildState:
    commander_set = set(commander_oracle_ids)
    tags = commander_theme_tags(conn, commander_oracle_ids)
    state = _BuildState(
        conn=conn,
        criteria=criteria,
        identity=identity,
        commander_oracle_ids=commander_set,
        commander_theme_tags=tags,
        rng=random.Random(seed if seed is not None else criteria.seed),
    )
    _init_state_from_cards(state, fixed_cards)
    return state


def preview_swap_deck_cards(
    conn: sqlite3.Connection,
    criteria: DeckCriteria,
    *,
    identity: list[str],
    commander_oracle_ids: list[str],
    fixed_cards: list[DeckCard],
    oracle_ids: list[str],
    constraints: SwapConstraints | None = None,
    preview_limit: int = 8,
    seed: int | None = None,
) -> list[SwapPreviewPosition]:
    """Return top candidate picks per vacated position without mutating the deck."""
    commander_set = set(commander_oracle_ids)
    remaining, removed = _remove_cards_for_swap(
        fixed_cards,
        oracle_ids,
        commander_oracle_ids=commander_set,
    )
    state = _build_swap_state(
        conn,
        criteria,
        identity=identity,
        commander_oracle_ids=commander_oracle_ids,
        fixed_cards=remaining,
        seed=seed,
    )
    positions: list[SwapPreviewPosition] = []
    for removed_card in removed:
        candidates = preview_swap_candidates(
            state,
            removed_card.slot,
            constraints=constraints,
            limit=preview_limit,
        )
        positions.append(
            SwapPreviewPosition(
                from_oracle_id=removed_card.oracle_id,
                from_name=removed_card.name,
                slot=removed_card.slot,
                candidates=candidates,
            )
        )
    return positions


def swap_deck_cards(
    conn: sqlite3.Connection,
    criteria: DeckCriteria,
    *,
    identity: list[str],
    commander_oracle_ids: list[str],
    fixed_cards: list[DeckCard],
    oracle_ids: list[str],
    seed: int | None = None,
    constraints: SwapConstraints | None = None,
    preferred_replacements: list[SwapPreferredReplacement] | None = None,
) -> tuple[DeckBuildResult | None, list[SwapRecord], list[SwapFailure]]:
    """Replace selected maindeck cards with new picks under current criteria.

    When a position has no eligible replacement, that card is left unchanged and
    reported in the returned failure list. Other positions still swap.
    """
    slot_config = load_slot_template_config()
    slots = dict(criteria.slot_template or slot_config.default)
    commander_count = max(1, len(commander_oracle_ids))
    slots = adjust_slot_template_for_commanders(slots, commander_count)
    mainboard_size = mainboard_size_for_commanders(commander_count)

    commander_set = set(commander_oracle_ids)
    remaining, removed = _remove_cards_for_swap(
        fixed_cards,
        oracle_ids,
        commander_oracle_ids=commander_set,
    )

    state = _build_swap_state(
        conn,
        criteria,
        identity=identity,
        commander_oracle_ids=commander_oracle_ids,
        fixed_cards=remaining,
        seed=seed,
    )

    swaps: list[SwapRecord] = []
    failures: list[SwapFailure] = []
    preferred_queues = _preferred_replacement_queues(preferred_replacements)
    use_lands_pipeline = constraints is None or not (
        constraints.type_lines_any
        or constraints.replacement_oracle_id
        or constraints.effect_role
    )
    if preferred_queues:
        use_lands_pipeline = False
    for removed_card in removed:
        slot = removed_card.slot
        from_id = removed_card.oracle_id
        from_name = removed_card.name
        preferred_id: str | None = None
        if preferred_queues.get(from_id):
            preferred_id = preferred_queues[from_id].popleft()
        position_constraints = _constraints_for_position(constraints, preferred_id)
        new_card: DeckCard | None = None
        failure_message: str | None = None
        if slot == "lands" and use_lands_pipeline and not preferred_id:
            card_count_before = len(state.cards)
            _fill_lands(state, 1, mainboard_size=mainboard_size)
            if len(state.cards) <= card_count_before:
                failure_message = f"Could not find replacement for {from_name!r} in slot '{slot}'."
            else:
                new_card = state.cards[-1]
        else:
            try:
                pick = pick_swap_replacement(
                    state,
                    slot,
                    constraints=position_constraints,
                    rng=state.rng,
                )
            except ValueError as exc:
                failure_message = str(exc)
                pick = None
            else:
                if pick is None:
                    failure_message = (
                        f"Could not find replacement for {from_name!r} in slot '{slot}'."
                    )
                else:
                    new_card = add_candidate_to_state(state, slot, pick)
        if failure_message is not None:
            _restore_removed_card(state, removed_card)
            failures.append(
                SwapFailure(
                    slot=slot,
                    from_oracle_id=from_id,
                    from_name=from_name,
                    message=failure_message,
                )
            )
            continue
        assert new_card is not None
        swaps.append(
            SwapRecord(
                slot=slot,
                from_oracle_id=from_id,
                from_name=from_name,
                to_oracle_id=new_card.oracle_id,
                to_name=new_card.name,
            )
        )

    if not swaps:
        return None, swaps, failures

    if swaps:
        state.warnings.append(f"Swapped {len(swaps)} maindeck card(s).")
    if failures:
        state.warnings.append(
            f"Could not swap {len(failures)} of {len(removed)} selected card(s)."
        )

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

    mana_plan = plan_mana_base(
        cards,
        identity=identity,
        template_lands=slots.get("lands", 0),
        min_lands=slot_config.bounds["lands"].min,
        max_lands=slot_config.bounds["lands"].max,
        mainboard_size=mainboard_size,
    )
    warnings = list(warnings)
    warnings.extend(mana_plan.warnings)

    return (
        DeckBuildResult(
            cards=cards,
            warnings=warnings,
            budget_spent=budget_spent,
            unpriced_names=state.unpriced_names,
            mana_base=mana_plan,
        ),
        swaps,
        failures,
    )
