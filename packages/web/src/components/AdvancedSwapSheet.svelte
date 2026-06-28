<script lang="ts">
  import ColorPipPicker from "./ColorPipPicker.svelte";
  import ManaCost from "./ManaCost.svelte";
  import {
    DeckValidationError,
    previewDeckSwap,
    searchCards,
    swapDeckCards,
    getSwapPlaybooks,
    type CardSearchResult,
    type SwapConstraints,
    type SwapPreviewPosition,
    type SwapRecord,
    type SwapPreferredReplacement,
    type SwapStrategy,
  } from "../lib/api";
  import { formatPrice } from "../lib/format";

  export interface AdvancedSwapIssueContext {
    ruleId: string;
    ruleLabel: string;
    deficit?: string | null;
    strategyId?: string | null;
  }

  interface Props {
    open: boolean;
    deckId: string;
    oracleIds: string[];
    cardNames: string[];
    deckColors: string[];
    issue?: AdvancedSwapIssueContext | null;
    onclose: () => void;
    onapplied: (deck: Record<string, unknown>, swaps: SwapRecord[]) => void;
  }

  let {
    open,
    deckId,
    oracleIds,
    cardNames,
    deckColors,
    issue = null,
    onclose,
    onapplied,
  }: Props = $props();

  const TYPE_OPTIONS = [
    "Creature",
    "Instant",
    "Sorcery",
    "Artifact",
    "Enchantment",
    "Equipment",
    "Vehicle",
  ] as const;

  const RARITY_OPTIONS = [
    { id: "common", label: "Common" },
    { id: "uncommon", label: "Uncommon" },
    { id: "rare", label: "Rare" },
    { id: "mythic", label: "Mythic" },
  ] as const;

  let strategies = $state<SwapStrategy[]>([]);
  let strategyId = $state<string | null>(null);
  let selectedTypes = $state<Set<string>>(new Set());
  let selectedColors = $state<Set<string>>(new Set());
  let selectedRarities = $state<Set<string>>(new Set());
  let maxPriceText = $state("");
  let crossSlot = $state(false);
  let filtersOpen = $state(true);
  let busy = $state(false);
  let previewBusy = $state(false);
  let error = $state("");
  let validationErrors = $state<{ code: string; message: string }[]>([]);
  let forceOverride = $state(false);
  let previewRows = $state<SwapPreviewPosition[] | null>(null);
  /** Preview position index → chosen replacement oracle_id */
  let selectedPreview = $state<Record<number, string>>({});

  let cardQuery = $state("");
  let cardResults = $state<CardSearchResult[]>([]);
  let cardSearchBusy = $state(false);
  let namedCard = $state<CardSearchResult | null>(null);
  let searchTimer: ReturnType<typeof setTimeout> | null = null;

  const title = $derived(issue ? `Fix: ${issue.ruleLabel}` : "Advanced swap");
  const subtitle = $derived(
    issue
      ? `Replacing ${oracleIds.length} card${oracleIds.length === 1 ? "" : "s"}`
      : `Replacing ${oracleIds.length} card${oracleIds.length === 1 ? "" : "s"}`,
  );
  const namedCardPinned = $derived(namedCard != null);
  const showValidationBlock = $derived(validationErrors.length > 0);

  $effect(() => {
    if (!open) return;
    error = "";
    validationErrors = [];
    forceOverride = false;
    previewRows = null;
    selectedPreview = {};
    cardQuery = "";
    cardResults = [];
    namedCard = null;
    selectedTypes = new Set();
    selectedColors = new Set();
    selectedRarities = new Set();
    maxPriceText = "";
    crossSlot = false;
    filtersOpen = true;
    strategyId = issue?.strategyId ?? null;
    strategies = [];

    if (issue?.ruleId) {
      void getSwapPlaybooks(issue.ruleId, issue.deficit ?? undefined)
        .then((response) => {
          strategies = response.strategies;
          if (!strategyId) {
            const defaultStrategy = response.strategies.find((row) => row.default);
            strategyId = defaultStrategy?.id ?? response.strategies[0]?.id ?? null;
          }
        })
        .catch(() => {
          strategies = [];
        });
    }
  });

  function clearPreview(): void {
    previewRows = null;
    selectedPreview = {};
  }

  function toggleType(type: string): void {
    const next = new Set(selectedTypes);
    if (next.has(type)) next.delete(type);
    else next.add(type);
    selectedTypes = next;
    clearPreview();
  }

  function toggleRarity(id: string): void {
    const next = new Set(selectedRarities);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    selectedRarities = next;
    clearPreview();
  }

  function buildConstraints(): SwapConstraints | null {
    if (namedCard) {
      return {
        replacement_oracle_id: namedCard.oracle_id,
        slot_policy: crossSlot ? "any" : "same",
      };
    }

    const constraints: SwapConstraints = {
      slot_policy: crossSlot ? "any" : "same",
    };
    if (selectedTypes.size) constraints.type_lines_any = [...selectedTypes];
    if (selectedColors.size) constraints.colors_all = [...selectedColors];
    if (selectedRarities.size) constraints.rarities = [...selectedRarities];
    const maxPrice = parseFloat(maxPriceText);
    if (maxPriceText.trim() && !Number.isNaN(maxPrice)) {
      constraints.max_price_usd = maxPrice;
    }

    const hasManual =
      (constraints.type_lines_any?.length ?? 0) > 0 ||
      (constraints.colors_all?.length ?? 0) > 0 ||
      (constraints.rarities?.length ?? 0) > 0 ||
      constraints.max_price_usd != null ||
      crossSlot;

    if (!hasManual && strategyId) return null;
    return constraints;
  }

  const selectedPreviewCount = $derived(Object.keys(selectedPreview).length);

  function buildPreferredReplacements(): SwapPreferredReplacement[] | undefined {
    if (!previewRows?.length) return undefined;
    const rows: SwapPreferredReplacement[] = [];
    for (const [idx, replacementId] of Object.entries(selectedPreview)) {
      const position = previewRows[Number(idx)];
      if (!position || !replacementId) continue;
      rows.push({
        from_oracle_id: position.from_oracle_id,
        replacement_oracle_id: replacementId,
      });
    }
    return rows.length ? rows : undefined;
  }

  function requestOptions(force = false) {
    const constraints = buildConstraints();
    return {
      constraints,
      strategy_id: constraints ? undefined : strategyId ?? undefined,
      rule_id: issue?.ruleId,
      preferred_replacements: buildPreferredReplacements(),
      force_validation_override: force || forceOverride,
      preview_limit: 8,
    };
  }

  async function runPreview(): Promise<void> {
    if (!oracleIds.length || previewBusy) return;
    previewBusy = true;
    error = "";
    try {
      const response = await previewDeckSwap(deckId, oracleIds, requestOptions());
      previewRows = response.candidates_by_position;
      selectedPreview = {};
    } catch (err) {
      error = err instanceof Error ? err.message : "Preview failed.";
      clearPreview();
    } finally {
      previewBusy = false;
    }
  }

  async function runApply(): Promise<void> {
    if (!oracleIds.length || busy) return;
    busy = true;
    error = "";
    validationErrors = [];
    try {
      const response = await swapDeckCards(deckId, oracleIds, requestOptions());
      onapplied(response.deck, response.swaps);
      onclose();
    } catch (err) {
      if (err instanceof DeckValidationError) {
        validationErrors = err.validationErrors;
        error = err.message;
      } else {
        error = err instanceof Error ? err.message : "Swap failed.";
      }
    } finally {
      busy = false;
    }
  }

  function scheduleCardSearch(query: string): void {
    cardQuery = query;
    namedCard = null;
    clearPreview();
    if (searchTimer) clearTimeout(searchTimer);
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      cardResults = [];
      return;
    }
    searchTimer = setTimeout(() => {
      cardSearchBusy = true;
      const params = new URLSearchParams({ q: trimmed, limit: "8" });
      for (const color of deckColors) params.append("colors", color);
      searchCards(params)
        .then((rows) => {
          cardResults = rows;
        })
        .catch(() => {
          cardResults = [];
        })
        .finally(() => {
          cardSearchBusy = false;
        });
    }, 250);
  }

  function pickNamedCard(row: CardSearchResult): void {
    namedCard = row;
    cardQuery = row.name;
    cardResults = [];
    clearPreview();
  }

  function clearNamedCard(): void {
    namedCard = null;
    cardQuery = "";
    cardResults = [];
    clearPreview();
  }
  function togglePreviewCandidate(positionIndex: number, replacementOracleId: string): void {
    const next = { ...selectedPreview };
    if (next[positionIndex] === replacementOracleId) {
      delete next[positionIndex];
    } else {
      next[positionIndex] = replacementOracleId;
    }
    selectedPreview = next;
  }
