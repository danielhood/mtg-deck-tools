<script lang="ts">
  interface Props {
    message?: string;
    detail?: string;
  }

  let { message = "Loading…", detail }: Props = $props();
</script>

<div class="status-panel status-loading" role="status" aria-live="polite" aria-busy="true">
  <span class="status-spinner" aria-hidden="true"></span>
  <div class="status-loading-copy">
    <p>{message}</p>
    {#if detail}
      <p class="status-loading-detail">{detail}</p>
    {/if}
  </div>
</div>
