<script>
  import Mascot from './Mascot.svelte';
  import Citations from './Citations.svelte';

  /**
   * One message. Pass `children` to render your own content (e.g. markdown) instead of `content`.
   * @type {{ role: 'user' | 'assistant', content?: string, citations?: import('./types').Citation[],
   *   mascotState?: import('./types').MascotState, children?: import('svelte').Snippet }}
   */
  let { role, content = '', citations = [], mascotState = 'idle', children } = $props();
  let paragraphs = $derived(content.split(/\n{2,}/).filter(Boolean));
</script>

{#snippet body()}
  {#if children}{@render children()}{:else}{#each paragraphs as p}<p>{p}</p>{/each}{/if}
{/snippet}

{#if role === 'user'}
  <div class="jb-msg jb-msg--user">
    <div class="jb-msg__stack"><div class="jb-bubble jb-bubble--user">{@render body()}</div></div>
  </div>
{:else}
  <div class="jb-msg">
    <Mascot size={36} state={mascotState} />
    <div class="jb-msg__stack">
      <span class="jb-msg__name">Danbi</span>
      <div class="jb-bubble jb-bubble--assistant">
        {@render body()}
        <Citations {citations} />
      </div>
    </div>
  </div>
{/if}
