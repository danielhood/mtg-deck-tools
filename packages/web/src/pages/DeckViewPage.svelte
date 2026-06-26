<script lang="ts">
  import CardLightbox from "../components/CardLightbox.svelte";
  import DeckMetricsPanel from "../components/DeckMetricsPanel.svelte";
  import DependenciesPanel from "../components/DependenciesPanel.svelte";
  import LockIcon from "../components/LockIcon.svelte";
  import ColorPipPicker from "../components/ColorPipPicker.svelte";
  import ErrorState from "../components/ErrorState.svelte";
  import LoadingState from "../components/LoadingState.svelte";
  import ManaCost from "../components/ManaCost.svelte";
  import {
    deleteDeck,
    getDeck,
    patchDeck,
    refillDeckSlot,
    swapDeckCards,
    type SwapRecord,
  } from "../lib/api";
  import { resetDraft } from "../lib/criteria";
  import type { DeckCardPreview } from "../lib/deck-cards";
  import {
    cacheDeck,
    loadCachedDeck,
    removeCachedDeck,
    updateCachedDeck,
    updateCachedDeckName,
  } from "../lib/deck-cache";
  import {
    displayCardName,
    emptyFilters,
    filteredCards,
    formatCardPrice,
    formatSlotCountLine,
    formatSummaryLine,
    formatTypeCountLine,
    groupCardsBySlot,
    parseDeck,
    toggleCardLocked,
    toggleFilterValue,
    type DeckCardRow,
    type DeckFilters,
  } from "../lib/deck-view";
  import { formatTagLabel, pipMiniClass } from "../lib/format";
  import { navigate } from "../lib/router";

  interface Props {
    deckId: string;
  }

  let { deckId }: Props = $props();

  let filters = $state<DeckFilters>(emptyFilters());
  let previewCard = $state<DeckCardPreview | null>(null);
  let loading = $state(true);
  let loadError = $state("");
  let deckName = $state("");
  let deckPayload = $state<Record<string, unknown> | null>(null);
  let returnTo = $state("/library");
  let showRename = $state(false);
  let renameValue = $state("");
  let renameSaving = $state(false);
  let renameError = $state("");
  let showDelete = $state(false);
  let deleteBusy = $state(false);
  let deleteError = $state("");
  let highlightedOracleId = $state<string | null>(null);
  let highlightTimer: ReturnType<typeof setTimeout> | null = null;

  let lockBusyId = $state<string | null>(null);
  let iterateError = $state("");
  let iterateBusy = $state(false);
  let swappingIssueKey = $state<string | null>(null);
  let regenSlot = $state<string | null>(null);
  let regenBusy = $state(false);
  let swapDiff = $state<SwapRecord[] | null>(null);
  let newCardIds = $state<Set<string>>(new Set());
  let selectedIds = $state<Set<string>>(new Set());

  $effect(() => {
    loading = true;
    loadError = "";
    const cached = loadCachedDeck(deckId);
    if (cached?.deck && Object.keys(cached.deck).length) {
      deckName = cached.name;
      deckPayload = cached.deck;
      returnTo = cached.returnTo;
      loading = false;
      return;
    }

    getDeck(deckId)
      .then((detail) => {
        deckName = detail.name;
        deckPayload = detail.deck;
        returnTo = cached?.returnTo ?? "/library";
        cacheDeck({
          id: detail.id,
          name: detail.name,
          deck: detail.deck,
          returnTo,
        });
        loading = false;
      })
      .catch(() => {
        navigate("/", true);
      });
  });

  const parsed = $derived(parseDeck(deckPayload));
  const commander = $derived(parsed?.commanders[0] ?? null);
  const filtered = $derived(parsed ? filteredCards(parsed.cards, filters) : []);
  const slotGroups = $derived(
    parsed ? groupCardsBySlot(filtered, parsed.slotOrder) : [],
  );
  const selectionCount = $derived(selectedIds.size);
  const dependencyHasIssues = $derived(
    parsed != null &&
      (!parsed.dependencyReport.passed || parsed.dependencyReport.reviewCount > 0),
  );

  $effect(() => {
    if (!parsed?.filterOptions.colors.length) return;
    const available = new Set(parsed.filterOptions.colors);
    const pruned = new Set([...filters.colors].filter((color) => available.has(color)));
    if (pruned.size !== filters.colors.size) {
      filters = { ...filters, colors: pruned };
    }
  });

  function applyDeckUpdate(deck: Record<string, unknown>): void {
    deckPayload = deck;
    cacheDeck({ id: deckId, name: deckName, deck, returnTo });
    updateCachedDeck(deckId, deck);
  }

  function openCardPreview(card: DeckCardRow): void {
    previewCard = {
      name: card.name,
      type_line: card.type_line,
      image_uri: card.image_uri,
      scryfall_uri: card.scryfall_uri,
    };
  }

  function toggleSlot(slot: string): void {
    filters = { ...filters, slots: toggleFilterValue(filters.slots, slot) };
  }

  function toggleType(type: string): void {
    filters = { ...filters, types: toggleFilterValue(filters.types, type) };
  }

  function clearFilterGroup(group: keyof DeckFilters): void {
    filters = { ...filters, [group]: new Set() };
  }

  function toggleSelection(oracleId: string): void {
    const next = new Set(selectedIds);
    if (next.has(oracleId)) next.delete(oracleId);
    else next.add(oracleId);
    selectedIds = next;
  }

  function clearSelection(): void {
    selectedIds = new Set();
  }

  async function toggleLock(card: DeckCardRow): Promise<void> {
    if (!deckPayload || lockBusyId) return;
    const nextLocked = !card.locked;
    const nextDeck = toggleCardLocked(deckPayload, card.oracle_id, nextLocked);
    lockBusyId = card.oracle_id;
    iterateError = "";
    try {
      const detail = await patchDeck(deckId, { deck: nextDeck });
      applyDeckUpdate(detail.deck);
    } catch (err) {
      iterateError = err instanceof Error ? err.message : "Lock update failed.";
    } finally {
      lockBusyId = null;
    }
  }

  function promptRegen(slot: string): void {
    regenSlot = slot;
    iterateError = "";
  }

  async function confirmRegen(): Promise<void> {
    if (!regenSlot) return;
    regenBusy = true;
    iterateError = "";
    try {
      const detail = await refillDeckSlot(deckId, regenSlot);
      applyDeckUpdate(detail.deck);
      swapDiff = null;
      newCardIds = new Set();
      regenSlot = null;
    } catch (err) {
      iterateError = err instanceof Error ? err.message : "Slot regenerate failed.";
    } finally {
      regenBusy = false;
    }
  }

  async function performSwap(oracleIds?: string[]): Promise<void> {
    const targets = oracleIds ?? [...selectedIds];
    if (!targets.length || iterateBusy) return;
    iterateBusy = true;
    iterateError = "";
    try {
      const response = await swapDeckCards(deckId, targets);
      applyDeckUpdate(response.deck);
      swapDiff = response.swaps;
      newCardIds = new Set(response.swaps.map((row) => row.to_oracle_id));
      selectedIds = new Set();
      swappingIssueKey = null;
    } catch (err) {
      iterateError = err instanceof Error ? err.message : "Swap failed.";
    } finally {
      iterateBusy = false;
    }
  }

  async function swapIssueCards(oracleIds: string[], issueKey: string): Promise<void> {
    swappingIssueKey = issueKey;
    await performSwap(oracleIds);
  }

  function openRename(): void {
    renameValue = deckName;
    renameError = "";
    showRename = true;
  }

  async function confirmRename(): Promise<void> {
    const next = renameValue.trim();
    if (!next) {
      renameError = "Name is required.";
      return;
    }
    renameSaving = true;
    renameError = "";
    try {
      const detail = await patchDeck(deckId, { name: next });
      deckName = detail.name;
      if (deckPayload) {
        cacheDeck({ id: deckId, name: detail.name, deck: deckPayload, returnTo });
      }
      updateCachedDeckName(deckId, detail.name);
      showRename = false;
    } catch (err) {
      renameError = err instanceof Error ? err.message : "Rename failed.";
    } finally {
      renameSaving = false;
    }
  }

  async function confirmDelete(): Promise<void> {
    deleteBusy = true;
    deleteError = "";
    try {
      await deleteDeck(deckId);
      removeCachedDeck(deckId);
      navigate(returnTo === `/deck/${deckId}` ? "/" : returnTo, true);
    } catch (err) {
      deleteError = err instanceof Error ? err.message : "Delete failed.";
    } finally {
      deleteBusy = false;
    }
  }

  function buildAnother(): void {
    resetDraft();
    navigate("/build/1");
  }

  function showInDeck(oracleId: string): void {
    if (highlightTimer) clearTimeout(highlightTimer);
    highlightedOracleId = oracleId;
    requestAnimationFrame(() => {
      document.getElementById(`deck-card-${oracleId}`)?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    });
    highlightTimer = setTimeout(() => {
      highlightedOracleId = null;
      highlightTimer = null;
    }, 2000);
  }
