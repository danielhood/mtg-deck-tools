<script lang="ts">
  import CardLightbox from "../components/CardLightbox.svelte";
  import ColorPipPicker from "../components/ColorPipPicker.svelte";
  import { clearDraft } from "../lib/criteria";
  import type { DeckCardPreview } from "../lib/deck-cards";
  import {
    displayCardName,
    emptyFilters,
    filteredCards,
    formatCardMana,
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
  import { renderMarkdown } from "../lib/markdown";
  import { clearResult, loadResult } from "../lib/result";
  import { navigate } from "../lib/router";
  import { formatTagLabel, pipMiniClass } from "../lib/format";

  interface Props {
    deckId: string;
  }

  let { deckId }: Props = $props();

  let filters = $state<DeckFilters>(emptyFilters());
  let previewCard = $state<DeckCardPreview | null>(null);
  let previewEl = $state<HTMLElement | null>(null);

  const stored = $derived(loadResult(deckId));

  $effect(() => {
    if (!stored) navigate("/", true);
  });

  const parsed = $derived(parseDeck(stored?.deck ?? null));
  const commander = $derived(parsed?.commanders[0] ?? null);
  const filtered = $derived(parsed ? filteredCards(parsed.cards, filters) : []);
  const slotGroups = $derived(
    parsed ? groupCardsBySlot(filtered, parsed.slotOrder) : [],
  );
  const markdownHtml = $derived(stored ? renderMarkdown(stored.markdown) : "");

  $effect(() => {
    const el = previewEl;
    if (!el) return;

    const handlePreviewClick = (event: MouseEvent): void => {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const anchor = target.closest("a");
      if (!anchor || !anchor.href.includes("scryfall.com")) return;
      event.preventDefault();
      const cardName = anchor.textContent?.trim();
      const match = parsed?.cards.find((card) => card.name === cardName);
      if (match) openCardPreview(match);
    };

    el.addEventListener("click", handlePreviewClick);
    return () => el.removeEventListener("click", handlePreviewClick);
  });

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

  function buildAnother(): void {
    clearDraft();
    clearResult();
    navigate("/");
  }
</script>

{#if stored && parsed}
  <div class="deck-view-body">
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
              <div class="card-sub">{formatCardMana(card)} · {formatCardPrice(card)}</div>
            </div>
            <span class="slot-badge">{group.label}</span>
          </div>
        {/each}
      {/each}
    {/if}

    <details class="deck-panel deck-md-panel">
      <summary>Markdown preview</summary>
      <article
        class="deck-preview"
        aria-label="Rendered deck Markdown"
        bind:this={previewEl}
      >
        {@html markdownHtml}
      </article>
    </details>
  </div>

  <div class="deck-footer">
    <button class="btn btn-primary" type="button" onclick={buildAnother}>Build another deck</button>
  </div>

  <CardLightbox
    open={previewCard != null}
    name={previewCard?.name ?? ""}
    imageUri={previewCard?.image_uri ?? null}
    subtitle={previewCard?.type_line ?? null}
    onclose={() => (previewCard = null)}
  />
{/if}
