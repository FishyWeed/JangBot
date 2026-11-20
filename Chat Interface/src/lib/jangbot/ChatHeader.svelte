<script>
  import Mascot from './Mascot.svelte';
  import Button from './Button.svelte';

  /**
   * @type {{ title: string, thinking?: boolean, mascotState?: 'idle' | 'thinking' | 'speaking',
   *   exploreOpen?: boolean, memoryOpen?: boolean, canReset?: boolean,
   *   ontoggleexplore?: () => void, ontogglememory?: () => void, onreset?: () => void }}
   */
  let { title, thinking = false, mascotState, exploreOpen = false, memoryOpen = false, canReset = true, ontoggleexplore, ontogglememory, onreset } = $props();
  let state = $derived(mascotState ?? (thinking ? 'thinking' : 'idle'));
</script>

<header class="jb-header">
  <Mascot size={40} {state} />
  <div class="jb-header__titles">
    <span class="jb-header__title">{title}</span>
    <span class="jb-header__sub" class:is-thinking={thinking} aria-live="polite">
      <span class="jb-subdot"></span>{thinking ? 'Danbi is thinking…' : 'Isolated profile memory active'}
    </span>
  </div>
  <div class="jb-header__actions">
    {#if ontoggleexplore}
      <Button variant="ghost" icon="network" label="Topics & Map" hideLabelOnMobile aria-expanded={exploreOpen} onclick={ontoggleexplore} />
    {/if}
    <Button variant="ghost" icon="database" label="Memory" hideLabelOnMobile aria-expanded={memoryOpen} onclick={ontogglememory} />
    <Button variant="ghost" icon="rotateCcw" label="Reset" hideLabelOnMobile disabled={thinking || !canReset} onclick={onreset} />
  </div>
</header>
