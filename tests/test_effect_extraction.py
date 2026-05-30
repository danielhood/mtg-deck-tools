"""Golden tests for effect extraction (D0)."""

from __future__ import annotations

from pathlib import Path

import yaml

from mtg_deck_tools.effects.extract import EffectExtractor
from mtg_deck_tools.paths import EFFECT_PATTERNS_PATH

FIXTURES = Path(__file__).parent / "fixtures" / "effect_golden.yaml"


def _load_cases() -> list[dict]:
    with FIXTURES.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return list(data.get("cases", []))


def _atom_key(atom) -> tuple:
    return (atom.effect_kind, atom.source, atom.payload)


def _assert_expected(actual, expected_spec: dict) -> None:
    kind = expected_spec["effect_kind"]
    source = expected_spec.get("source")
    payload = expected_spec.get("payload")
    matches = [a for a in actual if a.effect_kind == kind]
    if source:
        matches = [a for a in matches if a.source == source]
    assert matches, f"No atom kind={kind} source={source}; got {[_atom_key(a) for a in actual]}"
    atom = matches[0]
    if source:
        assert atom.source == source
    if payload is not None:
        for key, value in payload.items():
            if value is None:
                continue
            assert atom.payload.get(key) == value, (
                f"payload[{key}] expected {value!r}, got {atom.payload.get(key)!r}"
            )


def test_registry_loads():
    ext = EffectExtractor.from_yaml(EFFECT_PATTERNS_PATH)
    assert len(ext._registry.patterns) >= 10


def test_golden_cases():
    ext = EffectExtractor.from_yaml(EFFECT_PATTERNS_PATH)
    for case in _load_cases():
        atoms = ext.extract(
            oracle_text=case.get("oracle_text") or "",
            type_line=case.get("type_line") or "",
        )
        if "expected" in case:
            expected_list = case["expected"]
            assert len(atoms) == len(expected_list), (
                f"{case['name']}: expected {len(expected_list)} atoms, got {len(atoms)} "
                f"{[_atom_key(a) for a in atoms]}"
            )
            for spec in expected_list:
                _assert_expected(atoms, spec)
        if "expected_min" in case:
            for spec in case["expected_min"]:
                _assert_expected(atoms, spec)
        if "expected" not in case and "expected_min" not in case:
            raise AssertionError(f"Case {case['name']} missing expected/expected_min")


def test_pattern_ids_map_to_documented_kinds():
    ext = EffectExtractor.from_yaml(EFFECT_PATTERNS_PATH)
    for pattern in ext._registry.patterns:
        assert pattern.id
        assert pattern.effect_kind
