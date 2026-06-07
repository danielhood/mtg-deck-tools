<script lang="ts">
  interface Props {
    message: string;
    onretry?: () => void;
  }

  let { message, onretry }: Props = $props();
</script>

<div class="status-panel status-error" role="alert">
  <p>{message}</p>
  {#if onretry}
    <button type="button" class="btn btn-secondary status-retry" onclick={onretry}>Try again</button>
  {/if}
</div>
