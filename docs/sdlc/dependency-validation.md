# Dependency expansion — validation and ship workflow

SDLC for shipping new dependency profiles, rules, and patterns. **Phases:** [agent-phases.md](agent-phases.md). **Spec:** [shipped-inventory.md](../specs/dependency-engine/shipped-inventory.md). **Runner:** [deck-analysis.md](../specs/deck-analysis.md). **Active register:** [active.md](../roadmap/active.md).

---

## Dogfood regression gate

| Artifact | Purpose |
| --- | --- |
| [`config/dogfood-matrix.yaml`](../../config/dogfood-matrix.yaml) | Scenario matrix |
| `mtg-deck-tools analyze run --fail-on-expect` | Gate after import |
| `analysis/rubric.py` | Inappropriate-warning target &lt; 5% |

**Current:** **30/30**. After bulk refresh: `import` → optional `dependency-audit` → analyze.

---

## Implementation checklist (per PR)

1. Patterns → import → profile → scope → validate → build → rubric → dogfood → tests
2. Docs per [DOC-MAP.md](../DOC-MAP.md)

---

## Doc updates when shipping

| Step | File | Action |
| --- | --- | --- |
| 1 | `docs/specs/dependency-engine/shipped-inventory.md` | Inventory tables |
| 2 | `docs/history/changelog.md` | Dated bullet |
| 3 | `docs/roadmap/active.md` | Remove task row (cli-engine) |
| 4 | `docs/history/dependency-priorities.md` | Strike through only if in Priority 1–8 archive |
| 5 | `README.md` | User-facing mechanic if applicable |

Promote from [backlog/cli-engine.md](../roadmap/backlog/cli-engine.md) → [active.md](../roadmap/active.md) before implementation.
