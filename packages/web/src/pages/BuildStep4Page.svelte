<script lang="ts">
  import ColorPipPicker from "../components/ColorPipPicker.svelte";
  import WizardChrome from "../components/WizardChrome.svelte";
  import WizardIntro from "../components/WizardIntro.svelte";
  import { loadDraft, saveDraft, type WizardDraft } from "../lib/criteria";
  import type { WizardMeta } from "../lib/api";
  import { formatColors } from "../lib/format";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();

  let draft = $state<WizardDraft>(loadDraft());

  $effect(() => {
    saveDraft(draft);
  });

  function summary(): string {
    if (draft.colorFilter === "colorless") return "Colorless only";
    if (draft.colorFilter === "any" || !draft.colors.length) return "Any (no color filter)";
    return formatColors(draft.colors);
  }
</script>

<WizardChrome step={4} backRoute="/build/3" nextRoute="/build/5" dbReady={meta.db_ready}>
  <WizardIntro
    title="Colors"
    lead="Choose colors that should be present in the commander's identity."
  />

  <section class="wizard-section" aria-label="Color identity">
    <ColorPipPicker
      mode="wizard"
      colorFilter={draft.colorFilter}
      colors={draft.colors}
      onwizardchange={(value) => (draft = { ...draft, ...value })}
    />

    <div class="selection-summary" aria-live="polite">
      <h3>Selected identity</h3>
      <p>{summary()}</p>
    </div>
  </section>
</WizardChrome>
