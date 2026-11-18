<script>
  /** @type {{ connected?: boolean, backend?: string }} */
  let { connected = false, backend } = $props();
</script>

<div class="jb-status" class:is-connecting={!connected} role="status">
  <span class="jb-status__dot"></span>
  <span class="jb-status__state">{connected ? 'Online' : 'Connecting…'}</span>
  {#if backend}<span class="jb-status__sep">·</span><span>Memory: <code>{backend}</code></span>{/if}
</div>
