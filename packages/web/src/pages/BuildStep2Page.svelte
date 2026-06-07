<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import WizardIntro from "../components/WizardIntro.svelte";
  import { getMechanics, type MechanicChoice, type WizardMeta } from "../lib/api";
  import { loadDraft, saveDraft, type WizardDraft } from "../lib/criteria";
  import { formatTagLabel } from "../lib/format";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());
  let mechanics = $state<MechanicChoice[]>([]);

  $effect(() => {
    saveDraft(draft);
  });

  $effect(() => {
    getMechanics().then((rows) => {
      mechanics = rows;
    });
  });

  type Triage = "neutral" | "avoid" | "include";

  function triageFor(id: string): Triage {
    if (draft.avoid_mechanics.includes(id)) return "avoid";
    if (draft.include_mechanics.includes(id)) return "include";
    return "neutral";
  }

  function setTriage(id: string, mode: Triage): void {
    const avoid = new Set(draft.avoid_mechanics);
    const include = new Set(draft.include_mechanics);
    avoid.delete(id);
    include.delete(id);
    if (mode === "avoid") avoid.add(id);
    if (mode === "include") include.add(id);
    draft = {
      ...draft,
      avoid_mechanics: [...avoid].sort(),
      include_mechanics: [...include].sort(),
    };
  }

  const avoidCount = $derived(draft.avoid_mechanics.length);
  const includeCount = $derived(draft.include_mechanics.length);
  const neutralCount = $derived(
    Math.max(0, mechanics.length - avoidCount - includeCount),
  );
</script>

<WizardChrome step={2} backRoute="/build/1" nextRoute="/build/3" dbReady={meta.db_ready}>
  <WizardIntro
    title="Include / avoid mechanics"
    lead="Choose which mechanics the build engine should include or avoid."
  />

  <div class="triage-legend" aria-hidden="true">
    <span class="col-keyword">Keyword</span>
    <span class="col-avoid">Avoid</span>
    <span class="col-include">Include</span>
  </div>

  <div class="triage-list" role="list" aria-label="Keyword mechanics triage">
    {#each mechanics as mechanic (mechanic.id)}
      {@const state = triageFor(mechanic.id)}
      <div
        class="triage-row"
        class:is-avoid={state === "avoid"}
        class:is-include={state === "include"}
        role="listitem"
      >
        <span class="keyword">{formatTagLabel(mechanic.id)}</span>
        <button
          type="button"
          class="zone zone-avoid"
          class:is-active={state === "avoid"}
          aria-label={`Avoid ${mechanic.id}`}
          aria-pressed={state === "avoid"}
          onclick={() => setTriage(mechanic.id, state === "avoid" ? "neutral" : "avoid")}
        >
          <span class="zone-mark"></span>
        </button>
        <button
          type="button"
          class="zone zone-include"
          class:is-active={state === "include"}
          aria-label={`Include ${mechanic.id}`}
          aria-pressed={state === "include"}
          onclick={() => setTriage(mechanic.id, state === "include" ? "neutral" : "include")}
        >
          <span class="zone-mark"></span>
        </button>
      </div>
    {/each}
  </div>

  <div class="triage-summary" aria-live="polite">
    <span class="count-avoid"><strong>{avoidCount}</strong> avoided</span>
    <span class="count-neutral"><strong>{neutralCount}</strong> neutral</span>
    <span class="count-include"><strong>{includeCount}</strong> included</span>
  </div>
</WizardChrome>