</script>

{#if open}
  <div
    class="swap-sheet-scrim"
    role="presentation"
    tabindex="-1"
    onclick={(event) => {
      if (event.target === event.currentTarget) onclose();
    }}
    onkeydown={(event) => {
      if (event.key === "Escape") onclose();
    }}
  >
    <div
      class="swap-sheet"
      role="dialog"
      aria-labelledby="advanced-swap-title"
      aria-modal="true"
      tabindex="-1"
    >
      <div class="swap-sheet-handle" aria-hidden="true"></div>
      <header class="swap-sheet-header">
        <div>
          <h2 id="advanced-swap-title" class="swap-sheet-title">{title}</h2>
          <p class="swap-sheet-sub">{subtitle}</p>
        </div>
        <button type="button" class="swap-sheet-close" aria-label="Close" onclick={onclose}>×</button>
      </header>

      <div class="swap-sheet-scroll">
        <p class="swap-section-label">Replacing</p>
        {#each cardNames as name (name)}
          <div class="swap-chip-card">{name}</div>
        {/each}

        {#if strategies.length}
          <p class="swap-section-label">Strategy</p>
          <div class="chips" role="group" aria-label="Resolution strategies">
            {#each strategies as strategy (strategy.id)}
              <button
                type="button"
                class="chip"
                class:active={strategyId === strategy.id}
                disabled={namedCardPinned}
                onclick={() => {
                  strategyId = strategy.id;
                  clearPreview();
                }}
              >
                {strategy.label}
              </button>
            {/each}
          </div>
        {/if}

        <p class="swap-section-label">Replace with specific card</p>
        <div class="swap-search-wrap">
          <input
            class="swap-search-input"
            type="search"
            placeholder="Search card name…"
            value={cardQuery}
            aria-label="Search card name"
            oninput={(event) => scheduleCardSearch(event.currentTarget.value)}
          />
          {#if namedCard}
            <button type="button" class="swap-search-clear" onclick={clearNamedCard}>Clear</button>
          {/if}
        </div>
        {#if cardSearchBusy}
          <p class="swap-hint">Searching…</p>
        {:else if cardResults.length}
          <div class="swap-search-results" role="listbox" aria-label="Search results">
            {#each cardResults as row (row.oracle_id)}
              <button
                type="button"
                class="swap-result-row"
                class:selected={namedCard?.oracle_id === row.oracle_id}
                onclick={() => pickNamedCard(row)}
              >
                {#if row.image_uri}
                  <img src={row.image_uri} alt="" class="swap-result-thumb" />
                {:else}
                  <div class="swap-result-thumb swap-result-thumb-placeholder" aria-hidden="true"></div>
                {/if}
                <div>
                  <div class="swap-result-name">{row.name}</div>
                  <div class="swap-result-meta">
                    <ManaCost cost={row.mana_cost} />
                    <span aria-hidden="true"> · </span>
                    {row.type_line}
                    {#if row.rarity}
                      <span aria-hidden="true"> · </span>
                      {row.rarity}
                    {/if}
                    {#if row.price_usd != null}
                      <span aria-hidden="true"> · </span>
                      {formatPrice(row.price_usd)}
                    {/if}
                  </div>
                </div>
              </button>
            {/each}
          </div>
        {/if}

        {#if namedCardPinned}
          <p class="swap-hint swap-hint-muted">
            Named card pins the replacement — type/color/rarity filters are hidden.
          </p>
        {:else}
          <button
            type="button"
            class="swap-filters-toggle"
            aria-expanded={filtersOpen}
            onclick={() => (filtersOpen = !filtersOpen)}
          >
            Filters {filtersOpen ? "▾" : "▸"}
          </button>

          {#if filtersOpen}
            <div class="swap-filters">
              <p class="swap-section-label">Card type</p>
              <div class="chips">
                {#each TYPE_OPTIONS as type (type)}
                  <button
                    type="button"
                    class="chip"
                    class:active={selectedTypes.has(type)}
                    onclick={() => toggleType(type)}
                  >
                    {type}
                  </button>
                {/each}
              </div>

              {#if deckColors.length}
                <p class="swap-section-label">Color</p>
                <ColorPipPicker
                  mode="filter"
                  availableColors={deckColors}
                  selected={selectedColors}
                  onfilterchange={(colors) => {
                    selectedColors = colors;
                    clearPreview();
                  }}
                />
              {/if}

              <p class="swap-section-label">Rarity</p>
              <div class="chips">
                {#each RARITY_OPTIONS as rarity (rarity.id)}
                  <button
                    type="button"
                    class="chip"
                    class:active={selectedRarities.has(rarity.id)}
                    onclick={() => toggleRarity(rarity.id)}
                  >
                    {rarity.label}
                  </button>
                {/each}
              </div>

              <label class="swap-price-field">
                <span class="swap-section-label">Max price (USD)</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="No cap"
                  bind:value={maxPriceText}
                  oninput={clearPreview}
                />
              </label>
            </div>
          {/if}
        {/if}

        <label class="swap-scope-row">
          <span>
            <span class="swap-scope-label">Any eligible slot</span>
            <span class="swap-scope-hint">Expert — may move cards across slots</span>
          </span>
          <input type="checkbox" bind:checked={crossSlot} onchange={clearPreview} />
        </label>

        {#if showValidationBlock}
          <div class="swap-validation-block" role="alert">
            <strong>Deck validation failed</strong>
            <ul>
              {#each validationErrors as item (item.code + item.message)}
                <li>{item.message}</li>
              {/each}
            </ul>
          </div>
          <label class="swap-override-row">
            <input type="checkbox" bind:checked={forceOverride} />
            <span>
              <span class="swap-override-label">Override validation and apply anyway</span>
              <span class="swap-override-hint">Deck will be saved with validation errors.</span>
            </span>
          </label>
        {/if}

        {#if error && !showValidationBlock}
          <p class="swap-sheet-error" role="alert">{error}</p>
        {/if}

        {#if previewRows}
          <p class="swap-section-label">
            Preview
            {#if selectedPreviewCount}
              <span class="swap-preview-picked"> · {selectedPreviewCount} selected</span>
            {/if}
          </p>
          <p class="swap-hint">Tap a candidate to prefer it on apply. Unselected slots use a random pick.</p>
          <div class="swap-preview-list">
            {#each previewRows as position, positionIndex (position.from_oracle_id + ":" + positionIndex)}
              <div class="swap-preview-group">
                <div class="swap-preview-from">For {position.from_name}</div>
                {#if position.candidates.length}
                  {#each position.candidates as candidate (candidate.oracle_id)}
                    <button
                      type="button"
                      class="swap-preview-row"
                      class:swap-preview-row-selected={selectedPreview[positionIndex] === candidate.oracle_id}
                      aria-pressed={selectedPreview[positionIndex] === candidate.oracle_id}
                      onclick={() => togglePreviewCandidate(positionIndex, candidate.oracle_id)}
                    >
                      <div class="swap-preview-name">{candidate.name}</div>
                      <div class="swap-preview-meta">
                        <ManaCost cost={candidate.mana_cost} />
                        {#if candidate.price_usd != null}
                          <span aria-hidden="true"> · </span>
                          {formatPrice(candidate.price_usd)}
                        {/if}
                      </div>
                    </button>
                  {/each}
                {:else}
                  <p class="swap-hint">No candidates match these constraints.</p>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <footer class="swap-sheet-footer">
        <button
          type="button"
          class="btn-swap-preview"
          disabled={previewBusy || busy || namedCardPinned}
          onclick={() => void runPreview()}
        >
          {previewBusy ? "Loading preview…" : "Preview candidates"}
        </button>
        <button
          type="button"
          class="btn-swap-apply"
          disabled={busy || (showValidationBlock && !forceOverride)}
          onclick={() => void runApply()}
        >
          {busy ? "Applying…" : showValidationBlock && forceOverride ? "Apply anyway" : "Apply swap"}
        </button>
      </footer>
    </div>
  </div>
{/if}
