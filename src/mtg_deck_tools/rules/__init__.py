"""Commander format rules helpers."""

from mtg_deck_tools.rules.commander import (
    color_identity_subset,
    detect_partner_kind,
    is_commander_eligible,
    is_playable_card,
    parse_color_identity,
)
from mtg_deck_tools.rules.validate import (
    ValidationIssue,
    ValidationResult,
    adjust_slot_template_for_commanders,
    is_valid_partner_pair,
    mainboard_size_for_commanders,
    validate_commander_deck,
    validation_messages,
)

__all__ = [
    "ValidationIssue",
    "ValidationResult",
    "adjust_slot_template_for_commanders",
    "color_identity_subset",
    "detect_partner_kind",
    "is_commander_eligible",
    "is_playable_card",
    "is_valid_partner_pair",
    "mainboard_size_for_commanders",
    "parse_color_identity",
    "validate_commander_deck",
    "validation_messages",
]
