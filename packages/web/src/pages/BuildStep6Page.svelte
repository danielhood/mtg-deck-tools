<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import { searchCommanders, type CommanderResult, type WizardMeta } from "../lib/api";
  import {
    commanderSearchColors,
    loadDraft,
    saveDraft,
    toDeckCriteria,
    type WizardDraft,
  } from "../lib/criteria";
  import { formatPrice } from "../lib/format";

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
            selected = rows.find((row) => row.oracle_id === draft.commander_oracle_ids[0]) ?? selected;
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
    draft = { ...draft, commander_oracle_ids: [row.oracle_id] };
  }

  const nextDisabled = $derived(!draft.commander_oracle_ids.length);
</script>

<WizardChrome
  step={6}
  backRoute="/build/5"
  nextRoute="/build/7"
  dbReady={meta.db_ready}
  nextDisabled={nextDisabled}
>
  <h2 class="section-title">Commander</h2>
  <p class="section-lead">Search and pick a commander. Required before continuing.</p>

  <div class="toggle-row">
    <label for="color-match">Exact color identity match</label>
    <input
      id="color-match"
      type="checkbox"
      checked={draft.colorMatch === "exact"}
      onchange={(e) =>
        (draft = { ...draft, colorMatch: e.currentTarget.checked ? "exact" : "includes" })}
    />
  </div>

  <input
    class="search-input"
    type="search"
    placeholder="Search commanders"
    bind:value={query}
    aria-label="Commander search"
  />

  <div class="result-list" role="listbox" aria-label="Commander results">
    {#each results as row (row.oracle_id)}
      <button
        type="button"
        class="result-row"
        class:selected={draft.commander_oracle_ids[0] === row.oracle_id}
        onclick={() => pickCommander(row)}
      >
        <span class="name">{row.name}</span>
        <span class="meta">
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
</WizardChrome>

{#if showArt && selected?.image_uri}
  <div class="lightbox" role="dialog" aria-modal="true" onclick={() => (showArt = false)}>
    <button type="button" class="close" onclick={() => (showArt = false)}>Close</button>
    <img src={selected.image_uri} alt={selected.name} />
  </div>
{/if}

<style>
  .search-input {
    width: 100%;
    min-height: 44px;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0 12px;
  }

  .result-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .result-row {
    text-align: left;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--bg);
    cursor: pointer;
  }

  .result-row.selected {
    border-color: var(--blue-700);
    background: var(--blue-100);
  }

  .name {
    display: block;
    font-size: 13px;
    font-weight: 600;
  }

  .meta {
    font-size: 11px;
    color: var(--text-muted);
  }

  .empty-panel {
    padding: 14px;
    border: 1px dashed var(--border);
    border-radius: 10px;
    font-size: 13px;
    color: var(--text-muted);
  }

  .art-preview {
    border: none;
    background: none;
    padding: 0;
    cursor: pointer;
  }

  .art-preview img {
    width: 100%;
    border-radius: 10px;
  }

  .lightbox {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.7);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px;
    z-index: 20;
  }

  .lightbox img {
    max-width: min(360px, 90vw);
    border-radius: 12px;
  }

  .close {
    align-self: flex-end;
    margin-bottom: 12px;
    min-height: 44px;
    padding: 0 16px;
    border-radius: 8px;
    border: none;
    background: var(--bg);
    cursor: pointer;
  }
</style>
