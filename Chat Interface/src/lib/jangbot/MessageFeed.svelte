<script>
  import Danbi from './Danbi.svelte';
  import MessageBubble from './MessageBubble.svelte';
  import TypingIndicator from './TypingIndicator.svelte';

  /**
   * Scrolling conversation. Shows `empty` (e.g. <StarterPrompts>) when there are no messages.
   * @type {{ messages?: import('./types').Message[], thinking?: boolean, connecting?: boolean,
   *   speakingId?: string, showAvatar?: boolean, empty?: import('svelte').Snippet, after?: import('svelte').Snippet }}
   */
  let { messages = [], thinking = false, connecting = false, speakingId, showAvatar = true, empty, after } = $props();

  /** @type {HTMLDivElement | undefined} */
  let el = $state();
  let pinned = true;

  function onScroll() {
    if (el) pinned = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  }
  $effect(() => {
    messages.length; thinking; // follow new content
    if (el && pinned) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  });
</script>

<div class="jb-feed" bind:this={el} onscroll={onScroll}>
  {#if connecting}
    <div class="jb-feed-state" role="status">
      <Danbi pose="lantern" class="jb-feed-state__art" />
      <span class="jb-feed-state__title">Connecting to Danbi…</span>
      <span>He’s lighting the lantern</span>
    </div>
  {:else if !messages.length && !thinking}
    <div class="jb-feed__col">{@render empty?.()}</div>
  {:else}
    <div class="jb-feed__col" aria-live="polite">
      {#each messages as m (m.id)}
        <MessageBubble role={m.role} content={m.content} citations={m.citations} mascotState={m.id === speakingId ? 'speaking' : 'idle'} {showAvatar} />
      {/each}
      {#if thinking}<TypingIndicator {showAvatar} />{/if}
      {@render after?.()}
    </div>
  {/if}
</div>
