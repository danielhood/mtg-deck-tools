<script lang="ts">
  import { navigate } from "../lib/router";

  $effect(() => {
    navigate("/library", true);
  });
</script>
