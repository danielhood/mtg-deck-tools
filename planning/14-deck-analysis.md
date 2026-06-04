# Deck analysis and dogfood automation

Repeatable validation and dependency reporting for calibration, regressions, and future enhancements.

## CLI

```bash
# After import (requires cards.db + card_effects)
mtg-deck-tools analyze run

# Custom matrix / output / deck artifacts
mtg-deck-tools analyze run --matrix config/dogfood-matrix.yaml \
  --output-dir output/my-run --write-decks

# CI gate: fail if any scenario violates its expect block
mtg-deck-tools analyze run --fail-on-expect
```

## Matrix format

Default: [`config/dogfood-matrix.yaml`](../config/dogfood-matrix.yaml) (28 scenarios as of 2026-06-03: tribal, artifacts, aristocrats, landfall, enchantress, experience/blood/+1/+1/rad/oil/charge counters, plus budget/strict/repair cases).

**Matrix status (2026-06-03):** `analyze run --fail-on-expect` passes **25/25** scenarios (0% inappropriate warnings) after import against Scryfall oracle bulk and calibration fixes for `blood-yawgmoth` / `elves-lathril`.

Each scenario defines:

| Field | Purpose |
| --- | --- |
| `id` | Stable case name (output file prefix) |
| `commander_names` | **Required for repeatability** — exact Scryfall names in `cards.db` |
| `criteria` | `DeckCriteria` fields (themes, colors, budget, `include_mechanics`, `mechanic_focus`, …) |
| `seed` | RNG seed (inherits matrix `defaults.seed` if omitted) |
| `strict_*` / `repair_dependencies` / `prefer_available` | Same as `generate` flags |
| `expect` | Machine-checkable pass criteria |

### Expect blocks

```yaml
expect:
  validation:
    passed: true
    max_errors: 0
    max_warnings: 3
  dependency:
    max_warnings: 2
    rules_must_warn: [ENERGY_BALANCE]
    rules_must_not_warn: [AURA_SUPPORT_MIN, ENERGY_BALANCE]
    max_inappropriate_warnings: 0
```

## Output layout

```
output/analysis-YYYYMMDD-HHMMSS/
  summary.json          # aggregate metrics + false-positive rate
  summary.md            # human table
  cases/
    <scenario-id>.json  # full case payload
  decks/                # only with --write-decks
    <scenario-id>.deck.json
    <scenario-id>.md
```

## Heuristic rubric

[`analysis/rubric.py`](../src/mtg_deck_tools/analysis/rubric.py) labels each dependency warning:

- **appropriate** — matches user intent or card-driven rule
- **inappropriate** — likely calibration noise (e.g. `AURA_SUPPORT_MIN` on tokens)
- **review** — unknown rule; needs human judgment

False-positive rate in `summary.json`:

```
inappropriate_warnings / total_dependency_warnings
```

Target: **&lt; 5%** on the full matrix ([planning/13](13-dependency-engine-decisions.md)).

## Future: deck composition metrics in analyze output

Not implemented. Planned **UX8** ([07-deck-output-format.md](07-deck-output-format.md), [11-dependency-engine-user-experience.md](11-dependency-engine-user-experience.md)): per-case and aggregate **CMC histograms** (and creature-specific curves) in `cases/<id>.json` and `summary.json` when `--write-decks` is used — useful for spotting regressions in curve shape without manual MD review. Distinct from dependency `expect` blocks (no mandatory curve gate in dogfood matrix until thresholds are calibrated).

## Extending

- Add scenarios to the YAML (no code change).
- For new check types, extend `expect` parsing in `analysis/matrix.py` and `analysis/expectations.py`.
- For new dependency rules and mechanic packages, follow [15-dependency-expansion-roadmap.md](15-dependency-expansion-roadmap.md).
- Programmatic use: `build_generate_outcome()` → inspect `GenerateOutcome` without writing decks.

## CI

`tests/test_analysis.py` runs a **mini matrix** against the in-memory filler fixture DB. Full `dogfood-matrix.yaml` runs locally after `import` (not in default pytest).
