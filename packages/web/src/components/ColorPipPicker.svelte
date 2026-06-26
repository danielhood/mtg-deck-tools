<script lang="ts">
  import type { ColorFilter } from "../lib/criteria";
  import { COLOR_ORDER, MANA_PIPS, VOID_COLOR_ID } from "../lib/color-pips";

  interface Props {
    mode: "wizard" | "filter";
    colorFilter?: ColorFilter;
    colors?: string[];
    selected?: Set<string>;
    /** Filter mode: only show pips present in the deck (from `parseDeck` filterOptions.colors). */
    availableColors?: string[];
    onwizardchange?: (value: { colorFilter: ColorFilter; colors: string[] }) => void;
    onfilterchange?: (selected: Set<string>) => void;
    voidTitle?: string;
    voidLead?: string;
  }

  let {
    mode,
    colorFilter = "any",
    colors = [],
    selected = new Set<string>(),
    availableColors = [],
    onwizardchange,
    onfilterchange,
    voidTitle = "Colorless only",
    voidLead = "Commanders with empty color identity (void) — excludes all colored picks.",
  }: Props = $props();

  const visiblePips = $derived(
    mode === "filter"
      ? MANA_PIPS.filter((pip) => availableColors.includes(pip.id))
      : MANA_PIPS,
  );
  const showVoidPip = $derived(
    mode === "filter" && availableColors.includes(VOID_COLOR_ID),
  );
  const filterColumnCount = $derived(visiblePips.length + (showVoidPip ? 1 : 0));

  function isPipChecked(id: string): boolean {
    if (mode === "filter") return selected.has(id);
    return colorFilter === "selected" && colors.includes(id);
  }

  function isVoidChecked(): boolean {
    if (mode === "filter") return selected.has(VOID_COLOR_ID);
    return colorFilter === "colorless";
  }

  function togglePip(id: string, checked: boolean): void {
    if (mode === "filter") {
      const next = new Set(selected);
      if (checked) next.add(id);
      else next.delete(id);
      onfilterchange?.(next);
      return;
    }

    const nextColors = new Set(colors);
    if (checked) {
      nextColors.add(id);
      onwizardchange?.({
        colorFilter: "selected",
        colors: COLOR_ORDER.filter((color) => nextColors.has(color)),
      });
      return;
    }

    nextColors.delete(id);
    const ordered = COLOR_ORDER.filter((color) => nextColors.has(color));
    onwizardchange?.({
      colorFilter: ordered.length ? "selected" : "any",
      colors: ordered,
    });
  }

  function toggleVoid(): void {
    const enabled = colorFilter !== "colorless";
    onwizardchange?.(
      enabled
        ? { colorFilter: "colorless", colors: [] }
        : { colorFilter: "any", colors: [] },
    );
  }
</script>

<div
  class="color-grid"
  class:color-grid-six={mode === "filter" && filterColumnCount === 6}
  style={mode === "filter" && filterColumnCount !== 6
    ? `grid-template-columns: repeat(${filterColumnCount}, 1fr)`
    : undefined}
  role="group"
  aria-label="Mana colors"
>
  {#each visiblePips as pip (pip.id)}
    <label class="color-option color-{pip.id.toLowerCase()}">
      <input
        type="checkbox"
        name="color"
        value={pip.id}
        checked={isPipChecked(pip.id)}
        onchange={(e) => togglePip(pip.id, e.currentTarget.checked)}
      />
      <span class="pip-slot">
        <span class="mana-pip" aria-hidden="true">{pip.id}</span>
      </span>
      <span class="color-label">{pip.label}</span>
    </label>
  {/each}

  {#if showVoidPip}
    <label class="color-option color-void">
      <input
        type="checkbox"
        name="color"
        value={VOID_COLOR_ID}
        checked={isVoidChecked()}
        onchange={(e) => togglePip(VOID_COLOR_ID, e.currentTarget.checked)}
      />
      <span class="pip-slot">
        <span class="mana-pip" aria-hidden="true">∅</span>
      </span>
      <span class="color-label">Void</span>
    </label>
  {/if}
</div>

{#if mode === "wizard"}
  <div class="colorless-row">
    <button
      type="button"
      class="colorless-option"
      class:is-selected={isVoidChecked()}
      aria-pressed={isVoidChecked()}
      onclick={toggleVoid}
    >
      <span class="colorless-pip-slot">
        <span class="mana-pip-colorless" aria-hidden="true">∅</span>
      </span>
      <span class="colorless-copy">
        <strong>{voidTitle}</strong>
        <span>{voidLead}</span>
      </span>
    </button>
  </div>
{/if}
