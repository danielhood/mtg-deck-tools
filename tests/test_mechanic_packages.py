"""Included mechanic package enforcement (energy floors)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from mtg_deck_tools.builder.deck import DeckCard
from mtg_deck_tools.builder.mechanic_packages import (
    ensure_energy_package,
    ensure_sacrifice_package,
    ensure_subtype_lord_packages,
    ensure_token_package,
    ensure_vehicle_package,
)
from mtg_deck_tools.db.schema import apply_schema
from mtg_deck_tools.models.criteria import DeckCriteria
from mtg_deck_tools.rules.dependencies import validate_dependencies


def _deck_card(*, oracle_id: str, name: str, type_line: str, slot: str = "flex") -> DeckCard:
    return DeckCard(
        oracle_id=oracle_id,
        name=name,
        slot=slot,
        quantity=1,
        cmc=2.0,
        mana_cost="{2}",
        type_line=type_line,
        price_usd=1.0,
        price_known=True,
        scryfall_uri=None,
        image_uri=None,
    )


def _insert_card(conn: sqlite3.Connection, *, oracle_id: str, name: str, type_line: str) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES (?, ?, ?, '', '{2}', 2, '["G"]', '[]', 1, 0, 0, 1)
        """,
        (oracle_id, name, type_line),
    )


def _insert_effect(
    conn: sqlite3.Connection,
    oracle_id: str,
    effect_kind: str,
    source: str,
) -> None:
    conn.execute(
        """
        INSERT INTO card_effects (
            oracle_id, face_index, effect_kind, payload, confidence, source
        ) VALUES (?, 0, ?, '{}', 1.0, ?)
        """,
        (oracle_id, effect_kind, source),
    )


@pytest.fixture
def energy_pkg_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    for i in range(4):
        _insert_card(conn, oracle_id=f"f{i}", name=f"Filler {i}", type_line="Instant")
    _insert_card(conn, oracle_id="hub", name="Aether Hub", type_line="Land")
    _insert_effect(conn, "hub", "energy_produce", "energy_produce")
    _insert_card(conn, oracle_id="pay1", name="Attune with Aether", type_line="Sorcery")
    _insert_effect(conn, "pay1", "energy_consume", "energy_consume")
    _insert_card(conn, oracle_id="pay2", name="Harnessed Lightning", type_line="Instant")
    _insert_effect(conn, "pay2", "energy_consume", "energy_consume")
    _insert_card(conn, oracle_id="solo", name="Conversion Apparatus", type_line="Artifact")
    _insert_effect(conn, "solo", "energy_consume", "energy_consume")
    conn.commit()
    return conn


