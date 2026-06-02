"""Profile threshold helpers."""

from mtg_deck_tools.rules.dependency_profiles import subtype_lord_minimum, vehicle_profile_floors


def test_subtype_lord_minimum_uses_per_subtype_map() -> None:
    profiles = {
        "subtype_lords": {
            "payoff_creature_min": 5,
            "subtype_minimums": {"Elf": 5, "Goblin": 8, "Vampire": 6},
        }
    }
    assert subtype_lord_minimum("Goblin", profiles) == 8
    assert subtype_lord_minimum("Vampire", profiles) == 6
    assert subtype_lord_minimum("Knight", profiles) == 5
