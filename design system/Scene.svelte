<script>
  import { art } from './art.js';
  /**
   * A traditional rainy-night environment.
   * @type {{ name: 'hanokNight' | 'eavesRain' | 'palaceGate' | 'pagodaCourtyard' | 'mountainMist' | 'signboard' | 'lantern' | 'windBell' | 'giwaBand',
   *   still?: boolean, class?: string }}
   */
  let { name, still = false, class: cls = '' } = $props();
  let svg = $derived(art(name).replace('class="jb-art ', `class="jb-art ${still ? 'is-still ' : ''}`));
</script>

<div class="jb-scene {cls}">{@html svg}</div>
