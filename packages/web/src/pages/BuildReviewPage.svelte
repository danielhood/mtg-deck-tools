<script lang="ts">
  import ErrorState from "../components/ErrorState.svelte";
  import LoadingState from "../components/LoadingState.svelte";
  import SectionHeader from "../components/SectionHeader.svelte";
  import WizardIntro from "../components/WizardIntro.svelte";
  import WizardProgress from "../components/WizardProgress.svelte";
  import {
    getMechanics,
    getRarities,
    getSlotTemplateDefaults,
    getThemes,
    postGenerate,
    postPreflight,
    postSynergyContext,
    type CriteriaWarning,
    type WizardMeta,
  } from "../lib/api";
  import { loadDraft, toDeckCriteria, type WizardDraft } from "../lib/criteria";
  import { buildSummaryRows, slotTemplateEntries } from "../lib/review-summary";
  import { saveResult } from "../lib/result";
  import { navigate } from "../lib/router";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());
  let warnings = $state<CriteriaWarning[]>([]);
  let preflightLoading = $state(true);
  let preflightError = $state("");
  let generating = $state(false);
  let generateError = $state("");

  let themeLabels = $state<Record<string, string>>({});
  let mechanicLabels = $state<Record<string, string>>({});
  let slotLabels = $state<Record<string, string>>({});
  let slotOrder = $state<string[]>([]);
  let rarityLabels = $state<Record<string, string>>({});
  let profiles = $state<Awaited<ReturnType<typeof postSynergyContext>>["activated_profiles"]>([]);

  const criteria = $derived(toDeckCriteria(draft));

  const summaryRows = $derived(
    buildSummaryRows(draft, {
      themeLabels,
      mechanicLabels,
      slotLabels,
      slotOrder,
      profiles,
      rarityLabels,
    }),
  );

  const slotRows = $derived(slotTemplateEntries(draft, slotLabels, slotOrder));

  const generateDisabled = $derived(
    !meta.db_ready || generating || preflightLoading || !draft.commander_oracle_ids.length,
  );

  $effect(() => {
    Promise.all([
      getThemes(),
      getMechanics(),
      getSlotTemplateDefaults(),
      getRarities(),
      postSynergyContext(criteria),
    ])
      .then(([themes, mechanics, slots, rarities, synergy]) => {
        themeLabels = Object.fromEntries(themes.map((row) => [row.id, row.description]));
        mechanicLabels = Object.fromEntries(mechanics.map((row) => [row.id, row.description]));
        slotLabels = slots.labels;
        slotOrder = slots.order;
        rarityLabels = Object.fromEntries(rarities.map((row) => [row.id, row.label]));
        profiles = synergy.activated_profiles;
      })
      .catch(() => {
        /* summary falls back to tag labels */
      });
  });

  $effect(() => {
    preflightLoading = true;
    preflightError = "";
    postPreflight(criteria)
      .then((response) => {
        warnings = response.warnings;
        preflightLoading = false;
      })
      .catch((err: Error) => {
        preflightError = err.message;
        warnings = [];
        preflightLoading = false;
      });
  });

  async function handleGenerate(): Promise<void> {
    if (generateDisabled) return;
    generating = true;
    generateError = "";
    try {
      const response = await postGenerate(criteria);
      if (!response.markdown) {
        throw new Error("Generate succeeded but no markdown was returned.");
      }
      const deckId = saveResult({
        markdown: response.markdown,
        json_path: response.json_path,
        md_path: response.md_path,
        deck: response.deck,
      });
      navigate(`/deck/${deckId}`);
    } catch (err) {
      generateError = err instanceof Error ? err.message : "Generate failed.";
    } finally {
      generating = false;
    }
  }
</script>

<div class="wizard-body">
  <WizardProgress step={7} complete />
  <WizardIntro
    title="Review & generate"
    lead="Check preflight warnings, then generate your deck."
  />

  <section class="wizard-section" aria-labelledby="warnings-heading">
    <SectionHeader id="warnings-heading" title="Preflight warnings" />

    {#if preflightLoading}
      <LoadingState message="Checking criteria…" />
    {:else if preflightError}
      <ErrorState message={preflightError} />
    {:else if warnings.length}
      <div class="warnings-panel" role="region" aria-label="Preflight warnings">
        <div class="warnings-panel-header">
          <span class="warnings-icon" aria-hidden="true">!</span>
          <strong>{warnings.length} warning{warnings.length === 1 ? "" : "s"}</strong>
        </div>
        <ul class="warnings-list">
          {#each warnings as warning (warning.rule_id + warning.message)}
            <li>{warning.message}</li>
          {/each}
        </ul>
        <p class="warnings-footnote">Use Back to revise earlier steps.</p>
      </div>
    {:else}
      <div class="preflight-ok" role="status">
        <strong>No preflight issues</strong>
        <span>Criteria checks passed — ready to generate.</span>
      </div>
    {/if}
  </section>

  <section class="wizard-section" aria-labelledby="criteria-heading">
    <SectionHeader
      id="criteria-heading"
      title="Deck criteria"
      description="Read-only recap of wizard selections."
    />

    <div class="summary-card">
      {#each summaryRows as row (row.label)}
        <div class="summary-row">
          <span class="summary-label">{row.label}</span>
          <span class="summary-value" class:is-muted={row.muted}>
            {#if row.lines.length === 1}
              {row.lines[0]}
            {:else}
              <span class="summary-value-stack">
                {#each row.lines as line}
                  <span>{line}</span>
                {/each}
              </span>
            {/if}
          </span>
        </div>
      {/each}

      {#if slotRows.length}
        <details class="summary-details">
          <summary>Slot template (99 + commander)</summary>
          <div class="slot-mini-grid" aria-label="Slot counts">
            {#each slotRows as slot (slot.label)}
              <span>{slot.label}</span>
              <span>{slot.count}</span>
            {/each}
          </div>
        </details>
      {/if}
    </div>
  </section>

  {#if generateError}
    <ErrorState message={generateError} />
  {/if}
</div>

<div class="wizard-footer">
  <button class="btn btn-back" type="button" onclick={() => navigate("/build/7")}>Back</button>
  <button
    class="btn btn-generate"
    type="button"
    disabled={generateDisabled}
    onclick={handleGenerate}
  >
    {generating ? "Generating…" : "Generate"}
  </button>
</div>
