<script>
  import { danbi } from './art.js';
  /**
   * Danbi in a pose, animated. For the 36/40px avatar use <Mascot> instead.
   * @type {{ pose: 'drumming' | 'sticks' | 'umbrella' | 'wave' | 'bow' | 'sleep' | 'read' | 'sad' | 'lantern',
   *   size?: number | string, still?: boolean, class?: string }}
   */
  let { pose, size, still = false, class: cls = '' } = $props();
  let svg = $derived(danbi(pose).replace('class="jb-danbi-pose ', `class="jb-danbi-pose ${still ? 'is-still ' : ''}`));
  let width = $derived(typeof size === 'number' ? `${size}px` : size);
</script>

<div class="jb-danbi-wrap {cls}" style:width>{@html svg}</div>