</script>

{#if loading}
  <LoadingState message="Loading deck…" />
{:else if loadError}
  <ErrorState message={loadError} />
{:else if parsed}
  <div class="deck-view-body deck-view-editing">
    <div class="deck-label-row">
      <h2 class="deck-label">{deckName}</h2>
      <button type="button" class="rename-btn" aria-label="Rename deck" onclick={openRename}>
        ✎
      </button>
    </div>

    {#if swapDiff?.length}
      <aside class="swap-diff" role="status">
        <h3 class="swap-diff-title">Swapped {swapDiff.length} card{swapDiff.length === 1 ? "" : "s"}</h3>
        <ul class="swap-diff-list">
          {#each swapDiff as row (row.from_oracle_id + row.to_oracle_id)}
            <li>{row.from_name} → {row.to_name}</li>
          {/each}
        </ul>
        {#if dependencyHasIssues}
          <p class="swap-diff-warn">
            Dependency review may need attention — check the Dependencies panel below.
          </p>
        {/if}
      </aside>
    {/if}

    {#if iterateError}
      <p class="iterate-error" role="alert">{iterateError}</p>
    {/if}

    {#if commander}
      <section class="commander-block" aria-label="Commander">
        <button
          type="button"
          class="commander-art-btn"
          aria-label={`View ${commander.name} art`}
          onclick={() => openCardPreview({
            oracle_id: commander.oracle_id,
            name: commander.name,
            slot: "commander",
            quantity: 1,
            cmc: 0,
            mana_cost: "",
            type_line: commander.type_line,
            primary_type: "Creature",
            colors: commander.color_identity,
            price_usd: null,
            price_known: false,
            image_uri: commander.image_uri,
            scryfall_uri: commander.scryfall_uri,
            locked: true,
          })}
        >
          {#if commander.image_uri}
            <img src={commander.image_uri} alt="" class="commander-art" />
          {:else}
            <div class="commander-art commander-art-placeholder" aria-hidden="true"></div>
          {/if}
        </button>
        <div class="commander-meta">
          <h1>{commander.name}</h1>
          <p>{commander.type_line}</p>
          {#if commander.color_identity.length}
            <div class="ci-pips" aria-label={`Color identity ${commander.color_identity.join(" ")}`}>
              {#each commander.color_identity as color (color)}
                <span class="ci-pip {pipMiniClass(color)}">{color}</span>
              {/each}
            </div>
          {/if}
        </div>
      </section>
    {/if}

    <section class="deck-panel deck-panel-static" aria-label="Summary">
      <h2 class="deck-panel-heading">Summary</h2>
      <div class="deck-panel-body">
        <p>{formatSummaryLine(parsed.stats)}</p>
        <p class="deck-panel-secondary">{formatSlotCountLine(parsed.slotCounts, parsed.slotOrder)}</p>
        <p class="deck-panel-secondary">{formatTypeCountLine(parsed.typeCounts)}</p>
      </div>
    </section>

    {#if parsed.deckMetrics}
      <DeckMetricsPanel metrics={parsed.deckMetrics} />
    {/if}

    <DependenciesPanel
      report={parsed.dependencyReport}
      cards={parsed.cards}
      swapBusy={iterateBusy}
      swappingIssueKey={swappingIssueKey}
      onShowInDeck={(oracleId) => showInDeck(oracleId)}
      onSwapAll={(oracleIds, issueKey) => void swapIssueCards(oracleIds, issueKey)}
    />

    <section class="deck-filters" aria-label="Filters">
      <div class="filter-group">
        <div class="filter-header">
          <span class="filter-label">Slot</span>
          {#if filters.slots.size}
            <button type="button" class="filter-clear" onclick={() => clearFilterGroup("slots")}>
              Clear
            </button>
          {/if}
        </div>
        <div class="chips">
          {#each parsed.filterOptions.slots as slot (slot)}
            <button
              type="button"
              class="chip"
              class:active={filters.slots.has(slot)}
              onclick={() => toggleSlot(slot)}
            >
              {formatTagLabel(slot)}
            </button>
          {/each}
        </div>
      </div>

      <div class="filter-group">
        <div class="filter-header">
          <span class="filter-label">Type</span>
          {#if filters.types.size}
            <button type="button" class="filter-clear" onclick={() => clearFilterGroup("types")}>
              Clear
            </button>
          {/if}
        </div>
        <div class="chips">
          {#each parsed.filterOptions.types as type (type)}
            <button
              type="button"
              class="chip"
              class:active={filters.types.has(type)}
              onclick={() => toggleType(type)}
            >
              {type}
            </button>
          {/each}
        </div>
      </div>

      {#if parsed.filterOptions.colors.length}
      <div class="filter-group filter-group-colors">
        <div class="filter-header">
          <span class="filter-label">Color</span>
          {#if filters.colors.size}
            <button type="button" class="filter-clear" onclick={() => clearFilterGroup("colors")}>
              Clear
            </button>
          {/if}
        </div>
        <ColorPipPicker
          mode="filter"
          availableColors={parsed.filterOptions.colors}
          selected={filters.colors}
          onfilterchange={(colors) => (filters = { ...filters, colors })}
        />
      </div>
      {/if}
    </section>

    {#if !filtered.length}
      <p class="deck-empty" role="status">No cards match the current filters.</p>
    {:else}
      {#each slotGroups as group (group.slot)}
        <div class="slot-heading-row">
          <h2 class="slot-heading">{group.label}</h2>
          <button
            type="button"
            class="btn-regen"
            disabled={iterateBusy || regenBusy}
            onclick={() => promptRegen(group.slot)}
          >
            Regenerate
          </button>
        </div>
        {#each group.cards as card (card.oracle_id)}
          <div
            id="deck-card-{card.oracle_id}"
            class="card-row"
            class:card-row-highlight={highlightedOracleId === card.oracle_id}
            class:card-row-locked={card.locked}
            class:card-row-selected={selectedIds.has(card.oracle_id)}
            class:card-row-new={newCardIds.has(card.oracle_id)}
          >
            <label class="row-check">
              <input
                type="checkbox"
                checked={selectedIds.has(card.oracle_id)}
                disabled={card.locked || iterateBusy}
                aria-label={`Select ${card.name}`}
                onchange={() => toggleSelection(card.oracle_id)}
              />
            </label>
            <button
              type="button"
              class="card-thumb-btn"
              aria-label={`View ${card.name} art`}
              onclick={() => openCardPreview(card)}
            >
              {#if card.image_uri}
                <img src={card.image_uri} alt="" class="card-thumb" />
              {:else}
                <div class="card-thumb card-thumb-placeholder" aria-hidden="true"></div>
              {/if}
            </button>
            <div class="card-info">
              <div class="card-name">{displayCardName(card)}</div>
              <div class="card-sub">
                <ManaCost cost={card.mana_cost} />
                <span class="card-sub-sep" aria-hidden="true">·</span>
                {formatCardPrice(card)}
                {#if newCardIds.has(card.oracle_id)}
                  <span class="card-sub-sep" aria-hidden="true">·</span>
                  <span class="card-tag-new">new</span>
                {/if}
              </div>
            </div>
            <button
              type="button"
              class="lock-btn"
              class:lock-btn-on={card.locked}
              class:lock-btn-off={!card.locked}
              disabled={lockBusyId === card.oracle_id || iterateBusy}
              aria-label={card.locked ? `Unlock ${card.name}` : `Lock ${card.name}`}
              onclick={() => void toggleLock(card)}
            >
              <LockIcon locked={card.locked} />
            </button>
          </div>
        {/each}
      {/each}
    {/if}
  </div>

  {#if selectionCount > 0}
    <div class="swap-bar" role="toolbar" aria-label="Swap selected cards">
      <button
        type="button"
        class="btn-swap"
        disabled={iterateBusy}
        onclick={() => void performSwap()}
      >
        {iterateBusy ? "Swapping…" : `Swap (${selectionCount})`}
      </button>
      <button type="button" class="btn-clear" disabled={iterateBusy} onclick={clearSelection}>
        Clear
      </button>
    </div>
  {/if}

  <div class="deck-footer deck-footer-stack" class:deck-footer-with-swap={selectionCount > 0}>
    <button class="btn btn-primary" type="button" onclick={buildAnother}>Build another deck</button>
    <button class="btn btn-delete" type="button" onclick={() => (showDelete = true)}>
      Delete deck
    </button>
    <div class="nav-row">
      <button class="btn btn-back" type="button" onclick={() => navigate("/library")}>Library</button>
      <button class="btn btn-back" type="button" onclick={() => navigate("/")}>Home</button>
    </div>
  </div>

  <CardLightbox
    open={previewCard != null}
    name={previewCard?.name ?? ""}
    imageUri={previewCard?.image_uri ?? null}
    subtitle={previewCard?.type_line ?? null}
    onclose={() => (previewCard = null)}
  />

  {#if showRename}
    <div class="modal-backdrop" role="presentation" onclick={() => (showRename = false)}>
      <div
        class="modal-panel"
        role="dialog"
        aria-labelledby="rename-title"
        aria-modal="true"
        onclick={(event) => event.stopPropagation()}
      >
        <h2 id="rename-title" class="modal-title">Rename deck</h2>
        <label class="modal-field">
          <span class="modal-label">Deck name</span>
          <input type="text" bind:value={renameValue} maxlength="120" />
        </label>
        {#if renameError}
          <p class="modal-error" role="alert">{renameError}</p>
        {/if}
        <div class="modal-actions">
          <button class="btn btn-back" type="button" onclick={() => (showRename = false)}>
            Cancel
          </button>
          <button
            class="btn btn-primary"
            type="button"
            disabled={renameSaving}
            onclick={() => void confirmRename()}
          >
            {renameSaving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  {/if}

  {#if regenSlot}
    <div class="modal-backdrop" role="presentation" onclick={() => (regenSlot = null)}>
      <div
        class="modal-panel"
        role="alertdialog"
        aria-labelledby="regen-title"
        aria-modal="true"
        onclick={(event) => event.stopPropagation()}
      >
        <h2 id="regen-title" class="modal-title">Regenerate slot?</h2>
        <p class="modal-copy">
          Replace unlocked cards in <strong>{formatTagLabel(regenSlot)}</strong>. Locked cards stay locked.
        </p>
        {#if iterateError}
          <p class="modal-error" role="alert">{iterateError}</p>
        {/if}
        <div class="modal-actions">
          <button class="btn btn-back" type="button" onclick={() => (regenSlot = null)}>Cancel</button>
          <button
            class="btn btn-primary"
            type="button"
            disabled={regenBusy}
            onclick={() => void confirmRegen()}
          >
            {regenBusy ? "Regenerating…" : "Regenerate"}
          </button>
        </div>
      </div>
    </div>
  {/if}

  {#if showDelete}
    <div class="modal-backdrop" role="presentation" onclick={() => (showDelete = false)}>
      <div
        class="modal-panel"
        role="alertdialog"
        aria-labelledby="delete-title"
        aria-modal="true"
        onclick={(event) => event.stopPropagation()}
      >
        <h2 id="delete-title" class="modal-title">Delete deck?</h2>
        <p class="modal-copy">This removes <strong>{deckName}</strong> from your saved library.</p>
        {#if deleteError}
          <p class="modal-error" role="alert">{deleteError}</p>
        {/if}
        <div class="modal-actions">
          <button class="btn btn-back" type="button" onclick={() => (showDelete = false)}>
            Cancel
          </button>
          <button
            class="btn btn-delete"
            type="button"
            disabled={deleteBusy}
            onclick={() => void confirmDelete()}
          >
            {deleteBusy ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>
    </div>
  {/if}
{/if}
