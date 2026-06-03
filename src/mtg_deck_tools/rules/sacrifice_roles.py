"""Sacrifice / aristocrats role counting (shared by validate, packages, scoring)."""

from __future__ import annotations

from typing import Protocol

from mtg_deck_tools.builder.deck import DeckCard


class _EffectLike(Protocol):
    effect_kind: str

EFFECT_KIND_DEATH_RECURSION = "death_recursion"
EFFECT_KIND_SACRIFICE_OPPONENT = "sacrifice_opponent"

# Token makers count toward aristocrats fodder; token payoffs stay on the token axis.
_FODDER_KINDS = frozenset({"sacrifice_fodder", "token_produce"})

# Minimum recursion pieces before treating payoffs as supported without outlets.
_DEATH_RECURSION_OUTLET_THRESHOLD = 2


def card_effect_kinds(effects: list[_EffectLike]) -> set[str]:
    return {e.effect_kind for e in effects}


def card_is_sacrifice_fodder(effects: list[_EffectLike]) -> bool:
    return bool(card_effect_kinds(effects) & _FODDER_KINDS)


def collect_sacrifice_roles(
    effects_map: dict[str, list[_EffectLike]],
    cards: list[DeckCard],
) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    """
    Return (outlets, payoffs, fodder, opponent_sacrifice, death_recursion) as card names.
    Each card appears at most once per list.
    """
    outlets: list[str] = []
    payoffs: list[str] = []
    fodder: list[str] = []
    opponent_sac: list[str] = []
    death_rec: list[str] = []

    for card in cards:
        kinds = card_effect_kinds(effects_map.get(card.oracle_id, []))
        if "sacrifice_outlet" in kinds:
            outlets.append(card.name)
        if "sacrifice_payoff" in kinds:
            payoffs.append(card.name)
        if kinds & _FODDER_KINDS:
            fodder.append(card.name)
        if EFFECT_KIND_SACRIFICE_OPPONENT in kinds:
            opponent_sac.append(card.name)
        if EFFECT_KIND_DEATH_RECURSION in kinds:
            death_rec.append(card.name)

    return outlets, payoffs, fodder, opponent_sac, death_rec


def count_sacrifice_roles(
    effects_map: dict[str, list[_EffectLike]],
    cards: list[DeckCard],
) -> tuple[int, int, int, int, int]:
    """Return (outlets, payoffs, fodder, opponent_sacrifice, death_recursion) counts."""
    o, p, f, opp, dr = collect_sacrifice_roles(effects_map, cards)
    return len(o), len(p), len(f), len(opp), len(dr)


def sacrifice_outlet_support(
    *,
    outlet_count: int,
    opponent_sacrifice_count: int,
    death_recursion_count: int,
) -> int:
    """Effective outlets for balance checks (player-sacrifice + enablers)."""
    return outlet_count + opponent_sacrifice_count + (
        death_recursion_count if death_recursion_count >= _DEATH_RECURSION_OUTLET_THRESHOLD else 0
    )


def sacrifice_roles_balanced(
    *,
    outlet_count: int,
    payoff_count: int,
    opponent_sacrifice_count: int = 0,
    death_recursion_count: int = 0,
) -> bool:
    effective_outlets = sacrifice_outlet_support(
        outlet_count=outlet_count,
        opponent_sacrifice_count=opponent_sacrifice_count,
        death_recursion_count=death_recursion_count,
    )
    if effective_outlets == 0 and payoff_count == 0:
        return True
    return effective_outlets > 0 and payoff_count > 0


def fodder_effect_kinds_for_swap() -> tuple[str, ...]:
    """Prefer real token producers when filling aristocrats fodder."""
    return ("token_produce", "sacrifice_fodder")
