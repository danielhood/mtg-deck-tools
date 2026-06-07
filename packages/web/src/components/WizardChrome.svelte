<script lang="ts">
  import type { Snippet } from "svelte";
  import { navigate } from "../lib/router";
  import WizardProgress from "./WizardProgress.svelte";

  interface Props {
    step: number;
    backRoute: string | null;
    nextRoute: string | null;
    nextLabel?: string;
    nextDisabled?: boolean;
    dbReady?: boolean;
    children: Snippet;
  }

  let {
    step,
    backRoute,
    nextRoute,
    nextLabel = "Next",
    nextDisabled = false,
    dbReady = true,
    children,
  }: Props = $props();
</script>

<div class="wizard-body">
  <WizardProgress {step} />
  {@render children()}
</div>

<div class="wizard-footer">
  <button
    class="btn btn-back"
    type="button"
    disabled={!backRoute}
    onclick={() => backRoute && navigate(backRoute)}
  >
    Back
  </button>
  <button
    class="btn btn-next"
    type="button"
    disabled={!dbReady || !nextRoute || nextDisabled}
    onclick={() => nextRoute && !nextDisabled && navigate(nextRoute)}
  >
    {nextLabel}
  </button>
</div>
