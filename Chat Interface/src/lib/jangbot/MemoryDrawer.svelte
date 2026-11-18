<script>
  import Icon from './Icon.svelte';
  import IconButton from './IconButton.svelte';
  import Danbi from './Danbi.svelte';

  /** @type {{ memories?: string[], onclose?: () => void }} */
  let { memories = [], onclose } = $props();
</script>

<svelte:window onkeydown={(e) => e.key === 'Escape' && onclose?.()} />

<section class="jb-drawer" aria-label="Stored memories">
  <div class="jb-drawer__head">
    <span class="jb-drawer__title">
      <Icon name="database" size={16} />Stored Memories for this Profile
      {#if memories.length}<span class="jb-drawer__count">{memories.length}</span>{/if}
    </span>
    <IconButton icon="x" label="Close memories" size="sm" onclick={onclose} />
  </div>
  <div class="jb-drawer__body">
    {#if memories.length}
      <ul class="jb-drawer__list">
        {#each memories as m}<li>{m}</li>{/each}
      </ul>
    {:else}
      <div class="jb-drawer__empty">
        <Danbi pose="read" class="jb-drawer__empty-art" />
        <span>No memories yet. Danbi will remember things you share, like your skill level or favourite rhythm.</span>
      </div>
    {/if}
  </div>
</section>
