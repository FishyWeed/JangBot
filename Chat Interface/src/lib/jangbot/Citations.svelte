<script>
  import Icon from './Icon.svelte';
  /** @type {{ citations: import('./types').Citation[], open?: boolean }} */
  let { citations, open = $bindable(false) } = $props();
  let count = $derived(citations.length);
</script>

{#if count}
  <div class="jb-cite">
    <button type="button" class="jb-cite__toggle" aria-expanded={open} onclick={() => (open = !open)}>
      <Icon name="bookOpen" size={14} />
      <span>{count} verified source{count === 1 ? '' : 's'}</span>
      <span class="jb-cite__ids">{citations.map((c) => c.id).join(' · ')}</span>
      <Icon name="chevronDown" size={14} class="jb-cite__chev" />
    </button>
    {#if open}
      <ul class="jb-cite__list">
        {#each citations as c (c.id)}
          <li class="jb-cite__item">
            <span class="jb-factid">{c.id}</span>
            <div class="jb-cite__body">
              <span class="jb-cite__detail">{c.detail}</span>
              <span class="jb-cite__meta">{c.publisher}<span class="jb-tier" class:jb-tier--1={c.tierLevel === 1}>{c.tier}</span></span>
            </div>
            {#if c.url}
              <a class="jb-iconbtn jb-iconbtn--sm" href={c.url} target="_blank" rel="noopener noreferrer" aria-label="Open source {c.id}">
                <Icon name="externalLink" size={15} />
              </a>
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  </div>
{/if}
