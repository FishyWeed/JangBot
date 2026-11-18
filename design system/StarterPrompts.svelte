<script>
  import Icon from './Icon.svelte';
  import Danbi from './Danbi.svelte';

  /** @type {{ prompts?: string[], greeting?: boolean, onpick?: (prompt: string) => void }} */
  let {
    prompts = ['What is a janggu?', 'How old is the janggu?', 'Explain the gutgeori rhythm', 'Which stick hits which head?', 'What is samul nori?', 'How is the janggu tuned?'],
    greeting = true,
    onpick
  } = $props();
</script>

<div class="jb-empty">
  {#if greeting}
    <div class="jb-empty__hello">
      <Danbi pose="wave" class="jb-empty__art" />
      <div>
        <h2 class="jb-empty__title"><span lang="ko">반가워요!</span> Hi, I’m Danbi</h2>
        <p class="jb-empty__sub">Your guide to the Korean hourglass drum, <span lang="ko">장구</span>.</p>
      </div>
    </div>
  {/if}
  <div class="jb-starters">
    <span class="jb-starters__label"><Icon name="sparkles" size={16} />Try asking Danbi:</span>
    <div class="jb-starters__grid">
      {#each prompts as p}
        <button type="button" class="jb-chip" onclick={() => onpick?.(p)}>{p}</button>
      {/each}
    </div>
  </div>
</div>
