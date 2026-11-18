<script>
  import Mascot from './Mascot.svelte';
</script>

<div class="jb-msg">
  <Mascot size={36} state="thinking" />
  <div class="jb-msg__stack">
    <span class="jb-msg__name">Danbi</span>
    <div class="jb-bubble jb-bubble--assistant jb-typing" role="status" aria-label="Danbi is typing"><span></span><span></span><span></span></div>
  </div>
</div>
