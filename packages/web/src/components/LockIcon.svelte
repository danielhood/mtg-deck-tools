<script lang="ts">
  interface Props {
    locked: boolean;
  }

  let { locked }: Props = $props();
</script>

<svg
  class="lock-icon"
  class:lock-icon--locked={locked}
  viewBox="0 0 24 24"
  width="20"
  height="20"
  aria-hidden="true"
  fill="none"
  stroke="currentColor"
  stroke-width="2"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  {#if locked}
    <rect x="5" y="11" width="14" height="10" rx="2" />
    <path d="M8 11V8a4 4 0 0 1 8 0v3" />
  {:else}
    <path d="M7 11V8a5 5 0 0 1 9.9-1" />
    <rect x="5" y="11" width="14" height="10" rx="2" />
  {/if}
</svg>
