<script lang="ts">
  import { getActiveDeckId } from "../lib/result";
  import { navigate } from "../lib/router";

  $effect(() => {
    const activeId = getActiveDeckId();
    if (activeId) navigate(`/deck/${activeId}`, true);
    else navigate("/", true);
  });
</script>
