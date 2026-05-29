"""Mechanic tagger tests."""

from pathlib import Path

from mtg_deck_tools.paths import TAXONOMY_PATH
from mtg_deck_tools.tags.tagger import Tagger, load_taxonomy


def test_load_taxonomy():
    tags = load_taxonomy(TAXONOMY_PATH)
    assert len(tags) >= 10
    ids = {t.id for t in tags}
    assert "ramp" in ids
    assert "flying" in ids


def test_tag_flying_keyword():
    tagger = Tagger(load_taxonomy(TAXONOMY_PATH))
    result = tagger.tag_card(
        {
            "oracle_id": "x",
            "type_line": "Creature — Bird",
            "oracle_text": "Flying",
            "keywords": ["Flying"],
        }
    )
    assert any(a.tag == "flying" for a in result)


def test_tag_aristocrats_oracle():
    tagger = Tagger(load_taxonomy(TAXONOMY_PATH))
    result = tagger.tag_card(
        {
            "oracle_id": "x",
            "type_line": "Creature",
            "oracle_text": "Whenever another creature you control dies, draw a card.",
            "keywords": [],
        }
    )
    assert any(a.tag == "aristocrats" for a in result)


def test_tag_vehicle_type():
    tagger = Tagger(load_taxonomy(TAXONOMY_PATH))
    result = tagger.tag_card(
        {
            "oracle_id": "x",
            "type_line": "Artifact — Vehicle",
            "oracle_text": "Crew 3",
            "keywords": [],
        }
    )
    assert any(a.tag == "vehicles" for a in result)
