<script lang="ts">
	import { Mascot } from '#lib/jangbot/index.js';
	import type { MascotState } from '#lib/jangbot/types.d.ts';

	interface Props {
		state?: MascotState;
		size?: number;
		framed?: boolean;
		label?: string;
	}

	let { state = 'idle', size = 44, framed = true, label }: Props = $props();
</script>

<Mascot {state} {size} {framed} {label} />
