<script>
  import Icon from './Icon.svelte';
  import IconButton from './IconButton.svelte';
  /** @type {{ message: string, ondismiss?: () => void }} */
  let { message, ondismiss } = $props();
</script>

<div class="jb-error" role="alert">
  <Icon name="alertCircle" size={18} />
  <span class="jb-error__text">{message}</span>
  <IconButton icon="x" label="Dismiss error" size="sm" onclick={ondismiss} />
</div>
