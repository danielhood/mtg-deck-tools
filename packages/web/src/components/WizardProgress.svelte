<script lang="ts">
  interface Props {
    step: number;
  }

  let { step }: Props = $props();
</script>

<div class="progress-bar" aria-hidden="true">
  {#each Array(7) as _, index}
    <div
      class="progress-segment"
      class:is-complete={index + 1 < step}
      class:is-active={index + 1 === step}
    ></div>
  {/each}
</div>
