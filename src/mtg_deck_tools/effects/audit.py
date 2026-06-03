"""Inventory audit over cards.db for dependency planning (D0.5)."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mtg_deck_tools.effects.extract import EffectExtractor
from mtg_deck_tools.models.effects import EffectAtom
from mtg_deck_tools.paths import DEPENDENCY_RESOURCES_DIR

SEARCH_ORACLE_HINT = "search your library"


@dataclass
class AuditCardRow:
    oracle_id: str
    name: str
    color_identity: list[str]
    type_line: str
    oracle_text: str
    atoms: list[EffectAtom] = field(default_factory=list)


def _ci_key(color_identity: list[str]) -> str:
    order = "WUBRG"
    return "".join(c for c in order if c in color_identity) or "C"


def _payload_key(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)


def _fetch_legal_cards(conn: sqlite3.Connection) -> list[AuditCardRow]:
    rows = conn.execute(
        """
        SELECT oracle_id, name, color_identity, type_line, oracle_text
        FROM cards
        WHERE commander_legal = 1
        ORDER BY name
        """
    ).fetchall()
    result: list[AuditCardRow] = []
    for row in rows:
        ci = json.loads(row["color_identity"] or "[]")
        result.append(
            AuditCardRow(
                oracle_id=row["oracle_id"],
                name=row["name"],
                color_identity=ci,
                type_line=row["type_line"] or "",
                oracle_text=row["oracle_text"] or "",
            )
        )
    return result


def _profile_counts(card: AuditCardRow) -> dict[str, dict[str, int]]:
    """Map atoms to dependency profile role counters."""
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for atom in card.atoms:
        kind = atom.effect_kind
        if kind == "energy_produce":
            counts["energy"]["producer"] += 1
        elif kind == "energy_consume":
            counts["energy"]["consumer"] += 1
        elif kind == "experience_produce":
            counts["experience"]["producer"] += 1
        elif kind == "experience_consume":
            counts["experience"]["consumer"] += 1
        elif kind == "blood_produce":
            counts["blood"]["producer"] += 1
        elif kind == "blood_consume":
            counts["blood"]["consumer"] += 1
        elif kind == "plus_one_produce":
            counts["plus_one"]["producer"] += 1
        elif kind == "plus_one_consume":
            counts["plus_one"]["consumer"] += 1
        elif kind == "rad_produce":
            counts["rad"]["producer"] += 1
        elif kind == "rad_consume":
            counts["rad"]["consumer"] += 1
        elif kind == "oil_produce":
            counts["oil"]["producer"] += 1
        elif kind == "oil_consume":
            counts["oil"]["consumer"] += 1
        elif kind == "charge_produce":
            counts["charge"]["producer"] += 1
        elif kind == "charge_consume":
            counts["charge"]["consumer"] += 1
        elif kind == "type_line_aura":
            counts["aura_support"]["aura_spell"] += 1
        elif kind == "search_library":
            payload = atom.payload
            if payload.get("subtypes") == ["Aura"] or (
                payload.get("types") == ["enchantment"]
                and payload.get("subtypes") == ["Aura"]
            ):
                counts["aura_support"]["aura_tutor"] += 1
            elif "enchantment" in [t.lower() for t in (payload.get("types") or [])]:
                if payload.get("subtypes") != ["Aura"]:
                    counts["enchantments"]["enchantment_tutor"] += 1
        elif kind == "buff_subtype":
            subtypes = atom.payload.get("subtypes") or []
            if subtypes == ["Elf"]:
                counts["elves"]["payoff"] += 1
                counts["elves"]["creature"] += 1
        elif kind == "whenever_cast_type":
            types = atom.payload.get("types") or []
            if types == ["artifact"]:
                counts["artifacts"]["payoff"] += 1
        elif kind == "whenever_cast_enchantment":
            counts["enchantments"]["payoff"] += 1
    if "Elf" in card.type_line:
        counts["elves"]["creature"] += 1
    if "Enchantment" in card.type_line:
        counts["enchantments"]["enchantment_spell"] += 1
    return {k: dict(v) for k, v in counts.items()}


def run_dependency_audit(
    conn: sqlite3.Connection,
    *,
    extractor: EffectExtractor | None = None,
    review_sample_size: int = 40,
) -> dict[str, Any]:
    """Scan commander-legal cards and aggregate dependency extraction stats."""
    ext = extractor or EffectExtractor.from_yaml()
    cards = _fetch_legal_cards(conn)

    pattern_hits: Counter[str] = Counter()
    pattern_examples: dict[str, list[str]] = defaultdict(list)
    effect_kind_hits: Counter[str] = Counter()
    tutor_predicates: Counter[str] = Counter()
    tutor_examples: dict[str, list[str]] = defaultdict(list)

    profile_totals: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    profile_by_ci: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )

    review_queue: list[dict[str, Any]] = []
    low_confidence: list[dict[str, Any]] = []

    energy_tagged = {
        row[0]
        for row in conn.execute(
            "SELECT oracle_id FROM card_mechanic_tags WHERE tag = 'energy'"
        ).fetchall()
    }
    energy_producers_tagged = 0
    energy_consumers_tagged = 0
    energy_producers_untagged = 0
    energy_consumers_untagged = 0

    for card in cards:
        card.atoms = ext.extract(
            oracle_text=card.oracle_text,
            type_line=card.type_line,
        )
        has_produce = False
        has_consume = False
        for atom in card.atoms:
            if atom.effect_kind == "energy_produce":
                has_produce = True
            if atom.effect_kind == "energy_consume":
                has_consume = True
            effect_kind_hits[atom.effect_kind] += 1
            pattern_hits[atom.source] += 1
            if len(pattern_examples[atom.source]) < 5:
                pattern_examples[atom.source].append(card.name)

            if atom.effect_kind == "search_library":
                key = _payload_key(atom.payload)
                tutor_predicates[key] += 1
                if len(tutor_examples[key]) < 5:
                    tutor_examples[key].append(card.name)

            if atom.confidence < 0.7:
                low_confidence.append(
                    {
                        "name": card.name,
                        "source": atom.source,
                        "confidence": atom.confidence,
                        "effect_kind": atom.effect_kind,
                    }
                )

        if SEARCH_ORACLE_HINT.lower() in card.oracle_text.lower():
            if not any(a.effect_kind == "search_library" for a in card.atoms):
                review_queue.append(
                    {
                        "name": card.name,
                        "reason": "oracle_has_search_no_atom",
                        "oracle_excerpt": card.oracle_text[:200],
                    }
                )

        for profile, roles in _profile_counts(card).items():
            for role, n in roles.items():
                profile_totals[profile][role] += n
                ci = _ci_key(card.color_identity)
                profile_by_ci[ci][profile][role] += n

        tagged_energy = card.oracle_id in energy_tagged
        if has_produce:
            if tagged_energy:
                energy_producers_tagged += 1
            else:
                energy_producers_untagged += 1
        if has_consume:
            if tagged_energy:
                energy_consumers_tagged += 1
            else:
                energy_consumers_untagged += 1

    energy_tag_gap = {
        "cards_with_energy_tag": len(energy_tagged),
        "producers_tagged": energy_producers_tagged,
        "consumers_tagged": energy_consumers_tagged,
        "producers_untagged": energy_producers_untagged,
        "consumers_untagged": energy_consumers_untagged,
    }

    generated_at = datetime.now(UTC).isoformat()
    meta = {
        row["key"]: row["value"]
        for row in conn.execute("SELECT key, value FROM import_metadata").fetchall()
    }

    return {
        "generated_at": generated_at,
        "extraction_version": ext._registry.extraction_version,
        "schema_version": ext._registry.schema_version,
        "commander_legal_cards": len(cards),
        "import_metadata": meta,
        "pattern_hits": {
            "by_source": dict(pattern_hits.most_common()),
            "examples": dict(pattern_examples),
        },
        "effect_kind_hits": dict(effect_kind_hits.most_common()),
        "tutor_predicates": {
            "counts": [
                {"payload": json.loads(k), "count": v, "examples": tutor_examples.get(k, [])}
                for k, v in tutor_predicates.most_common()
            ],
        },
        "profile_summary": {
            "global": {p: dict(r) for p, r in profile_totals.items()},
            "by_color_identity": {
                ci: {p: dict(r) for p, r in profiles.items()}
                for ci, profiles in sorted(profile_by_ci.items())
            },
        },
        "energy_tag_gap": energy_tag_gap,
        "review_queue": {
            "unmatched_search_oracle": review_queue[:review_sample_size],
            "unmatched_search_total": len(review_queue),
            "low_confidence_atoms": low_confidence[:review_sample_size],
            "low_confidence_total": len(low_confidence),
        },
    }


def write_audit_reports(
    audit: dict[str, Any],
    output_dir: Path,
) -> dict[str, Path]:
    """Write JSON and CSV audit artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    pattern_path = output_dir / "dependency-pattern-hits.json"
    pattern_path.write_text(
        json.dumps(
            {
                "generated_at": audit["generated_at"],
                "commander_legal_cards": audit["commander_legal_cards"],
                "pattern_hits": audit["pattern_hits"],
                "effect_kind_hits": audit["effect_kind_hits"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    written["pattern_hits"] = pattern_path

    profile_path = output_dir / "dependency-profile-summary.json"
    profile_path.write_text(
        json.dumps(
            {
                "generated_at": audit["generated_at"],
                "profile_summary": audit["profile_summary"],
                "energy_tag_gap": audit["energy_tag_gap"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    written["profile_summary"] = profile_path

    tutor_path = output_dir / "tutor-predicates.csv"
    with tutor_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["count", "payload_json", "example_cards"])
        for row in audit["tutor_predicates"]["counts"]:
            writer.writerow(
                [
                    row["count"],
                    json.dumps(row["payload"], sort_keys=True),
                    "; ".join(row["examples"]),
                ]
            )
    written["tutor_predicates"] = tutor_path

    review_path = output_dir / "dependency-review-queue.json"
    review_path.write_text(json.dumps(audit["review_queue"], indent=2), encoding="utf-8")
    written["review_queue"] = review_path

    summary_path = output_dir / "dependency-audit-summary.json"
    summary_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    written["summary"] = summary_path

    return written


def run_audit_to_disk(
    db_path: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    from mtg_deck_tools.db.connection import connect

    out = output_dir or (DEPENDENCY_RESOURCES_DIR / "reports")
    conn = connect(db_path)
    try:
        audit = run_dependency_audit(conn)
        paths = write_audit_reports(audit, out)
        audit["report_paths"] = {k: str(v) for k, v in paths.items()}
        return audit
    finally:
        conn.close()
