<script lang="ts">
  interface Props {
    step: number;
    complete?: boolean;
  }

  let { step, complete = false }: Props = $props();
</script>

<div class="progress-bar" aria-hidden="true">
  {#each Array(7) as _, index}
    <div
      class="progress-segment"
      class:is-complete={complete || index + 1 < step}
      class:is-active={!complete && index + 1 === step}
    ></div>
  {/each}
</div>
