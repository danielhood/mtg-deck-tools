<script lang="ts">
  import ErrorState from "../components/ErrorState.svelte";
  import LoadingState from "../components/LoadingState.svelte";
  import WizardChrome from "../components/WizardChrome.svelte";
  import WizardIntro from "../components/WizardIntro.svelte";
  import SectionHeader from "../components/SectionHeader.svelte";
  import { getRarities, type RarityChoice, type WizardMeta } from "../lib/api";
  import { loadDraft, saveDraft, type WizardDraft } from "../lib/criteria";
  import { RARITY_HINTS } from "../lib/format";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());
  let rarities = $state<RarityChoice[]>([]);
  let loading = $state(true);
  let error = $state("");
  let reload = $state(0);

  $effect(() => {
    saveDraft(draft);
  });

  $effect(() => {
    loading = true;
    error = "";
    void reload;
    getRarities()
      .then((rows) => {
        rarities = rows;
      })
      .catch((err: Error) => {
        error = err.message;
      })
      .finally(() => {
        loading = false;
      });
  });
</script>

<WizardChrome
  step={7}
  backRoute="/build/6"
  nextRoute="/build/review"
  nextLabel="Next"
  dbReady={meta.db_ready}
>
  <WizardIntro
    title="Card rarity"
    lead="Exclude maindeck cards below this rarity. Commander is not filtered here."
  />

  <section aria-labelledby="rarity-heading">
    <SectionHeader
      id="rarity-heading"
      title="Minimum card rarity"
      description="Choose the lowest rarity allowed in the 99-card maindeck."
    />

    {#if error}
      <ErrorState message={error} onretry={() => (reload += 1)} />
    {:else if loading}
      <LoadingState message="Loading rarity options…" />
    {/if}

    <div class="rarity-list" role="radiogroup" aria-label="Minimum card rarity">
      {#each loading ? [] : rarities as rarity (rarity.id)}
        <label class="rarity-option">
          <input
            type="radio"
            name="min_rarity"
            value={rarity.id}
            checked={draft.min_rarity === rarity.id}
            onchange={() => (draft = { ...draft, min_rarity: rarity.id })}
          />
          <span class="rarity-gem rarity-{rarity.id}" aria-hidden="true"></span>
          <span class="rarity-copy">
            <strong>{rarity.label}</strong>
            <span>{RARITY_HINTS[rarity.id] ?? ""}</span>
          </span>
        </label>
      {/each}
    </div>
  </section>
</WizardChrome>
