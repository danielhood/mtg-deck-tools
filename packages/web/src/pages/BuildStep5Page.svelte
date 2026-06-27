<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import WizardIntro from "../components/WizardIntro.svelte";
  import SectionHeader from "../components/SectionHeader.svelte";
  import ToggleRow from "../components/ToggleRow.svelte";
  import PriceStepperRow from "../components/PriceStepperRow.svelte";
  import type { WizardMeta } from "../lib/api";
  import { loadDraft, saveDraft, type WizardDraft } from "../lib/criteria";
  import {
    BUDGET_MIN,
    BUDGET_STEP,
    formatAmount,
    formatUsd,
    MAX_CARD_STEP,
    MIN_CARD_STEP,
    parseBudgetMoney,
    parseOptionalMoney,
    sanitizeMoneyEntry,
    stepOptional,
  } from "../lib/money";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());
  let budgetText = $state(formatAmount(draft.budget_usd ?? 150));
  let minText = $state(formatAmount(draft.card_price_min_usd));
  let maxText = $state(formatAmount(draft.card_price_max_usd));

  $effect(() => {
    saveDraft(draft);
  });

  const budgetParsed = $derived(parseBudgetMoney(budgetText));
  const minParsed = $derived(parseOptionalMoney(minText));
  const maxParsed = $derived(parseOptionalMoney(maxText));

  const rangeInvalid = $derived(
    minParsed.valid &&
      maxParsed.valid &&
      minParsed.value !== null &&
      maxParsed.value !== null &&
      minParsed.value > maxParsed.value,
  );

  const budgetFieldInvalid = $derived(draft.budgetEnabled && !budgetParsed.valid);
  const minFieldInvalid = $derived(!minParsed.valid || rangeInvalid);
  const maxFieldInvalid = $derived(!maxParsed.valid || rangeInvalid);

  const budgetLessDisabled = $derived(
    budgetParsed.valid && budgetParsed.value !== null && budgetParsed.value <= BUDGET_MIN,
  );

  const hasPerCardBounds = $derived(
    (minParsed.valid && minParsed.value !== null) || (maxParsed.valid && maxParsed.value !== null),
  );

  function handleBudgetInput(raw: string): void {
    const sanitized = sanitizeMoneyEntry(raw);
    budgetText = sanitized;
    const parsed = parseBudgetMoney(sanitized);
    if (parsed.valid && parsed.value !== null) {
      draft = { ...draft, budget_usd: parsed.value };
    }
  }

  function commitBudgetInput(): void {
    const parsed = parseBudgetMoney(budgetText, { strict: true });
    if (!parsed.valid || parsed.value === null) {
      budgetText = formatAmount(BUDGET_MIN);
      draft = { ...draft, budget_usd: BUDGET_MIN };
      return;
    }
    budgetText = formatAmount(parsed.value);
    draft = { ...draft, budget_usd: parsed.value };
  }

  function handleOptionalInput(raw: string, field: "min" | "max"): void {
    const sanitized = sanitizeMoneyEntry(raw);
    if (field === "min") minText = sanitized;
    else maxText = sanitized;
  }

  function commitOptionalInput(field: "min" | "max"): void {
    const text = field === "min" ? minText : maxText;
    const parsed = parseOptionalMoney(text, { strict: true });
    if (!parsed.valid) {
      if (field === "min") {
        minText = "";
        draft = { ...draft, card_price_min_usd: null };
      } else {
        maxText = "";
        draft = { ...draft, card_price_max_usd: null };
      }
      return;
    }
    const formatted = formatAmount(parsed.value);
    if (field === "min") {
      minText = formatted;
      draft = { ...draft, card_price_min_usd: parsed.value };
    } else {
      maxText = formatted;
      draft = { ...draft, card_price_max_usd: parsed.value };
    }
  }

  function clearOptional(field: "min" | "max"): void {
    if (field === "min") {
      minText = "";
      draft = { ...draft, card_price_min_usd: null };
    } else {
      maxText = "";
      draft = { ...draft, card_price_max_usd: null };
    }
  }

  function stepBudget(direction: "more" | "less"): void {
    const current =
      budgetParsed.valid && budgetParsed.value !== null ? budgetParsed.value : BUDGET_MIN;
    const next =
      direction === "more" ? current + BUDGET_STEP : Math.max(BUDGET_MIN, current - BUDGET_STEP);
    budgetText = formatAmount(next);
    draft = { ...draft, budget_usd: next };
  }

  function stepMin(direction: "more" | "less"): void {
    const next = stepOptional(minParsed.valid ? minParsed.value : null, MIN_CARD_STEP, direction);
    minText = formatAmount(next);
    draft = { ...draft, card_price_min_usd: next };
  }

  function stepMax(direction: "more" | "less"): void {
    const next = stepOptional(maxParsed.valid ? maxParsed.value : null, MAX_CARD_STEP, direction);
    maxText = formatAmount(next);
    draft = { ...draft, card_price_max_usd: next };
  }

  const summaryText = $derived.by(() => {
    const parts: string[] = [];

    if (draft.budgetEnabled) {
      const budgetPart =
        budgetParsed.valid && budgetParsed.value !== null
          ? `Deck budget: ${formatUsd(budgetParsed.value)}`
          : "Deck budget: (invalid amount)";
      const flags: string[] = [];
      if (draft.strict_budget) flags.push("strict");
      if (draft.prefer_available) flags.push("prefer available");
      parts.push(flags.length ? `${budgetPart} · ${flags.join(" · ")}` : budgetPart);
    } else {
      parts.push("No total deck budget");
    }

    if (hasPerCardBounds) {
      if (minParsed.valid && maxParsed.valid) {
        const minLabel = minParsed.value !== null ? formatUsd(minParsed.value) : "no min";
        const maxLabel = maxParsed.value !== null ? formatUsd(maxParsed.value) : "no max";
        parts.push(`Per card: ${minLabel} – ${maxLabel}`);
      } else {
        parts.push("Per-card range: invalid amount");
      }
      if (rangeInvalid) parts.push("min > max");
    }

    if (
      parts.length === 1 &&
      parts[0] === "No total deck budget" &&
      !hasPerCardBounds
    ) {
      return { text: "No price constraints", muted: true };
    }
    return { text: parts.join(" · "), muted: false };
  });
