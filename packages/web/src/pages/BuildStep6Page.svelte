<script lang="ts">
  import CardLightbox from "../components/CardLightbox.svelte";
  import ErrorState from "../components/ErrorState.svelte";
  import LoadingState from "../components/LoadingState.svelte";
  import WizardChrome from "../components/WizardChrome.svelte";
  import WizardIntro from "../components/WizardIntro.svelte";
  import SectionHeader from "../components/SectionHeader.svelte";
  import { searchCommanders, type CommanderResult, type WizardMeta } from "../lib/api";
  import {
    mergeCommanderSearchResults,
    restoreCommanderQuery,
    restoreCommanderSelection,
    resultToSnapshot,
  } from "../lib/commander-step";
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
  let query = $state(restoreCommanderQuery(draft));
  let results = $state<CommanderResult[]>([]);
  let selected = $state<CommanderResult | null>(restoreCommanderSelection(draft));
  let showArt = $state(false);
  let resultsEl = $state<HTMLDivElement | null>(null);
  let searchLoading = $state(false);
  let searchError = $state("");
  /** Avoid re-running scrollIntoView — it was snapping scroll back to the selected row. */
  let initialSelectionScrollDone = $state(false);

  $effect(() => {
    const q = query;
    if (draft.commander_search_query !== q) {
      draft = { ...draft, commander_search_query: q };
    }
  });

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

    const oracleId = draft.commander_oracle_ids[0];
    const fallback = selected ?? restoreCommanderSelection(draft);

    searchLoading = true;
    searchError = "";

    const timer = setTimeout(() => {
      searchCommanders(params)
        .then((rows) => {
          const merged = mergeCommanderSearchResults(rows, oracleId, fallback);
          results = merged.results;
          if (merged.selected) {
            selected = merged.selected;
            draft = { ...draft, commander_snapshot: resultToSnapshot(merged.selected) };
          }
        })
        .catch((err: Error) => {
          results = [];
          searchError = err.message;
        })
        .finally(() => {
          searchLoading = false;
        });
    }, 200);
    return () => clearTimeout(timer);
  });

  $effect(() => {
    const oracleId = draft.commander_oracle_ids[0];
    if (initialSelectionScrollDone || !oracleId || !results.length || !resultsEl) return;

    queueMicrotask(() => {
      const row = resultsEl?.querySelector(`[data-commander-id="${oracleId}"]`);
      if (!row) return;
      row.scrollIntoView({ block: "nearest" });
      initialSelectionScrollDone = true;
    });
  });

  function clearSearch(): void {
    query = "";
  }

  function pickCommander(row: CommanderResult): void {
    selected = row;
    draft = {
      ...draft,
      commander_oracle_ids: [row.oracle_id],
      commander_label: row.name,
      commander_snapshot: resultToSnapshot(row),
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
      <div class="search-field" class:has-query={query.trim().length > 0}>
        <span class="search-icon" aria-hidden="true">⌕</span>
        <input
          class="search-input"
          type="search"
          placeholder="Search commander name…"
          bind:value={query}
          aria-label="Search commander name"
        />
        <button
          type="button"
          class="search-clear"
          aria-label="Clear search"
          onclick={clearSearch}
        >
          ×
        </button>
      </div>
    </div>

    {#if searchError}
      <ErrorState message={searchError} />
    {:else if searchLoading && !results.length}
      <LoadingState message="Searching commanders…" />
    {/if}

    <div class="commander-results" role="listbox" aria-label="Commander results" bind:this={resultsEl}>
      {#each results as row (row.oracle_id)}
        <button
          type="button"
          class="commander-row"
          class:is-selected={draft.commander_oracle_ids[0] === row.oracle_id}
          data-commander-id={row.oracle_id}
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

<CardLightbox
  open={showArt && selected != null}
  name={selected?.name ?? ""}
  imageUri={selected?.image_uri ?? null}
  subtitle={selected?.type_line ?? null}
  onclose={() => (showArt = false)}
/>

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
</style>
