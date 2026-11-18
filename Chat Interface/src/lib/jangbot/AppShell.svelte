<script>
  import RainLayer from './RainLayer.svelte';
  import BrandBar from './BrandBar.svelte';
  import { onMount } from 'svelte';

  /**
   * Layout: pinned brand bar (logo + panel toggle) + collapsible sidebar + chat column.
   * Desktop (>= 1024px wide): the toggle collapses the inline panel (remembered).
   * Tablet (768–1023px) and mobile (< 768px): it opens an overlay drawer below the top row.
   * The layout follows the width of the app container (.jb-app), not just the window.
   * Ctrl/Cmd+B toggles too; Esc closes the mobile drawer.
   * @type {{ collapsed?: boolean, open?: boolean, rain?: boolean, href?: string,
   *   sidebar: import('svelte').Snippet, children: import('svelte').Snippet }}
   */
  let { collapsed = $bindable(false), open = $bindable(false), rain = true, href = '/', sidebar, children } = $props();

  const KEY = 'jangbot-panel';
  /** @type {HTMLDivElement | undefined} */
  let app = $state();
  /** @type {'desktop' | 'tablet' | 'mobile'} */
  let layout = $state('desktop');
  let overlay = $derived(layout !== 'desktop');
  let panelOpen = $derived(overlay ? open : !collapsed);

  onMount(() => {
    try { if (localStorage.getItem(KEY) === 'collapsed') collapsed = true; } catch {}
    const ro = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      layout = w >= 1024 ? 'desktop' : w >= 768 ? 'tablet' : 'mobile';
      if (layout === 'desktop') open = false;
    });
    if (app) ro.observe(app);
    return () => ro.disconnect();
  });

  function toggle() {
    if (overlay) { open = !open; return; }
    collapsed = !collapsed;
    try { localStorage.setItem(KEY, collapsed ? 'collapsed' : 'open'); } catch {}
  }
  function onKey(/** @type {KeyboardEvent} */ e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') { e.preventDefault(); toggle(); }
    else if (open && e.key === 'Escape') open = false;
  }
</script>

<svelte:window onkeydown={onKey} />

<div class="jb-app" bind:this={app} data-layout={layout}>
<div class="jb jb-shell" class:is-collapsed={collapsed && !overlay} class:is-open={overlay && open}>
  {#if rain}<RainLayer />{/if}
  <BrandBar {panelOpen} {href} ontoggle={toggle} />
  {@render sidebar()}
  <main class="jb-shell__main">
    {@render children()}
  </main>
  <div class="jb-backdrop" aria-hidden="true" onclick={() => (open = false)}></div>
</div>
</div>
