<script lang="ts">
  import AppShell from "./components/AppShell.svelte";
  import { getWizardMeta, type WizardMeta } from "./lib/api";
  import { getPath, matchRoute, navigate, subscribe } from "./lib/router";
  import HomePage from "./pages/HomePage.svelte";
  import BuildStep1Page from "./pages/BuildStep1Page.svelte";
  import BuildStep2Page from "./pages/BuildStep2Page.svelte";
  import BuildStep3Page from "./pages/BuildStep3Page.svelte";
  import BuildStep4Page from "./pages/BuildStep4Page.svelte";
  import BuildStep5Page from "./pages/BuildStep5Page.svelte";
  import BuildStep6Page from "./pages/BuildStep6Page.svelte";
  import BuildStep7Page from "./pages/BuildStep7Page.svelte";
  import BuildReviewStubPage from "./pages/BuildReviewStubPage.svelte";

  let path = $state(getPath());
  let meta = $state<WizardMeta | null>(null);
  let loadError = $state("");

  $effect(() => {
    return subscribe(() => {
      path = getPath();
    });
  });

  $effect(() => {
    getWizardMeta()
      .then((response) => {
        meta = response;
        loadError = "";
        if (!response.db_ready && path.startsWith("/build") && path !== "/build/review") {
          navigate("/", true);
        }
      })
      .catch((err: Error) => {
        loadError = err.message;
      });
  });

  const route = $derived(matchRoute(path));

  $effect(() => {
    if (route === "build-redirect") navigate("/build/1", true);
  });
</script>

<AppShell {meta}>
  {#if loadError}
    <p class="inline-warning">{loadError}</p>
  {:else if !meta}
    <p class="section-lead">Loading…</p>
  {:else if route === "home"}
    <HomePage {meta} />
  {:else if route === "build-step-1"}
    <BuildStep1Page {meta} />
  {:else if route === "build-step-2"}
    <BuildStep2Page {meta} />
  {:else if route === "build-step-3"}
    <BuildStep3Page {meta} />
  {:else if route === "build-step-4"}
    <BuildStep4Page {meta} />
  {:else if route === "build-step-5"}
    <BuildStep5Page {meta} />
  {:else if route === "build-step-6"}
    <BuildStep6Page {meta} />
  {:else if route === "build-step-7"}
    <BuildStep7Page {meta} />
  {:else if route === "build-review"}
    <BuildReviewStubPage {meta} />
  {:else}
    <h2 class="section-title">Not found</h2>
    <button class="btn btn-primary" type="button" onclick={() => navigate("/")}>Home</button>
  {/if}
</AppShell>
