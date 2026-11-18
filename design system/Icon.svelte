<script>
  import { ICONS } from './icons.js';
  /** @type {{ name: keyof typeof ICONS, size?: number, class?: string }} */
  let { name, size = 18, class: cls = '' } = $props();
</script>

<svg class="jb-icon {cls}" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{@html ICONS[name]}</svg>
