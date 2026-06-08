<script lang="ts">
  import CardLightbox from "../components/CardLightbox.svelte";
  import ColorPipPicker from "../components/ColorPipPicker.svelte";
  import ErrorState from "../components/ErrorState.svelte";
  import LoadingState from "../components/LoadingState.svelte";
  import ManaCost from "../components/ManaCost.svelte";
  import { deleteDeck, getDeck, patchDeck } from "../lib/api";
  import { resetDraft } from "../lib/criteria";
  import type { DeckCardPreview } from "../lib/deck-cards";
  import {
    cacheDeck,
    loadCachedDeck,
    removeCachedDeck,
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
      const detail = await patchDeck(deckId, next);
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
</script>

{#if loading}
  <LoadingState message="Loading deck…" />
{:else if loadError}
  <ErrorState message={loadError} />
{:else if parsed}
  <div class="deck-view-body">
    <div class="deck-label-row">
      <h2 class="deck-label">{deckName}</h2>
      <button type="button" class="rename-btn" aria-label="Rename deck" onclick={openRename}>
        ✎
      </button>
    </div>

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

    {#if parsed.analysis.looksGood}
      <div class="analysis-ok" role="status">{parsed.analysis.message}</div>
    {:else}
      <section class="analysis-warn" aria-label="Areas to review">
        <h2>Areas to review</h2>
        <ul>
          {#each parsed.analysis.warnings as issue (issue.rule_id + issue.message)}
            <li><strong>{issue.rule_id}</strong> — {issue.message}</li>
          {/each}
        </ul>
      </section>
    {/if}

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
          selected={filters.colors}
          onfilterchange={(colors) => (filters = { ...filters, colors })}
        />
      </div>
    </section>

    {#if !filtered.length}
      <p class="deck-empty" role="status">No cards match the current filters.</p>
    {:else}
      {#each slotGroups as group (group.slot)}
        <h2 class="slot-heading">{group.label}</h2>
        {#each group.cards as card (card.oracle_id)}
          <div class="card-row">
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
              </div>
            </div>
            <span class="slot-badge">{group.label}</span>
          </div>
        {/each}
      {/each}
    {/if}
  </div>

  <div class="deck-footer deck-footer-stack">
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