</script>

<WizardChrome step={5} backRoute="/build/4" nextRoute="/build/6" dbReady={meta.db_ready}>
  <WizardIntro
    title="Budget & card prices"
    lead="Optional total deck cap and per-card min/max using Scryfall USD prices."
  />

  <section class="wizard-section" aria-labelledby="budget-heading">
    <SectionHeader
      id="budget-heading"
      title="Total deck budget"
      description="Cap total spend for the full 100-card list."
    />

    <div class="toggle-list">
      <ToggleRow
        title="Set a total deck budget"
        description="Maximum USD spend for the entire deck."
        checked={draft.budgetEnabled}
        ontoggle={(enabled) => {
          const turningOn = enabled && !draft.budgetEnabled;
          draft = {
            ...draft,
            budgetEnabled: enabled,
            strict_budget: enabled ? (turningOn ? true : draft.strict_budget) : false,
            prefer_available: enabled ? (turningOn ? true : draft.prefer_available) : false,
            budget_usd: enabled ? (draft.budget_usd ?? 150) : null,
          };
          if (enabled && !budgetText.trim()) {
            budgetText = formatAmount(draft.budget_usd ?? 150);
          }
        }}
      />
    </div>

    {#if draft.budgetEnabled}
      <div class="conditional-panel">
        <div class="price-stepper-list" aria-label="Deck budget amount">
          <PriceStepperRow
            label="Maximum deck budget"
            inputId="budget-input"
            text={budgetText}
            stepHint="$10 per tap."
            invalid={budgetFieldInvalid}
            lessDisabled={budgetLessDisabled}
            ontextinput={handleBudgetInput}
            onblur={commitBudgetInput}
            onless={() => stepBudget("less")}
            onmore={() => stepBudget("more")}
          />
        </div>

        <div class="nested-toggles" aria-label="Budget enforcement options">
          <ToggleRow
            title="Exclude unpriced cards"
            description="Skip cards without USD prices."
            checked={draft.strict_budget}
            ontoggle={(checked) => (draft = { ...draft, strict_budget: checked })}
          />
          <ToggleRow
            title="Prefer readily available"
            description="Filter obscure / hard-to-find picks."
            checked={draft.prefer_available}
            ontoggle={(checked) => (draft = { ...draft, prefer_available: checked })}
          />
        </div>
      </div>
    {/if}
  </section>

  <section class="wizard-section" aria-labelledby="price-range-heading">
    <SectionHeader
      id="price-range-heading"
      title="Per-card price range"
      description="Optional min and/or max USD per card."
    />

    <div class="price-stepper-list" aria-label="Per-card price bounds">
      <PriceStepperRow
        label="Maximum per card"
        inputId="price-max-input"
        text={maxText}
        placeholder="None"
        stepHint="$5 per tap."
        showClear
        invalid={maxFieldInvalid}
        lessDisabled={maxParsed.value === null}
        ontextinput={(raw) => handleOptionalInput(raw, "max")}
        onblur={() => commitOptionalInput("max")}
        onless={() => stepMax("less")}
        onmore={() => stepMax("more")}
        onclear={() => clearOptional("max")}
      />
      <PriceStepperRow
        label="Minimum per card"
        inputId="price-min-input"
        text={minText}
        placeholder="None"
        stepHint="$1 per tap."
        showClear
        invalid={minFieldInvalid}
        lessDisabled={minParsed.value === null}
        ontextinput={(raw) => handleOptionalInput(raw, "min")}
        onblur={() => commitOptionalInput("min")}
        onless={() => stepMin("less")}
        onmore={() => stepMin("more")}
        onclear={() => clearOptional("min")}
      />
    </div>
    <p class="range-warning" class:is-visible={rangeInvalid} role="alert">
      Minimum exceeds maximum — adjust before continuing.
    </p>
    <span class="field-hint">Leave blank for no limit.</span>
  </section>

  <section aria-labelledby="summary-heading">
    <div class="selection-summary" aria-live="polite">
      <h3 id="summary-heading">Price constraints</h3>
      <p class:is-none={summaryText.muted}>{summaryText.text}</p>
    </div>
  </section>
</WizardChrome>
