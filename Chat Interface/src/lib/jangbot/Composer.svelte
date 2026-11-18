<script>
  import Icon from './Icon.svelte';

  /**
   * Enter sends, Shift+Enter adds a line. Grows to 200px, then scrolls.
   * @type {{ value?: string, disabled?: boolean, busy?: boolean, placeholder?: string, onsend?: (text: string) => void }}
   */
  let { value = $bindable(''), disabled = false, busy = false, placeholder = 'Ask Danbi about the Korean janggu...', onsend } = $props();

  /** @type {HTMLTextAreaElement | undefined} */
  let ta = $state();
  let canSend = $derived(!disabled && !busy && value.trim().length > 0);

  $effect(() => {
    value; // re-run when the text changes
    if (!ta) return;
    if (!value) {
      ta.style.height = '';
      return;
    }
    ta.style.height = '0px';
    ta.style.height = Math.max(36, Math.min(ta.scrollHeight, 160)) + 'px';
  });

  function send() {
    if (!canSend) return;
    onsend?.(value.trim());
    value = '';
  }
  function onKey(/** @type {KeyboardEvent} */ e) {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); }
  }
</script>

<div class="jb-composer">
  <form class="jb-composer__box" class:is-disabled={disabled} onsubmit={(e) => { e.preventDefault(); send(); }}>
    <textarea bind:this={ta} bind:value class="jb-composer__input" rows="1" {placeholder} {disabled} aria-label="Message Danbi" onkeydown={onKey}></textarea>
    <button type="submit" class="jb-send" disabled={!canSend} aria-label="Send message"><Icon name="send" size={18} /></button>
  </form>
</div>
