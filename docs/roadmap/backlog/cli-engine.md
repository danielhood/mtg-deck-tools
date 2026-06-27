# Backlog — CLI engine

Python core: import, builder, dependency engine, analyze. Code: `src/mtg_deck_tools/` (excluding thin CLI/wizard — see [cli-ui.md](cli-ui.md)).

Promote to [active.md](../active.md) before starting. **Index:** [backlog/README.md](README.md). Ship via [dependency-validation.md](../../sdlc/dependency-validation.md).

---

## Priority 7 remainder (optional)

| ID | Item | Notes |
| --- | --- | --- |
| P7-GOLD | Golden cases | Surveil/discover/discard rows in `tests/fixtures/effect_golden.yaml` |
| P7-GY | Broader GY stuffing | “Put target … into your graveyard”, dies-to-GY — case-by-case patterns |
| P7-PKG | Post-fill package | `ensure_*` for `themes: [recursion]` if warn-only insufficient |

**Parallel:** Can run **in parallel with web-ui work** if no overlap with web API refactor; **depends on** fresh `import` before dogfood.

---

## Future candidates

| ID | Item | Notes |
| --- | --- | --- |
| TUTOR-NAMED | Named card tutor matching | `REQUIRES_CARD` — deferred from Priority 2 |
| PROFILE-AUDIT | New profiles from audit evidence | — |
| GY-PKG | Graveyard/landfall post-fill packages | Beyond warn-only rules |

Stances: [`resources/dependency/hard-cases.yaml`](../../../resources/dependency/hard-cases.yaml).

---

## References

| Doc | Role |
| --- | --- |
| [shipped-inventory.md](../../specs/dependency-engine/shipped-inventory.md) | Current atoms, rules, packages |
| [dependency-priorities.md](../../history/dependency-priorities.md) | Shipped Priority 1–8 archive |
| [overview.md](../../specs/dependency-engine/overview.md) | Engine architecture |
