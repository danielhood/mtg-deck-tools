"""Card effect extraction for the dependency engine."""

from mtg_deck_tools.effects.extract import EffectExtractor, extract_card_effects
from mtg_deck_tools.effects.patterns import EffectPattern, load_effect_patterns

__all__ = [
    "EffectExtractor",
    "EffectPattern",
    "extract_card_effects",
    "load_effect_patterns",
]
