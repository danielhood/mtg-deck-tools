<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import { getMechanics, type MechanicChoice, type WizardMeta } from "../lib/api";
  import { loadDraft, saveDraft, type WizardDraft } from "../lib/criteria";

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
</script>

<WizardChrome step={2} backRoute="/build/1" nextRoute="/build/3" dbReady={meta.db_ready}>
  <h2 class="section-title">Include / avoid mechanics</h2>
  <p class="section-lead">Tap × to avoid or + to include. Tap again to clear.</p>

  <div class="triage-list">
    {#each mechanics as mechanic (mechanic.id)}
      {@const state = triageFor(mechanic.id)}
      <div class="triage-row" class:avoid={state === "avoid"} class:include={state === "include"}>
        <div class="keyword">{mechanic.id}</div>
        <button
          type="button"
          class="zone avoid-zone"
          aria-label={`Avoid ${mechanic.id}`}
          onclick={() => setTriage(mechanic.id, state === "avoid" ? "neutral" : "avoid")}
        >
          ×
        </button>
        <button
          type="button"
          class="zone include-zone"
          aria-label={`Include ${mechanic.id}`}
          onclick={() => setTriage(mechanic.id, state === "include" ? "neutral" : "include")}
        >
          +
        </button>
      </div>
    {/each}
  </div>
</WizardChrome>

<style>
  .triage-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .triage-row {
    display: grid;
    grid-template-columns: 1fr 48px 48px;
    align-items: center;
    min-height: 44px;
    border-radius: 8px;
    border: 1px solid var(--border);
    overflow: hidden;
  }

  .triage-row.avoid {
    background: var(--avoid-100);
  }

  .triage-row.include {
    background: var(--include-100);
  }

  .keyword {
    padding: 8px 10px;
    font-size: 13px;
    font-weight: 600;
  }

  .zone {
    min-height: 44px;
    border: none;
    background: transparent;
    font-size: 20px;
    font-weight: 700;
    cursor: pointer;
    color: var(--text-muted);
  }

  .triage-row.avoid .avoid-zone,
  .triage-row.include .include-zone {
    color: var(--blue-900);
    font-weight: 800;
  }
</style>
