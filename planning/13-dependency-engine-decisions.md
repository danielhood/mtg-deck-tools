# Dependency engine — locked decisions (D0)

Resolved before D1 implementation (2026-05-30). Revisit only with evidence from [D0.5 inventory audit](12-dependency-engine-pre-implementation-checklist.md) or dogfood calibration in [09-next-steps.md](09-next-steps.md).

| Decision | Answer | Notes |
| --- | --- | --- |
| Threshold source | `config/dependency-profiles.yaml` | Theme multipliers optional later |
| Tutor matching depth (v1) | Type, subtype, supertypes, `max_cmc` | No “nonbasic land” / named Plains in v1 |
| Commander as tutor target | **Yes** for creature / legendary creature in CI | Document in validator (D2) |
| `strict_dependencies` default | **Off** | Until D2 false-positive review |
| Storage | `card_effects` table + JSON `payload` | No `effect_predicates` table in v1 |
| Include mechanic vs `mechanic_focus` | **Independent** | Wizard include does not auto-set focus |
| Combined themed share cap | **Defer** to UX6 | Use per-profile `share_max` only |
| Face extraction (v1) | **Merged** oracle only, `face_index=0` | See [14-effect-extraction-face-policy.md](14-effect-extraction-face-policy.md) |
| Static card data | Manual bulk refresh | [01-goals-and-scope.md](01-goals-and-scope.md) |

## v1 validator rules (default warn)

| Rule ID | Trigger |
| --- | --- |
| `TUTOR_TARGET_EXISTS` | `search_library` |
| `ENERGY_BALANCE` | `energy_produce` / `energy_consume` |
| `TYPE_SYNERGY_MIN` | `buff_subtype`, `whenever_cast_type` |
| `AURA_SUPPORT_MIN` | `type_line_aura`, aura `search_library` |

**Deferred:** graveyard / delve / escape, `SUBTYPE_SYNERGY_MIN` automation until audit justifies.

## False-positive budget (D2 gate)

Target: **&lt;5%** inappropriate warnings on **20** hand-reviewed generated decks before enabling strict mode or UX6 disables.
