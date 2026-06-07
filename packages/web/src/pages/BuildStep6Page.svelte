<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import WizardIntro from "../components/WizardIntro.svelte";
  import SectionHeader from "../components/SectionHeader.svelte";
  import { searchCommanders, type CommanderResult, type WizardMeta } from "../lib/api";
  import {
    commanderSearchColors,
    loadDraft,
    saveDraft,
    toDeckCriteria,
    type WizardDraft,
  } from "../lib/criteria";
  import { formatColorListLabel, formatPrice, pipMiniClass, sortColors } from "../lib/format";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());
  let query = $state("");
  let results = $state<CommanderResult[]>([]);
  let selected = $state<CommanderResult | null>(null);
  let showArt = $state(false);

  $effect(() => {
    saveDraft(draft);
  });

  $effect(() => {
    if (!meta.db_ready) return;
    const { colors, color_match } = commanderSearchColors(draft);
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    for (const color of colors) params.append("colors", color);
    params.set("color_match", color_match);
    const criteria = toDeckCriteria(draft);
    if (criteria.budget_usd != null) params.set("budget_usd", String(criteria.budget_usd));
    if (criteria.card_price_min_usd != null) {
      params.set("card_price_min_usd", String(criteria.card_price_min_usd));
    }
    if (criteria.card_price_max_usd != null) {
      params.set("card_price_max_usd", String(criteria.card_price_max_usd));
    }
    if (criteria.strict_budget) params.set("strict_budget", "true");

    const timer = setTimeout(() => {
      searchCommanders(params)
        .then((rows) => {
          results = rows;
          if (draft.commander_oracle_ids[0]) {
            selected =
              rows.find((row) => row.oracle_id === draft.commander_oracle_ids[0]) ?? selected;
          }
        })
        .catch(() => {
          results = [];
        });
    }, 200);
    return () => clearTimeout(timer);
  });

  function pickCommander(row: CommanderResult): void {
    selected = row;
    draft = {
      ...draft,
      commander_oracle_ids: [row.oracle_id],
      commander_label: row.name,
    };
  }

  const nextDisabled = $derived(!draft.commander_oracle_ids.length);

  const filterPips = $derived.by(() => {
    if (draft.colorFilter === "colorless") return { kind: "colorless" as const, colors: [] as string[] };
    if (draft.colorFilter === "any" || !draft.colors.length) return { kind: "any" as const, colors: [] as string[] };
    return { kind: "selected" as const, colors: sortColors(draft.colors) };
  });

  const filterCopy = $derived.by(() => {
    if (filterPips.kind === "colorless") return "Colorless only";
    if (filterPips.kind === "any") return "Any (no color filter)";
    const label = formatColorListLabel(filterPips.colors);
    return draft.colorMatch === "exact" ? `${label} only` : `${label} plus others`;
  });
</script>

<WizardChrome
  step={6}
  backRoute="/build/5"
  nextRoute="/build/7"
  dbReady={meta.db_ready}
  nextDisabled={nextDisabled}
>
  <WizardIntro title="Commander selection" lead="Search for and select your commander." />

  <section class="wizard-section" aria-labelledby="color-match-heading">
    <SectionHeader
      id="color-match-heading"
      title="Color filter"
      description="How commander identity should match your color picks."
    />

    <div class="segmented-control" role="radiogroup" aria-label="Commander color filter mode">
      <label class="segment-option">
        <input
          type="radio"
          name="color_match"
          value="includes"
          checked={draft.colorMatch === "includes"}
          onchange={() => (draft = { ...draft, colorMatch: "includes" })}
        />
        <span class="segment-label">
          <strong>Includes</strong>
          <span>Has your colors (may include more)</span>
        </span>
      </label>
      <label class="segment-option">
        <input
          type="radio"
          name="color_match"
          value="exact"
          checked={draft.colorMatch === "exact"}
          onchange={() => (draft = { ...draft, colorMatch: "exact" })}
        />
        <span class="segment-label">
          <strong>Exact</strong>
          <span>Only the colors you selected</span>
        </span>
      </label>
    </div>

    <div class="filter-context" aria-live="polite">
      <div class="pip-row" aria-label="Selected colors">
        {#if filterPips.kind === "selected"}
          {#each filterPips.colors as color (color)}
            <span class="mana-pip-mini {pipMiniClass(color)}">{color}</span>
          {/each}
        {:else if filterPips.kind === "colorless"}
          <span class="mana-pip-mini pip-colorless" aria-hidden="true">∅</span>
        {:else}
          <span class="mana-pip-mini pip-any" aria-hidden="true">∅</span>
        {/if}
      </div>
      <span class="filter-context-copy">{filterCopy}</span>
    </div>
  </section>

  <section class="wizard-section" aria-labelledby="search-heading">
    <SectionHeader id="search-heading" title="Search commanders" description="Type to filter by name." />

    <div class="search-wrap">
      <div class="search-field">
        <span class="search-icon" aria-hidden="true">⌕</span>
        <input
          class="search-input"
          type="search"
          placeholder="Search commander name…"
          bind:value={query}
          aria-label="Search commander name"
        />
      </div>
    </div>

    <div class="commander-results" role="listbox" aria-label="Commander results">
      {#each results as row (row.oracle_id)}
        <button
          type="button"
          class="commander-row"
          class:is-selected={draft.commander_oracle_ids[0] === row.oracle_id}
          onclick={() => pickCommander(row)}
        >
          <strong>{row.name}</strong>
          <span>
            {(row.color_identity.join("") || "C")} · {formatPrice(row.price_known ? row.price_usd : null)}
          </span>
        </button>
      {:else}
        <div class="empty-panel">No commanders match. Try different colors or search text.</div>
      {/each}
    </div>

    {#if selected?.image_uri}
      <button type="button" class="art-preview" onclick={() => (showArt = true)}>
        <img src={selected.image_uri} alt={`Art for ${selected.name}`} />
      </button>
    {/if}
  </section>
</WizardChrome>

{#if showArt && selected?.image_uri}
  <div class="lightbox" role="dialog" aria-modal="true">
    <button type="button" class="lightbox-backdrop" aria-label="Close" onclick={() => (showArt = false)}></button>
    <div class="lightbox-panel">
      <button type="button" class="lightbox-close" onclick={() => (showArt = false)}>×</button>
      <img src={selected.image_uri} alt={selected.name} />
      <p class="lightbox-title">{selected.name}</p>
    </div>
  </div>
{/if}

<style>
  .art-preview {
    border: none;
    background: none;
    padding: 0;
    cursor: pointer;
    width: 100%;
  }

  .art-preview img {
    width: 100%;
    max-width: 220px;
    border-radius: 10px;
    display: block;
    margin: 0 auto;
  }

  .lightbox {
    position: fixed;
    inset: 0;
    z-index: 30;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px 16px;
  }

  .lightbox-backdrop {
    position: absolute;
    inset: 0;
    border: none;
    background: rgba(15, 23, 42, 0.72);
    cursor: pointer;
  }

  .lightbox-panel {
    position: relative;
    z-index: 1;
    width: min(100%, 300px);
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .lightbox-close {
    align-self: flex-end;
    width: 36px;
    height: 36px;
    border: none;
    border-radius: 999px;
    background: var(--bg);
    font-size: 22px;
    cursor: pointer;
  }

  .lightbox-panel img {
    width: 100%;
    border-radius: 12px;
  }

  .lightbox-title {
    text-align: center;
    color: #fff;
    font-size: 14px;
    font-weight: 700;
  }
</style>
