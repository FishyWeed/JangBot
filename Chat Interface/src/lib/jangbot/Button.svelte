<script>
  import Icon from './Icon.svelte';
  /**
   * @type {{ variant?: 'primary' | 'ghost' | 'ink' | 'outline', block?: boolean, icon?: keyof typeof import('./icons.js').ICONS,
   *   iconSize?: number, label?: string, hideLabelOnMobile?: boolean, children?: import('svelte').Snippet,
   *   class?: string, [key: string]: any }}
   */
  let { variant = 'primary', block = false, icon, iconSize, label, hideLabelOnMobile = false, children, class: cls = '', ...rest } = $props();
</script>

<button type="button" class="jb-btn jb-btn--{variant} {cls}" class:jb-btn--block={block} aria-label={hideLabelOnMobile ? label : undefined} {...rest}>
  {#if icon}<Icon name={icon} size={iconSize ?? (variant === 'primary' ? 18 : 16)} />{/if}
  {#if label}<span class:jb-btn__label--collapse={hideLabelOnMobile}>{label}</span>{/if}
  {@render children?.()}
</button>
