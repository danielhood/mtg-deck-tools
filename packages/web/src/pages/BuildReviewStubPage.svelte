<script lang="ts">
  import type { WizardMeta } from "../lib/api";
  import { navigate } from "../lib/router";

  interface Props {
    meta: WizardMeta;
  }

  let { meta }: Props = $props();
</script>

<h2 class="section-title">Review &amp; generate</h2>
<p class="section-lead">
  UX7c-b adds criteria recap, preflight warnings, and deck generation. Wizard steps 1–7 are complete.
</p>

<div class="wizard-footer">
  <button class="btn btn-secondary" type="button" onclick={() => navigate("/build/7")}>Back</button>
  <button class="btn btn-primary" type="button" disabled>Generate (UX7c-b)</button>
</div>

<style>
  :global(.app-main) {
    padding-bottom: calc(var(--footer-height) + 16px);
  }
</style>
