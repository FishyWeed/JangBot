<script lang="ts">
	import { goto } from '$app/navigation';
	import { Landing } from '#lib/jangbot/index.js';
</script>

<Landing onstart={() => goto('/chat')} />
