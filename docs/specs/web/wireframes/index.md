# Wireframe index

Route → HTML mock map. UX7c wireframes **approved 2026-06-07** (shipped). UX7e/UX7f wireframes are **reference** — implementation shipped; status `shipped` means layout reference only.

| Route | File | Status | Notes |
| --- | --- | --- | --- |
| `/` (DB ready) | [home.html](home.html) | approved | App shell, hero, primary CTA enabled |
| `/` (DB missing) | [home-db-missing.html](home-db-missing.html) | approved | DB gate banner, Build disabled |
| `/build/1` | [build-step-01-themes.html](build-step-01-themes.html) | approved | Theme chips, default slot template, Next/Back |
| `/build/2` | [build-step-02-mechanics.html](build-step-02-mechanics.html) | approved | Triage: keyword · avoid · include; ghost zone icons |
| `/build/3` | [build-step-03-synergy.html](build-step-03-synergy.html) | approved | Synergy toggles; focus stepper + dot meter; collapsed level help |
| `/build/3` (no profiles) | [build-step-03-synergy-empty.html](build-step-03-synergy-empty.html) | approved | Toggles only; dashed empty state for mechanic focus |
| `/build/4` | [build-step-04-colors.html](build-step-04-colors.html) | approved | WUBRG pips + Colorless (void); engine design note |
| `/build/5` | [build-step-05-budget.html](build-step-05-budget.html) | approved | Steppers + manual $ fields; independent min/max; range warning only |
| `/build/6` | [build-step-06-commander.html](build-step-06-commander.html) | approved | Search-as-you-type; includes/exact; highlighted row + tappable card art lightbox |
| `/build/6` (no results) | [build-step-06-commander-empty.html](build-step-06-commander-empty.html) | approved | Dashed empty state; links back to steps 4–5; Next disabled |
| `/build/7` | [build-step-07-rarity.html](build-step-07-rarity.html) | approved | Min rarity radio list (common → mythic); commander exempt |
| `/build/review` | [build-review.html](build-review.html) | approved | Preflight warnings panel + criteria recap; Back / Generate |
| `/build/review` (clean) | [build-review-clean.html](build-review-clean.html) | approved | Empty preflight success state |
| `/build/result` | [build-result.html](build-result.html) | approved | MD HTML preview shell; **UX7e:** becomes redirect — keep for compat reference |
| `/deck/:id` | [deck-view.html](deck-view.html) | shipped | Library + Home footer; JSON render |
| `/deck/:id` (from home) | [deck-view-from-home.html](deck-view-from-home.html) | shipped | Entry from home **View last deck** |
| `/deck/:id` (post-generate) | [deck-view-from-generate.html](deck-view-from-generate.html) | shipped | Entry after wizard generate |
| `/deck/:id` (warnings) | [deck-view-warnings.html](deck-view-warnings.html) | shipped | Expanded summary + dependency warn analysis |
| `/deck/:id` (delete) | [deck-view-delete.html](deck-view-delete.html) | shipped | Delete confirm modal |
| `/` (resume deck) | [home-resume-deck.html](home-resume-deck.html) | shipped | Secondary **View last deck** CTA |
| `/` (library ready) | [home-library-ready.html](home-library-ready.html) | shipped | **View last deck** + **Saved library** |
| `/library` | [library.html](library.html) | shipped | Tappable card grid, search, sort |
| `/library` (empty) | [library-empty.html](library-empty.html) | shipped | Empty state + **Build new deck** CTA |
| `/deck/:id` (rename) | [deck-view-rename.html](deck-view-rename.html) | shipped | Rename modal |

Process: [README.md](README.md).
