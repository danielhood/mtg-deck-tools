"""Ensure included / selected mechanics meet profile floors after slot fill."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from mtg_deck_tools.builder.dependency_repair import (
    MAX_REPAIR_SWAPS,
    swap_effect_kind_card,
    swap_energy_card,
    swap_matching_card,
)
from mtg_deck_tools.builder.dependency_scoring import card_effects_enabled
from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import (
    _payload_searches_auras,
    _payload_searches_enchantments,
    _should_check_aura_support_min,
    _should_check_enchantment_support_min,
    fetch_card_effects,
)
from mtg_deck_tools.rules.dependency_profiles import (
    artifact_spell_min,
    aura_spell_min,
    enchantment_spell_min,
    energy_profile_floors,
    sacrifice_profile_floors,
    subtype_lord_minimum,
    token_profile_floors,
    equipment_profile_floors,
    vehicle_profile_floors,
)
from mtg_deck_tools.rules.dependency_scope import build_dependency_scope
from mtg_deck_tools.rules.resource_counters import (
    RESOURCE_COUNTER_SPECS,
    count_resource_cards,
    resource_profile_floors,
    resource_role_oracle_ids,
)


@dataclass
class MechanicPackageResult:
    cards: list[DeckCard]
    messages: list[str]
    swaps: int = 0


def count_aura_spells(cards: list[DeckCard]) -> int:
    return sum(1 for c in cards if "Aura" in (c.type_line or ""))


def count_enchantment_spells(cards: list[DeckCard]) -> int:
    return sum(1 for c in cards if "Enchantment" in (c.type_line or ""))


def count_type_on_maindeck(cards: list[DeckCard], card_type: str) -> int:
    needle = card_type.capitalize()
    return sum(1 for c in cards if needle in (c.type_line or ""))



def count_vehicles_on_maindeck(cards: list[DeckCard]) -> int:
    return sum(1 for c in cards if "Vehicle" in (c.type_line or ""))


def count_crew_creatures_on_maindeck(cards: list[DeckCard]) -> int:
    return sum(
        1
        for c in cards
        if "Creature" in (c.type_line or "") and "Vehicle" not in (c.type_line or "")
    )


def count_equipment_on_maindeck(cards: list[DeckCard]) -> int:
    return sum(1 for c in cards if "Equipment" in (c.type_line or ""))


def count_carrier_creatures_on_maindeck(cards: list[DeckCard]) -> int:
    return sum(
        1
        for c in cards
        if "Creature" in (c.type_line or "") and "Vehicle" not in (c.type_line or "")
    )


def count_subtype_creatures(cards: list[DeckCard], subtype: str) -> int:
    return sum(
        1
        for c in cards
        if subtype in (c.type_line or "") and "Creature" in (c.type_line or "")
    )


def _energy_role_oracle_ids(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
) -> tuple[set[str], set[str]]:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    producers: set[str] = set()
    consumers: set[str] = set()
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == "energy_produce":
                producers.add(card.oracle_id)
            elif effect.effect_kind == "energy_consume":
                consumers.add(card.oracle_id)
    return producers, consumers


def count_energy_cards(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
) -> tuple[int, int]:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    producers = 0
    consumers = 0
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == "energy_produce":
                producers += 1
            elif effect.effect_kind == "energy_consume":
                consumers += 1
    return producers, consumers


def _sacrifice_role_oracle_ids(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
) -> tuple[set[str], set[str], set[str]]:
    from mtg_deck_tools.rules.sacrifice_roles import card_is_sacrifice_fodder

    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    outlets: set[str] = set()
    payoffs: set[str] = set()
    fodders: set[str] = set()
    for card in cards:
        card_effects = effects.get(card.oracle_id, [])
        for effect in card_effects:
            if effect.effect_kind == "sacrifice_outlet":
                outlets.add(card.oracle_id)
            elif effect.effect_kind == "sacrifice_payoff":
                payoffs.add(card.oracle_id)
        if card_is_sacrifice_fodder(card_effects):
            fodders.add(card.oracle_id)
    return outlets, payoffs, fodders


def count_sacrifice_cards(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
) -> tuple[int, int, int]:
    from mtg_deck_tools.rules.sacrifice_roles import count_sacrifice_roles

    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    outlets, payoffs, fodders, _, _ = count_sacrifice_roles(effects, cards)
    return outlets, payoffs, fodders


def _token_role_oracle_ids(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
) -> tuple[set[str], set[str]]:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    producers: set[str] = set()
    payoffs: set[str] = set()
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == "token_produce":
                producers.add(card.oracle_id)
            elif effect.effect_kind == "token_payoff":
                payoffs.add(card.oracle_id)
    return producers, payoffs


def count_token_cards(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
) -> tuple[int, int]:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    producers = 0
    payoffs = 0
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == "token_produce":
                producers += 1
            elif effect.effect_kind == "token_payoff":
                payoffs += 1
    return producers, payoffs


def _lords_in_deck(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
) -> list[tuple[str, str, str]]:
    """Return (lord_oracle_id, lord_name, subtype) for each subtype lord in deck."""
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    lords: list[tuple[str, str, str]] = []
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind != "buff_subtype":
                continue
            subtypes = effect.payload.get("subtypes") or []
            if subtypes:
                lords.append((card.oracle_id, card.name, subtypes[0]))
    return lords


def _deck_has_artifact_payoff(conn: sqlite3.Connection, cards: list[DeckCard]) -> bool:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    for card_effects in effects.values():
        for effect in card_effects:
            if effect.effect_kind == "whenever_cast_type":
                types = effect.payload.get("types") or []
                if types == ["artifact"]:
                    return True
    return False




def _deck_has_vehicle_payoff(conn: sqlite3.Connection, cards: list[DeckCard]) -> bool:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    for card_effects in effects.values():
        for effect in card_effects:
            if effect.effect_kind != "buff_subtype":
                continue
            subtypes = effect.payload.get("subtypes") or []
            if subtypes and subtypes[0] == "Vehicle":
                return True
    return False


def _vehicle_payoff_oracle_ids(conn: sqlite3.Connection, cards: list[DeckCard]) -> set[str]:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    ids: set[str] = set()
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == "buff_subtype":
                subtypes = effect.payload.get("subtypes") or []
                if subtypes and subtypes[0] == "Vehicle":
                    ids.add(card.oracle_id)
    return ids

def _run_swap_loop(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    package_name: str,
    need_more: Callable[[list[DeckCard]], bool],
    swap_fn: Callable[[list[DeckCard]], tuple[list[DeckCard], str] | None],
    failure_message: Callable[[list[DeckCard]], str],
) -> MechanicPackageResult:
    working = list(cards)
    messages: list[str] = []
    swaps = 0

    for _ in range(MAX_REPAIR_SWAPS):
        if not need_more(working):
            break
        result = swap_fn(working)
        if result is None:
            messages.append(failure_message(working))
            break
        working, msg = result
        messages.append(msg.replace("Dependency repair:", f"{package_name}:"))
        swaps += 1

    return MechanicPackageResult(working, messages, swaps)


def ensure_energy_package(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    scope = build_dependency_scope(criteria)
    if not scope.energy_user_intent:
        return MechanicPackageResult(list(cards), [])

    producer_min, consumer_min = energy_profile_floors()
    working = list(cards)
    messages: list[str] = []
    swaps = 0

    for _ in range(MAX_REPAIR_SWAPS):
        producers, consumers = count_energy_cards(conn, working)
        if producers >= producer_min and consumers >= consumer_min:
            break

        if producers < producer_min:
            effect_kind = "energy_produce"
        elif consumers < consumer_min:
            effect_kind = "energy_consume"
        elif producers > 0 and consumers == 0:
            effect_kind = "energy_consume"
        elif consumers > 0 and producers == 0:
            effect_kind = "energy_produce"
        else:
            break

        producer_ids, consumer_ids = _energy_role_oracle_ids(conn, working)
        protect: set[str] = set()
        if effect_kind == "energy_produce" and len(consumer_ids) < consumer_min:
            protect = consumer_ids
        elif effect_kind == "energy_consume" and len(producer_ids) < producer_min:
            protect = producer_ids

        result = swap_energy_card(
            conn,
            working,
            effect_kind,
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
            protect_oracle_ids=protect,
        )
        if result is None:
            messages.append(
                f"Energy package: could not add {effect_kind.replace('_', ' ')} "
                f"(have {producers} producer(s), {consumers} consumer(s); "
                f"want ≥{producer_min} / ≥{consumer_min})."
            )
            break
        working, msg = result
        messages.append(msg.replace("Dependency repair:", "Energy package:"))
        swaps += 1

    return MechanicPackageResult(working, messages, swaps)


def ensure_resource_counter_packages(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    scope = build_dependency_scope(criteria)
    working = list(cards)
    all_messages: list[str] = []
    total_swaps = 0

    for spec in RESOURCE_COUNTER_SPECS:
        if not scope.resource_user_intent(spec.profile_id):
            continue

        producer_min, consumer_min = resource_profile_floors(spec.profile_id)
        messages: list[str] = []
        swaps = 0
        label = spec.display_name.title()

        for _ in range(MAX_REPAIR_SWAPS):
            producers, consumers = count_resource_cards(conn, working, spec)
            if producers >= producer_min and consumers >= consumer_min:
                break

            if producers < producer_min:
                effect_kind = spec.produce_kind
            elif consumers < consumer_min:
                effect_kind = spec.consume_kind
            elif producers > 0 and consumers == 0:
                effect_kind = spec.consume_kind
            elif consumers > 0 and producers == 0:
                effect_kind = spec.produce_kind
            else:
                break

            producer_ids, consumer_ids = resource_role_oracle_ids(conn, working, spec)
            protect: set[str] = set()
            if effect_kind == spec.produce_kind and len(consumer_ids) < consumer_min:
                protect = consumer_ids
            elif effect_kind == spec.consume_kind and len(producer_ids) < producer_min:
                protect = producer_ids

            role = "payoff" if effect_kind == spec.consume_kind else "producer"
            result = swap_effect_kind_card(
                conn,
                working,
                effect_kind,
                role_label=f"{spec.display_name} {role}",
                criteria=criteria,
                identity=identity,
                commander_oracle_ids=commander_oracle_ids,
                commander_theme_tags=commander_theme_tags,
                protect_oracle_ids=protect,
            )
            if result is None:
                messages.append(
                    f"{label} package: could not add {effect_kind.replace('_', ' ')} "
                    f"(have {producers} producer(s), {consumers} consumer(s); "
                    f"want ≥{producer_min} / ≥{consumer_min})."
                )
                break
            working, msg = result
            messages.append(msg.replace("Dependency repair:", f"{label} package:"))
            swaps += 1

        all_messages.extend(messages)
        total_swaps += swaps

    return MechanicPackageResult(working, all_messages, total_swaps)


def ensure_sacrifice_package(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    scope = build_dependency_scope(criteria)
    if not scope.sacrifice_user_intent:
        return MechanicPackageResult(list(cards), [])

    outlet_min, payoff_min, fodder_min = sacrifice_profile_floors()
    working = list(cards)
    messages: list[str] = []
    swaps = 0

    for _ in range(MAX_REPAIR_SWAPS):
        outlets, payoffs, fodders = count_sacrifice_cards(conn, working)
        if outlets >= outlet_min and payoffs >= payoff_min and fodders >= fodder_min:
            break

        if outlets < outlet_min:
            effect_kind = "sacrifice_outlet"
        elif payoffs < payoff_min:
            effect_kind = "sacrifice_payoff"
        elif fodders < fodder_min:
            effect_kind = "__fodder__"
        elif outlets > 0 and payoffs == 0:
            effect_kind = "sacrifice_payoff"
        elif payoffs > 0 and outlets == 0:
            effect_kind = "sacrifice_outlet"
        else:
            break

        outlet_ids, payoff_ids, fodder_ids = _sacrifice_role_oracle_ids(conn, working)
        protect: set[str] = set()
        if effect_kind == "sacrifice_outlet" and len(payoff_ids) <= payoff_min:
            protect = payoff_ids
        elif effect_kind == "sacrifice_payoff" and len(outlet_ids) <= outlet_min:
            protect = outlet_ids
        elif effect_kind in ("sacrifice_fodder", "__fodder__"):
            if len(outlet_ids) <= outlet_min:
                protect |= outlet_ids
            if len(payoff_ids) <= payoff_min:
                protect |= payoff_ids

        if effect_kind == "__fodder__":
            from mtg_deck_tools.rules.sacrifice_roles import fodder_effect_kinds_for_swap

            result = None
            for fodder_kind in fodder_effect_kinds_for_swap():
                result = swap_effect_kind_card(
                    conn,
                    working,
                    fodder_kind,
                    role_label="sacrifice fodder",
                    criteria=criteria,
                    identity=identity,
                    commander_oracle_ids=commander_oracle_ids,
                    commander_theme_tags=commander_theme_tags,
                    protect_oracle_ids=protect,
                )
                if result is not None:
                    break
        else:
            role_label = effect_kind.replace("sacrifice_", "sacrifice ")
            result = swap_effect_kind_card(
                conn,
                working,
                effect_kind,
                role_label=role_label,
                criteria=criteria,
                identity=identity,
                commander_oracle_ids=commander_oracle_ids,
                commander_theme_tags=commander_theme_tags,
                protect_oracle_ids=protect,
            )
        if result is None:
            messages.append(
                f"Sacrifice package: could not add {role_label} "
                f"(have {outlets} outlet(s), {payoffs} payoff(s), {fodders} fodder; "
                f"want ≥{outlet_min} / ≥{payoff_min} / ≥{fodder_min})."
            )
            break
        working, msg = result
        messages.append(msg.replace("Dependency repair:", "Sacrifice package:"))
        swaps += 1

    return MechanicPackageResult(working, messages, swaps)


def ensure_token_package(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    scope = build_dependency_scope(criteria)
    if not scope.tokens_user_intent:
        return MechanicPackageResult(list(cards), [])

    producer_min, payoff_min = token_profile_floors()
    working = list(cards)
    messages: list[str] = []
    swaps = 0

    for _ in range(MAX_REPAIR_SWAPS):
        producers, payoffs = count_token_cards(conn, working)
        if producers >= producer_min and payoffs >= payoff_min:
            break

        if producers < producer_min:
            effect_kind = "token_produce"
        elif payoffs < payoff_min:
            effect_kind = "token_payoff"
        elif producers > 0 and payoffs == 0:
            effect_kind = "token_payoff"
        elif payoffs > 0 and producers == 0:
            effect_kind = "token_produce"
        else:
            break

        producer_ids, payoff_ids = _token_role_oracle_ids(conn, working)
        protect: set[str] = set()
        if effect_kind == "token_produce" and len(payoff_ids) <= payoff_min:
            protect = payoff_ids
        elif effect_kind == "token_payoff":
            if len(producer_ids) <= producer_min:
                protect |= producer_ids
            protect |= payoff_ids
            for lord_id, _, subtype in _lords_in_deck(conn, working):
                minimum = subtype_lord_minimum(subtype)
                others = sum(
                    1
                    for c in working
                    if c.oracle_id != lord_id
                    and subtype in (c.type_line or "")
                    and "Creature" in (c.type_line or "")
                )
                if others < minimum:
                    protect.add(lord_id)
                    for card in working:
                        if subtype in (card.type_line or "") and "Creature" in (
                            card.type_line or ""
                        ):
                            protect.add(card.oracle_id)

        role_label = effect_kind.replace("token_", "token ")
        result = swap_effect_kind_card(
            conn,
            working,
            effect_kind,
            role_label=role_label,
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
            protect_oracle_ids=protect,
        )
        if result is None:
            messages.append(
                f"Token package: could not add {role_label} "
                f"(have {producers} producer(s), {payoffs} payoff(s); "
                f"want ≥{producer_min} / ≥{payoff_min})."
            )
            break
        working, msg = result
        messages.append(msg.replace("Dependency repair:", "Token package:"))
        swaps += 1

    return MechanicPackageResult(working, messages, swaps)


def ensure_aura_package(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    scope = build_dependency_scope(criteria)
    effects_map = fetch_card_effects(conn, [c.oracle_id for c in cards])
    if not _should_check_aura_support_min(
        scope=scope,
        aura_spells=count_aura_spells(cards),
        effects_map=effects_map,
        maindeck=cards,
    ):
        return MechanicPackageResult(list(cards), [])

    minimum = aura_spell_min()

    def _aura_protect_ids(deck: list[DeckCard]) -> set[str]:
        protect = {c.oracle_id for c in deck if "Aura" in (c.type_line or "")}
        deck_effects = fetch_card_effects(conn, [c.oracle_id for c in deck])
        for card in deck:
            for effect in deck_effects.get(card.oracle_id, []):
                if effect.effect_kind == "whenever_cast_aura":
                    protect.add(card.oracle_id)
                elif effect.effect_kind == "search_library" and _payload_searches_auras(
                    effect.payload
                ):
                    protect.add(card.oracle_id)
        return protect

    def need_more(deck: list[DeckCard]) -> bool:
        return count_aura_spells(deck) < minimum

    def swap_fn(deck: list[DeckCard]) -> tuple[list[DeckCard], str] | None:
        return swap_matching_card(
            conn,
            deck,
            match=lambda c: "Aura" in c.type_line,
            label="Aura",
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
            protect_oracle_ids=_aura_protect_ids(deck),
        )

    def fail_msg(deck: list[DeckCard]) -> str:
        have = count_aura_spells(deck)
        return f"Aura package: could not reach {minimum} Aura spells (have {have})."

    return _run_swap_loop(
        conn,
        cards,
        package_name="Aura package",
        need_more=need_more,
        swap_fn=swap_fn,
        failure_message=fail_msg,
    )


def ensure_enchantment_package(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    scope = build_dependency_scope(criteria)
    effects_map = fetch_card_effects(conn, [c.oracle_id for c in cards])
    if not _should_check_enchantment_support_min(
        scope=scope,
        enchantment_spells=count_enchantment_spells(cards),
        effects_map=effects_map,
        maindeck=cards,
    ):
        return MechanicPackageResult(list(cards), [])

    minimum = enchantment_spell_min()

    def _enchantment_protect_ids(deck: list[DeckCard]) -> set[str]:
        protect = {c.oracle_id for c in deck if "Enchantment" in (c.type_line or "")}
        deck_effects = fetch_card_effects(conn, [c.oracle_id for c in deck])
        for card in deck:
            for effect in deck_effects.get(card.oracle_id, []):
                if effect.effect_kind == "whenever_cast_enchantment":
                    protect.add(card.oracle_id)
                elif effect.effect_kind == "search_library" and _payload_searches_enchantments(
                    effect.payload
                ):
                    protect.add(card.oracle_id)
        return protect

    def need_more(deck: list[DeckCard]) -> bool:
        return count_enchantment_spells(deck) < minimum

    def swap_fn(deck: list[DeckCard]) -> tuple[list[DeckCard], str] | None:
        return swap_matching_card(
            conn,
            deck,
            match=lambda c: "Enchantment" in c.type_line,
            label="enchantment",
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
            protect_oracle_ids=_enchantment_protect_ids(deck),
        )

    def fail_msg(deck: list[DeckCard]) -> str:
        have = count_enchantment_spells(deck)
        return (
            f"Enchantment package: could not reach {minimum} enchantments (have {have})."
        )

    return _run_swap_loop(
        conn,
        cards,
        package_name="Enchantment package",
        need_more=need_more,
        swap_fn=swap_fn,
        failure_message=fail_msg,
    )


def ensure_artifact_package(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    scope = build_dependency_scope(criteria)
    has_payoff = _deck_has_artifact_payoff(conn, cards)
    if not scope.artifacts_user_intent and not has_payoff:
        return MechanicPackageResult(list(cards), [])

    minimum = artifact_spell_min()
    protect_payoffs: set[str] = set()
    if has_payoff:
        effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
        for card in cards:
            for effect in effects.get(card.oracle_id, []):
                if effect.effect_kind == "whenever_cast_type":
                    types = effect.payload.get("types") or []
                    if types == ["artifact"]:
                        protect_payoffs.add(card.oracle_id)

    def need_more(deck: list[DeckCard]) -> bool:
        return count_type_on_maindeck(deck, "artifact") < minimum

    def swap_fn(deck: list[DeckCard]) -> tuple[list[DeckCard], str] | None:
        return swap_matching_card(
            conn,
            deck,
            match=lambda c: "Artifact" in c.type_line,
            label="artifact",
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
            protect_oracle_ids=protect_payoffs,
        )

    def fail_msg(deck: list[DeckCard]) -> str:
        have = count_type_on_maindeck(deck, "artifact")
        return f"Artifact package: could not reach {minimum} artifacts (have {have})."

    return _run_swap_loop(
        conn,
        cards,
        package_name="Artifact package",
        need_more=need_more,
        swap_fn=swap_fn,
        failure_message=fail_msg,
    )



def ensure_vehicle_package(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    scope = build_dependency_scope(criteria)
    has_payoff = _deck_has_vehicle_payoff(conn, cards)
    if not scope.vehicles_user_intent and not has_payoff:
        return MechanicPackageResult(list(cards), [])

    vehicle_min, creature_min = vehicle_profile_floors()
    protect_payoffs = _vehicle_payoff_oracle_ids(conn, cards)

    def need_more(deck: list[DeckCard]) -> bool:
        vehicles = count_vehicles_on_maindeck(deck)
        creatures = count_crew_creatures_on_maindeck(deck)
        if vehicles < vehicle_min:
            return True
        return vehicles > 0 and creatures < creature_min

    def swap_fn(deck: list[DeckCard]) -> tuple[list[DeckCard], str] | None:
        vehicles = count_vehicles_on_maindeck(deck)
        if vehicles < vehicle_min:
            return swap_matching_card(
                conn,
                deck,
                match=lambda c: "Vehicle" in c.type_line,
                label="Vehicle",
                criteria=criteria,
                identity=identity,
                commander_oracle_ids=commander_oracle_ids,
                commander_theme_tags=commander_theme_tags,
                protect_oracle_ids=protect_payoffs,
            )
        return swap_matching_card(
            conn,
            deck,
            match=lambda c: "Creature" in c.type_line and "Vehicle" not in c.type_line,
            label="crew creature",
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
            protect_oracle_ids=protect_payoffs,
        )

    def fail_msg(deck: list[DeckCard]) -> str:
        vehicles = count_vehicles_on_maindeck(deck)
        creatures = count_crew_creatures_on_maindeck(deck)
        return (
            f"Vehicle package: could not reach {vehicle_min} Vehicle(s) and "
            f"{creature_min} crew creatures (have {vehicles} / {creatures})."
        )

    return _run_swap_loop(
        conn,
        cards,
        package_name="Vehicle package",
        need_more=need_more,
        swap_fn=swap_fn,
        failure_message=fail_msg,
    )


def _deck_has_equip_payoff(conn: sqlite3.Connection, cards: list[DeckCard]) -> bool:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == "whenever_equipped":
                return True
    return False


def _equip_payoff_oracle_ids(conn: sqlite3.Connection, cards: list[DeckCard]) -> set[str]:
    effects = fetch_card_effects(conn, [c.oracle_id for c in cards])
    ids: set[str] = set()
    for card in cards:
        for effect in effects.get(card.oracle_id, []):
            if effect.effect_kind == "whenever_equipped":
                ids.add(card.oracle_id)
    return ids


def ensure_equipment_package(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    scope = build_dependency_scope(criteria)
    has_payoff = _deck_has_equip_payoff(conn, cards)
    if not scope.equipment_user_intent and not has_payoff:
        return MechanicPackageResult(list(cards), [])

    equipment_min, carrier_min = equipment_profile_floors()
    protect_payoffs = _equip_payoff_oracle_ids(conn, cards)

    def need_more(deck: list[DeckCard]) -> bool:
        equipment = count_equipment_on_maindeck(deck)
        carriers = count_carrier_creatures_on_maindeck(deck)
        if equipment < equipment_min:
            return True
        return equipment > 0 and carriers < carrier_min

    def swap_fn(deck: list[DeckCard]) -> tuple[list[DeckCard], str] | None:
        equipment = count_equipment_on_maindeck(deck)
        if equipment < equipment_min:
            return swap_matching_card(
                conn,
                deck,
                match=lambda c: "Equipment" in c.type_line,
                label="Equipment",
                criteria=criteria,
                identity=identity,
                commander_oracle_ids=commander_oracle_ids,
                commander_theme_tags=commander_theme_tags,
                protect_oracle_ids=protect_payoffs,
            )
        return swap_matching_card(
            conn,
            deck,
            match=lambda c: "Creature" in c.type_line and "Vehicle" not in c.type_line,
            label="carrier creature",
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
            protect_oracle_ids=protect_payoffs,
        )

    def fail_msg(deck: list[DeckCard]) -> str:
        equipment = count_equipment_on_maindeck(deck)
        carriers = count_carrier_creatures_on_maindeck(deck)
        return (
            f"Equipment package: could not reach {equipment_min} Equipment and "
            f"{carrier_min} carrier creatures (have {equipment} / {carriers})."
        )

    return _run_swap_loop(
        conn,
        cards,
        package_name="Equipment package",
        need_more=need_more,
        swap_fn=swap_fn,
        failure_message=fail_msg,
    )


def ensure_subtype_lord_packages(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    """
    When the deck has a subtype lord (e.g. Elf), ensure enough other creatures of that subtype.

    Runs for any detected lord. ``elves`` mechanic_focus also sets elves_user_intent for
    future scoped rules; lords are always fixed when present.
    """
    lords = _lords_in_deck(conn, cards)
    if not lords:
        return MechanicPackageResult(list(cards), [])

    lord_ids = {lord_id for lord_id, _, _ in lords}
    scope = build_dependency_scope(criteria)
    token_protect: set[str] = set()
    if scope.tokens_user_intent:
        _, token_payoff_ids = _token_role_oracle_ids(conn, cards)
        token_protect = token_payoff_ids
    working = list(cards)
    messages: list[str] = []
    swaps = 0

    for lord_id, lord_name, subtype in lords:
        minimum = subtype_lord_minimum(subtype)

        for _ in range(MAX_REPAIR_SWAPS):
            others = sum(
                1
                for c in working
                if c.oracle_id != lord_id
                and subtype in (c.type_line or "")
                and "Creature" in (c.type_line or "")
            )
            if others >= minimum:
                break

            def match_creature(c) -> bool:
                return subtype in c.type_line and "Creature" in c.type_line

            protect = set(lord_ids) | token_protect
            for card in working:
                if card.oracle_id in protect:
                    continue
                if subtype in (card.type_line or "") and "Creature" in (card.type_line or ""):
                    protect.add(card.oracle_id)

            result = swap_matching_card(
                conn,
                working,
                match=match_creature,
                label=f"other {subtype}",
                criteria=criteria,
                identity=identity,
                commander_oracle_ids=commander_oracle_ids,
                commander_theme_tags=commander_theme_tags,
                protect_oracle_ids=protect,
            )
            if result is None:
                messages.append(
                    f"{subtype} package: could not add support for {lord_name} "
                    f"(have {others} other {subtype}(s); want ≥{minimum})."
                )
                break
            working, msg = result
            messages.append(msg.replace("Dependency repair:", f"{subtype} package:"))
            swaps += 1

    return MechanicPackageResult(working, messages, swaps)


def ensure_included_mechanic_packages(
    conn: sqlite3.Connection,
    cards: list[DeckCard],
    *,
    criteria: DeckCriteria,
    identity: list[str],
    commander_oracle_ids: set[str],
    commander_theme_tags: set[str],
) -> MechanicPackageResult:
    """Run package passes for mechanics the user selected or the deck requires."""
    if not card_effects_enabled(conn):
        return MechanicPackageResult(list(cards), [])

    working = list(cards)
    all_messages: list[str] = []
    total_swaps = 0

    for ensure_fn in (
        ensure_energy_package,
        ensure_resource_counter_packages,
        ensure_sacrifice_package,
        ensure_aura_package,
        ensure_enchantment_package,
        ensure_artifact_package,
        ensure_vehicle_package,
        ensure_equipment_package,
        ensure_subtype_lord_packages,
        ensure_token_package,
    ):
        result = ensure_fn(
            conn,
            working,
            criteria=criteria,
            identity=identity,
            commander_oracle_ids=commander_oracle_ids,
            commander_theme_tags=commander_theme_tags,
        )
        working = result.cards
        all_messages.extend(result.messages)
        total_swaps += result.swaps

    return MechanicPackageResult(working, all_messages, total_swaps)
