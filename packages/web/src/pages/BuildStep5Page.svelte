<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import type { WizardMeta } from "../lib/api";
  import { formatMoneyInput, formatPrice, parseMoneyInput } from "../lib/format";
  import { loadDraft, saveDraft, type WizardDraft } from "../lib/criteria";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());

  $effect(() => {
    saveDraft(draft);
  });

  function adjustBudget(delta: number): void {
    const current = draft.budget_usd ?? 0;
    draft = { ...draft, budget_usd: Math.max(0, current + delta) };
  }

  function adjustMin(delta: number): void {
    const current = draft.card_price_min_usd ?? 0;
    draft = { ...draft, card_price_min_usd: Math.max(0, current + delta) };
  }

  function adjustMax(delta: number): void {
    const current = draft.card_price_max_usd ?? 5;
    draft = { ...draft, card_price_max_usd: Math.max(0.01, current + delta) };
  }

  const rangeWarning = $derived(
    draft.cardPriceRangeEnabled &&
      draft.card_price_min_usd != null &&
      draft.card_price_max_usd != null &&
      draft.card_price_min_usd > draft.card_price_max_usd,
  );
</script>

<WizardChrome step={5} backRoute="/build/4" nextRoute="/build/6" dbReady={meta.db_ready}>
  <h2 class="section-title">Budget &amp; card prices</h2>
  <p class="section-lead">Optional deck budget and per-card price bounds.</p>

  <div class="toggle-row">
    <label for="budget-enabled">Total deck budget</label>
    <input
      id="budget-enabled"
      type="checkbox"
      checked={draft.budgetEnabled}
      onchange={(e) => {
        const enabled = e.currentTarget.checked;
        draft = {
          ...draft,
          budgetEnabled: enabled,
          strict_budget: enabled ? draft.strict_budget : false,
          prefer_available: enabled ? draft.prefer_available : false,
          budget_usd: enabled ? (draft.budget_usd ?? 150) : null,
        };
      }}
    />
  </div>

  {#if draft.budgetEnabled}
    <div class="money-row">
      <button type="button" class="step" onclick={() => adjustBudget(-5)}>−</button>
      <input
        type="text"
        inputmode="decimal"
        value={formatMoneyInput(draft.budget_usd)}
        oninput={(e) => (draft = { ...draft, budget_usd: parseMoneyInput(e.currentTarget.value) })}
        aria-label="Deck budget USD"
      />
      <button type="button" class="step" onclick={() => adjustBudget(5)}>+</button>
    </div>
    <div class="toggle-row">
      <label for="strict-budget">Exclude cards without USD prices</label>
      <input
        id="strict-budget"
        type="checkbox"
        checked={draft.strict_budget}
        onchange={(e) => (draft = { ...draft, strict_budget: e.currentTarget.checked })}
      />
    </div>
    <div class="toggle-row">
      <label for="prefer-available">Prefer readily available picks</label>
      <input
        id="prefer-available"
        type="checkbox"
        checked={draft.prefer_available}
        onchange={(e) => (draft = { ...draft, prefer_available: e.currentTarget.checked })}
      />
    </div>
  {/if}

  <div class="toggle-row">
    <label for="range-enabled">Per-card price range</label>
    <input
      id="range-enabled"
      type="checkbox"
      checked={draft.cardPriceRangeEnabled}
      onchange={(e) => {
        const enabled = e.currentTarget.checked;
        draft = {
          ...draft,
          cardPriceRangeEnabled: enabled,
          card_price_min_usd: enabled ? draft.card_price_min_usd : null,
          card_price_max_usd: enabled ? draft.card_price_max_usd : null,
        };
      }}
    />
  </div>

  {#if draft.cardPriceRangeEnabled}
    <div class="money-row">
      <span class="field-label">Max</span>
      <button type="button" class="step" onclick={() => adjustMax(-5)}>−</button>
      <input
        type="text"
        value={formatMoneyInput(draft.card_price_max_usd)}
        oninput={(e) => (draft = { ...draft, card_price_max_usd: parseMoneyInput(e.currentTarget.value) })}
      />
      <button type="button" class="step" onclick={() => adjustMax(5)}>+</button>
    </div>
    <div class="money-row">
      <span class="field-label">Min</span>
      <button type="button" class="step" onclick={() => adjustMin(-1)}>−</button>
      <input
        type="text"
        value={formatMoneyInput(draft.card_price_min_usd)}
        oninput={(e) => (draft = { ...draft, card_price_min_usd: parseMoneyInput(e.currentTarget.value) })}
      />
      <button type="button" class="step" onclick={() => adjustMin(1)}>+</button>
    </div>
    {#if rangeWarning}
      <p class="inline-warning">Minimum exceeds maximum — adjust either bound.</p>
    {/if}
  {/if}

  <div class="summary-box">
    Budget: {draft.budgetEnabled ? formatPrice(draft.budget_usd) : "off"} · Per-card range:
    {draft.cardPriceRangeEnabled ? "on" : "off"}
  </div>
</WizardChrome>

<style>
  .money-row {
    display: grid;
    grid-template-columns: auto 48px 1fr 48px;
    gap: 8px;
    align-items: center;
  }

  .money-row input {
    min-height: 44px;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0 10px;
  }

  .step {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--bg);
    font-size: 22px;
    cursor: pointer;
  }
</style>
