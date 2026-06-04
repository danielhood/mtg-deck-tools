# Dependency engine — locked decisions (D0)

Resolved before D1 implementation (2026-05-30). Revisit only with evidence from [D0.5 inventory audit](implementation-checklist.md) or dogfood calibration in [active.md](../../roadmap/active.md).

| Decision | Answer | Notes |
| --- | --- | --- |
| Threshold source | `config/dependency-profiles.yaml` | Theme multipliers optional later |
| Tutor matching depth (v1) | Type (OR when multi-type), subtype, supertypes, `min_cmc` / `max_cmc`, `colors` | Named card search (`REQUIRES_CARD`) still deferred |
| Commander as tutor target | **Yes** for creature / legendary creature in CI | Document in validator (D2) |
| `strict_dependencies` default | **Off** | Until D2 false-positive review |
| Storage | `card_effects` table + JSON `payload` | No `effect_predicates` table in v1 |
| Include mechanic vs `mechanic_focus` | **Independent** | Wizard include does not auto-set focus |
| Combined themed share cap | **Defer** to UX8 | Use per-profile `share_max` only |
| Face extraction (v1) | **Merged** oracle only, `face_index=0` | See [effect-extraction-policy.md](effect-extraction-policy.md) |
| Static card data | Manual bulk refresh | [goals-and-scope.md](../../product/goals-and-scope.md) |

## v1 validator rules (default warn)

| Rule ID | Trigger |
| --- | --- |
| `TUTOR_TARGET_EXISTS` | `search_library` |
| `ENERGY_BALANCE` | `energy_produce` / `energy_consume` |
| `TYPE_SYNERGY_MIN` | `buff_subtype`, `whenever_cast_type` |
| `AURA_SUPPORT_MIN` | `type_line_aura`, aura `search_library` |

**Deferred:** ~~graveyard / delve / escape~~ (shipped 2026-06 as warn-only heuristics), `SUBTYPE_SYNERGY_MIN` automation until audit justifies.

## False-positive budget (D2 gate)

Target: **&lt;5%** inappropriate warnings on **20** hand-reviewed generated decks before enabling strict mode or UX8 disables.
