<script>
  import IconButton from './IconButton.svelte';
  import { theme, toggleTheme } from './theme.svelte.js';
  let dark = $derived(theme.current === 'dark');
</script>

<IconButton icon={dark ? 'sun' : 'moon'} label={dark ? 'Switch to Misty dawn' : 'Switch to Rainy night'} size="sm" onclick={toggleTheme} />
