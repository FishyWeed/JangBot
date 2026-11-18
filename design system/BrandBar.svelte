<script>
  import Logo from './Logo.svelte';
  import Icon from './Icon.svelte';
  /**
   * Logo + panel toggle, pinned top-left at header height. Rendered by <AppShell>.
   * @type {{ panelOpen: boolean, href?: string, ontoggle?: () => void }}
   */
  let { panelOpen, href = '/', ontoggle } = $props();
  let label = $derived(panelOpen ? 'Hide panel' : 'Show panel');
</script>

<div class="jb-brandbar">
  <Logo {href} />
  <button type="button" class="jb-iconbtn jb-panel-toggle" aria-label={label} aria-expanded={panelOpen} aria-controls="jb-sidebar" title="{label} (Ctrl+B)" onclick={ontoggle}>
    <Icon name={panelOpen ? 'panelLeftClose' : 'panelLeftOpen'} size={20} />
  </button>
</div>
