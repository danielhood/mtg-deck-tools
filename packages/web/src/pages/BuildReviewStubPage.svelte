<script lang="ts">
  import WizardIntro from "../components/WizardIntro.svelte";
  import WizardProgress from "../components/WizardProgress.svelte";
  import type { WizardMeta } from "../lib/api";
  import { navigate } from "../lib/router";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();
</script>

<div class="wizard-body">
  <WizardProgress step={7} />
  <WizardIntro
    title="Review & generate"
    lead="UX7c-b adds criteria recap, preflight warnings, and deck generation."
  />
</div>

<div class="wizard-footer">
  <button class="btn btn-back" type="button" onclick={() => navigate("/build/7")}>Back</button>
  <button class="btn btn-next" type="button" disabled>Generate (UX7c-b)</button>
</div>
