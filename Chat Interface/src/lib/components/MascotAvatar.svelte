<script lang="ts">
	import Mascot from '../jangbot/Mascot.svelte';

	interface Props {
		state?: 'idle' | 'thinking' | 'speaking';
		size?: number;
		framed?: boolean;
	}

	let { state = 'idle', size = 44, framed = true }: Props = $props();
</script>

<Mascot {state} {size} {framed} />
