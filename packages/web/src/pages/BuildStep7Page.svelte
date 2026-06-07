<script lang="ts">
  import WizardChrome from "../components/WizardChrome.svelte";
  import { getRarities, type RarityChoice, type WizardMeta } from "../lib/api";
  import { loadDraft, saveDraft, type WizardDraft } from "../lib/criteria";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());
  let rarities = $state<RarityChoice[]>([]);

  $effect(() => {
    saveDraft(draft);
  });

  $effect(() => {
    getRarities().then((rows) => {
      rarities = rows;
    });
  });
</script>

<WizardChrome
  step={7}
  backRoute="/build/6"
  nextRoute="/build/review"
  nextLabel="Review"
  dbReady={meta.db_ready}
>
  <h2 class="section-title">Card rarity</h2>
  <p class="section-lead">Minimum maindeck rarity (commander exempt).</p>

  <div class="radio-list" role="radiogroup" aria-label="Minimum rarity">
    {#each rarities as rarity (rarity.id)}
      <label class="radio-row">
        <input
          type="radio"
          name="min-rarity"
          value={rarity.id}
          checked={draft.min_rarity === rarity.id}
          onchange={() => (draft = { ...draft, min_rarity: rarity.id })}
        />
        <span>{rarity.label}</span>
      </label>
    {/each}
  </div>
</WizardChrome>

<style>
  .radio-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .radio-row {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 44px;
    padding: 8px 10px;
    border: 1px solid var(--border);
    border-radius: 10px;
    font-size: 13px;
    cursor: pointer;
  }

  .radio-row input {
    width: 18px;
    height: 18px;
    accent-color: var(--blue-700);
  }
</style>
