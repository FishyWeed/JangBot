<script>
  import Mascot from './Mascot.svelte';

  /** @type {{ showAvatar?: boolean }} */
  let { showAvatar = true } = $props();
</script>

<div class="jb-msg">
  {#if showAvatar}<Mascot size={36} state="thinking" />{/if}
  <div class="jb-msg__stack">
    <span class="jb-msg__name">Danbi</span>
    <div class="jb-bubble jb-bubble--assistant jb-typing" role="status" aria-label="Danbi is typing"><span></span><span></span><span></span></div>
  </div>
</div>
