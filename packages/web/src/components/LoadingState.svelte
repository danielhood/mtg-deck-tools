<script lang="ts">
  interface Props {
    message?: string;
  }

  let { message = "Loading…" }: Props = $props();
</script>

<div class="status-panel status-loading" role="status" aria-live="polite" aria-busy="true">
  <span class="status-spinner" aria-hidden="true"></span>
  <p>{message}</p>
</div>