def test_ensure_energy_adds_producers_when_only_consumer(energy_pkg_db: sqlite3.Connection) -> None:
    cards = [
        _deck_card(oracle_id="solo", name="Conversion Apparatus", type_line="Artifact"),
        _deck_card(oracle_id="f0", name="Filler 0", type_line="Instant"),
    ]
    criteria = DeckCriteria(include_mechanics=["energy"])
    result = ensure_energy_package(
        energy_pkg_db,
        cards,
        criteria=criteria,
        identity=["G"],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps >= 1
    report = validate_dependencies(
        energy_pkg_db,
        maindeck=result.cards,
        commanders=[],
        criteria=criteria,
    )
    energy_issues = [i for i in report.issues if i.rule_id == "ENERGY_BALANCE"]
    assert not energy_issues


def test_ensure_aura_package(energy_pkg_db: sqlite3.Connection, monkeypatch) -> None:
    from mtg_deck_tools.builder.mechanic_packages import ensure_aura_package

    monkeypatch.setattr(
        "mtg_deck_tools.builder.mechanic_packages.aura_spell_min",
        lambda profiles=None: 2,
    )
    conn = energy_pkg_db
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('aura1', 'Ethereal Armor', 'Enchantment — Aura', '', '{W}', 1, '["G"]', '[]', 1, 0, 0, 1)
        """
    )
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES ('aura2', 'Rancor', 'Enchantment — Aura', '', '{G}', 1, '["G"]', '[]', 1, 0, 0, 1)
        """
    )
    for i in range(6, 12):
        _insert_card(conn, oracle_id=f"aura{i}", name=f"Aura {i}", type_line="Enchantment — Aura")
    conn.commit()

    cards = [
        _deck_card(
            oracle_id="aura1",
            name="Ethereal Armor",
            type_line="Enchantment — Aura",
            slot="synergy",
        ),
        _deck_card(oracle_id="f0", name="Filler 0", type_line="Instant", slot="flex"),
    ]
    criteria = DeckCriteria(themes=["voltron"])
    result = ensure_aura_package(
        conn,
        cards,
        criteria=criteria,
        identity=["G"],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps >= 1
    assert sum(1 for c in result.cards if "Aura" in c.type_line) >= 2


def _insert_card_b(
    conn: sqlite3.Connection, *, oracle_id: str, name: str, type_line: str
) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES (?, ?, ?, '', '{2}', 2, '["B"]', '[]', 1, 0, 0, 1)
        """,
        (oracle_id, name, type_line),
    )


@pytest.fixture
def sacrifice_pkg_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    for i in range(6):
        _insert_card_b(conn, oracle_id=f"f{i}", name=f"Filler {i}", type_line="Instant")
    _insert_card_b(conn, oracle_id="altar", name="Ashnod's Altar", type_line="Artifact")
    _insert_effect(conn, "altar", "sacrifice_outlet", "sacrifice_outlet")
    _insert_card_b(conn, oracle_id="artist", name="Blood Artist", type_line="Creature")
    _insert_effect(conn, "artist", "sacrifice_payoff", "sacrifice_creature_dies_payoff")
    _insert_card_b(conn, oracle_id="nest", name="Nest Invader", type_line="Creature")
    _insert_effect(conn, "nest", "sacrifice_fodder", "sacrifice_fodder_token")
    for i in range(3):
        oid = f"out{i}"
        _insert_card_b(conn, oracle_id=oid, name=f"Outlet {i}", type_line="Artifact")
        _insert_effect(conn, oid, "sacrifice_outlet", "sacrifice_outlet")
    for i in range(4):
        oid = f"pay{i}"
        _insert_card_b(conn, oracle_id=oid, name=f"Payoff {i}", type_line="Creature")
        _insert_effect(conn, oid, "sacrifice_payoff", "sacrifice_creature_dies_payoff")
    for i in range(10):
        oid = f"tok{i}"
        _insert_card_b(conn, oracle_id=oid, name=f"Token {i}", type_line="Creature")
        _insert_effect(conn, oid, "sacrifice_fodder", "sacrifice_fodder_token")
    conn.commit()
    return conn


def test_ensure_sacrifice_adds_payoff_when_only_outlet(
    sacrifice_pkg_db: sqlite3.Connection,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "mtg_deck_tools.builder.mechanic_packages.sacrifice_profile_floors",
        lambda profiles=None: (1, 1, 1),
    )
    cards = [
        _deck_card(oracle_id="altar", name="Ashnod's Altar", type_line="Artifact"),
        _deck_card(oracle_id="f0", name="Filler 0", type_line="Instant"),
    ]
    criteria = DeckCriteria(themes=["aristocrats"])
    result = ensure_sacrifice_package(
        sacrifice_pkg_db,
        cards,
        criteria=criteria,
        identity=["B"],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps >= 1
    report = validate_dependencies(
        sacrifice_pkg_db,
        maindeck=result.cards,
        commanders=[],
        criteria=criteria,
    )
    sacrifice_issues = [i for i in report.issues if i.rule_id == "SACRIFICE_BALANCE"]
    assert not sacrifice_issues


@pytest.fixture
def token_pkg_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    for i in range(6):
        _insert_card(conn, oracle_id=f"f{i}", name=f"Filler {i}", type_line="Instant")
    _insert_card(conn, oracle_id="nest", name="Nest Invader", type_line="Creature")
    _insert_effect(conn, "nest", "token_produce", "token_produce")
    _insert_card(conn, oracle_id="payoff", name="Token Draw", type_line="Creature")
    _insert_effect(conn, "payoff", "token_payoff", "token_payoff_on_create")
    for i in range(5):
        oid = f"prod{i}"
        _insert_card(conn, oracle_id=oid, name=f"Producer {i}", type_line="Creature")
        _insert_effect(conn, oid, "token_produce", "token_produce")
    for i in range(3):
        oid = f"pay{i}"
        _insert_card(conn, oracle_id=oid, name=f"Payoff {i}", type_line="Creature")
        _insert_effect(conn, oid, "token_payoff", "token_payoff_on_create")
    conn.commit()
    return conn


def test_ensure_token_adds_payoff_when_only_producer(
    token_pkg_db: sqlite3.Connection,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "mtg_deck_tools.builder.mechanic_packages.token_profile_floors",
        lambda profiles=None: (1, 1),
    )
    cards = [
        _deck_card(oracle_id="nest", name="Nest Invader", type_line="Creature"),
        _deck_card(oracle_id="f0", name="Filler 0", type_line="Instant"),
    ]
    criteria = DeckCriteria(themes=["tokens"])
    result = ensure_token_package(
        token_pkg_db,
        cards,
        criteria=criteria,
        identity=["G"],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps >= 1
    report = validate_dependencies(
        token_pkg_db,
        maindeck=result.cards,
        commanders=[],
        criteria=criteria,
    )
    token_issues = [i for i in report.issues if i.rule_id == "TOKEN_BALANCE"]
    assert not token_issues


def _insert_card_r(
    conn: sqlite3.Connection, *, oracle_id: str, name: str, type_line: str
) -> None:
    conn.execute(
        """
        INSERT INTO cards (
            oracle_id, name, type_line, oracle_text, mana_cost, cmc, color_identity,
            keywords, commander_legal, commander_eligible, is_basic_land, price_known
        ) VALUES (?, ?, ?, '', '{2}', 2, '["R"]', '[]', 1, 0, 0, 1)
        """,
        (oracle_id, name, type_line),
    )


@pytest.fixture
def goblin_lord_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    for i in range(8):
        _insert_card_r(conn, oracle_id=f"f{i}", name=f"Filler {i}", type_line="Instant")
    _insert_card_r(conn, oracle_id="lord", name="Goblin Warchief", type_line="Creature — Goblin Warrior")
    conn.execute(
        """
        INSERT INTO card_effects (
            oracle_id, face_index, effect_kind, payload, confidence, source
        ) VALUES (?, 0, 'buff_subtype', ?, 1.0, 'buff_subtype_other')
        """,
        ("lord", json.dumps({"subtypes": ["Goblin"]})),
    )
    for i in range(12):
        oid = f"g{i}"
        _insert_card_r(conn, oracle_id=oid, name=f"Goblin {i}", type_line="Creature — Goblin")
    conn.commit()
    return conn


def test_ensure_goblin_lord_adds_support(goblin_lord_db: sqlite3.Connection, monkeypatch) -> None:
    monkeypatch.setattr(
        "mtg_deck_tools.builder.mechanic_packages.subtype_lord_minimum",
        lambda subtype, profiles=None: 3 if subtype == "Goblin" else 5,
    )
    cards = [
        _deck_card(oracle_id="lord", name="Goblin Warchief", type_line="Creature — Goblin Warrior"),
        _deck_card(oracle_id="f0", name="Filler 0", type_line="Instant"),
        _deck_card(oracle_id="f1", name="Filler 1", type_line="Instant"),
        _deck_card(oracle_id="f2", name="Filler 2", type_line="Instant"),
        _deck_card(oracle_id="f3", name="Filler 3", type_line="Instant"),
    ]
    result = ensure_subtype_lord_packages(
        goblin_lord_db,
        cards,
        criteria=DeckCriteria(themes=["tokens"]),
        identity=["R"],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps >= 1
    goblins = sum(
        1
        for c in result.cards
        if "Goblin" in c.type_line and "Creature" in c.type_line and c.oracle_id != "lord"
    )
    assert goblins >= 3


@pytest.fixture
def vehicle_pkg_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    for i in range(6):
        _insert_card(conn, oracle_id=f"f{i}", name=f"Filler {i}", type_line="Instant")
    for i in range(4):
        oid = f"v{i}"
        _insert_card(conn, oracle_id=oid, name=f"Vehicle {i}", type_line="Artifact — Vehicle")
    for i in range(30):
        oid = f"c{i}"
        _insert_card(conn, oracle_id=oid, name=f"Crew {i}", type_line="Creature — Human")
    conn.commit()
    return conn


def test_ensure_vehicle_adds_vehicle_when_intent(
    vehicle_pkg_db: sqlite3.Connection,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "mtg_deck_tools.builder.mechanic_packages.vehicle_profile_floors",
        lambda profiles=None: (2, 5),
    )
    cards = [
        _deck_card(oracle_id="f0", name="Filler 0", type_line="Instant"),
        _deck_card(oracle_id="c0", name="Crew 0", type_line="Creature — Human"),
    ]
    criteria = DeckCriteria(include_mechanics=["vehicles"])
    result = ensure_vehicle_package(
        vehicle_pkg_db,
        cards,
        criteria=criteria,
        identity=["G"],
        commander_oracle_ids=set(),
        commander_theme_tags=set(),
    )
    assert result.swaps >= 1
    vehicles = sum(1 for c in result.cards if "Vehicle" in c.type_line)
    assert vehicles >= 1
