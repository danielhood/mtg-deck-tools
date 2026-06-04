# Active roadmap

Status as of 2026-06-04. **v1 and dependency engine D0–D5 are complete.** Shipped capability inventory lives in [history/milestones.md](../history/milestones.md); dependency-specific inventory in [roadmap/dependency-expansion.md](dependency-expansion.md).

## Suggested next task

**UX7** — local web / desktop UI ([user-experience.md](../specs/dependency-engine/user-experience.md)). CLI wizard UX2–UX5 are complete. Optional: **UX10** CMC metrics in deck output.

**Dependency (optional):** [dependency-expansion.md](dependency-expansion.md) **Priority 7 remainder** only — core surveil/discover/discard is shipped.

**Regression gate:** `mtg-deck-tools analyze run --fail-on-expect` — **30/30** ([deck-analysis.md](../specs/deck-analysis.md), [`config/dogfood-matrix.yaml`](../../config/dogfood-matrix.yaml)).

## Open work

| Area | Status | Notes |
| --- | --- | --- |
| UX7 local web / desktop UI | **Next** | Reuse Python core; dependency dashboard, UX10 metrics, UX11 editor |
| UX8 progressive wizard constraints | Backlog | Parked — see UX spec § Progressive constraints |
| UX10 deck composition metrics | Backlog | CMC distribution in MD/JSON; charts in UX7 |
| UX11 GUI deck editor (swap / lock) | Backlog | Pinned cards survive refill/regen |
| Dependency swap packages CLI | Backlog | `generate --swap-profile` — needs UX7 or CLI design |
| Priority 7 remainder (dependency) | Optional | Non-core items in dependency-expansion doc |
| Threshold tuning vs audit | Ongoing | When adding profiles — see dependency-expansion checklist |

## Product backlog

| Topic | Doc |
| --- | --- |
| Power level / salt | [open-questions.md](../product/open-questions.md) |
| Moxfield / Archidekt export | [deck-output-format.md](../product/deck-output-format.md) |
| Related token companion list | [deck-output-format.md](../product/deck-output-format.md) § Related token cards |
| Image gallery / diff on `.deck.json` | [deck-output-format.md](../product/deck-output-format.md) |
| Parquet / faster import | [technology-stack.md](../architecture/technology-stack.md) |
| DFC / adventure normalization | [problem-decomposition.md](../architecture/problem-decomposition.md) |
| Post-validation CR repair | Deferred — fill-time filters sufficient today |

## Maintainer workflow

After Scryfall bulk refresh: `import` → optional `dependency-audit` → `analyze run --fail-on-expect`.

When shipping a feature, update docs per [DOC-MAP.md](../DOC-MAP.md) (do not duplicate ship lists here — use [changelog.md](../history/changelog.md) and dependency-expansion strike-throughs).

## References

| Doc | Role |
| --- | --- |
| [dependency-expansion.md](dependency-expansion.md) | Dependency priority grid + shipped inventory |
| [user-experience.md](../specs/dependency-engine/user-experience.md) | UX7+ planned behavior |
| [changelog.md](../history/changelog.md) | Recent ships (append-only) |
| [milestones.md](../history/milestones.md) | Major milestone history |
