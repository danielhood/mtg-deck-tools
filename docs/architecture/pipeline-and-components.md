# Architecture Options

Three viable architectures for a local Windows tool. All assume **preprocessed oracle data in a local database**.

## Option A — CLI-first monolith (recommended for v1)

```
┌─────────────────────────────────────┐
│  CLI wizard (Python or .NET)        │
│  prompts → DeckCriteria → generator │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  Core library (pure logic)          │
│  filter · tag · score · slots ·     │
│  mana base · validate               │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│  SQLite                             │
│  cards · tags · prices · indices    │
└─────────────────────────────────────┘
```

| Pros | Cons |
| --- | --- |
| Fastest path to working deck output | Less discoverable for casual users |
| Easy to test core logic | Multi-step UX limited by terminal |
| Same core library powers future UI | |

**Best when:** You want to prove slot-filling and tagging before investing in UI.

---

## Option B — Local web app

```
Browser UI  ←→  FastAPI / ASP.NET  ←→  SQLite
     (React/Vue/Svelte or HTMX)
```

| Pros | Cons |
| --- | --- |
| Rich wizard UX (forms, previews, card images) | More moving parts |
| Can show card images from Scryfall URLs | Requires local server process |
| Easy export / share screenshots | |

**Best when:** UX quality matters early and you're comfortable with a small frontend.

---

## Option C — Desktop GUI (native or hybrid)

```
WPF / WinUI / Tauri shell  ←→  Core library  ←→  SQLite
```

| Pros | Cons |
| --- | --- |
| Feels like a Windows app | Highest UI effort |
| No browser tab | Tauri/Electron adds packaging complexity |
| Offline-native | |

**Best when:** You explicitly want a installable `.exe` with native feel in v1.

---

## Recommended phasing

```mermaid
flowchart LR
    P1[Phase 1: Preprocess + DB + tags] --> P2[Phase 2: Core generator CLI]
    P2 --> P3[Phase 3: Wizard UI layer]
    P3 --> P4[Phase 4: Export + polish]
```

1. **Preprocess** — Import JSON → SQLite, run tagger, build indices
2. **CLI vertical slice** — `deck-tools generate --commander "..." --tags aristocrats,tokens`
3. **Interactive wizard** — Add UI (CLI enhanced with questionary/Inquirer, or local web)
4. **Polish** — Export formats, deck stats dashboard, swap suggestions

## Component boundaries

| Module | Responsibility |
| --- | --- |
| `importer` | JSON → normalized rows, layout normalization |
| `tagger` | Apply taxonomy rules → tag table |
| `rules` | Commander legality validation |
| `criteria` | Wizard output model |
| `pool` | Filtered candidate queries |
| `scorer` | Rank cards for a slot |
| `builder` | Slot fill orchestration |
| `manabase` | Land count + color split |
| `export` | Text / CSV / Archidekt-ish format |

Keep **`builder` + `rules` UI-agnostic** so CLI and GUI share the same engine.

## Preprocessing vs. runtime

| Concern | Preprocess | Runtime |
| --- | --- | --- |
| Parse JSON | ✓ | |
| Mechanic tagging | ✓ | |
| Commander eligibility flags | ✓ | |
| Pip extraction | ✓ | |
| User criteria | | ✓ |
| Slot filling | | ✓ |
| Budget tracking | | ✓ |
| Validation | | ✓ |

Preprocessing runs when oracle bulk updates (~minutes once). Runtime deck build should complete in **< 2 seconds** on typical hardware.

## Alternative: embedded search engine

Instead of hand-rolled SQL filters, index cards in **SQLite FTS5** on `oracle_text` + `name` for theme search, while structured filters stay as columns.

Hybrid query example:

```sql
SELECT c.* FROM cards c
JOIN card_mechanic_tags t ON t.oracle_id = c.oracle_id
WHERE t.tag IN ('aristocrats')
  AND c.cmc <= 4
  AND c.color_identity <= ?
ORDER BY synergy_score DESC
LIMIT 50;
```

FTS is optional for v1 if curated tags cover user-facing mechanics.
