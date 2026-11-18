<script>
  import Icon from './Icon.svelte';
  /**
   * Icon-only button. `label` is required: it becomes the aria-label.
   * @type {{ icon: string, label: string, variant?: 'default' | 'danger' | 'confirm', size?: 'md' | 'sm',
   *   iconSize?: number, class?: string, [key: string]: any }}
   */
  let { icon, label, variant = 'default', size = 'md', iconSize, class: cls = '', ...rest } = $props();
</script>

<button type="button" class="jb-iconbtn {cls}" class:jb-iconbtn--sm={size === 'sm'} class:jb-iconbtn--danger={variant === 'danger'} class:jb-iconbtn--confirm={variant === 'confirm'} aria-label={label} title={label} {...rest}>
  <Icon name={icon} size={iconSize ?? (size === 'sm' ? 16 : 18)} />
</button>
