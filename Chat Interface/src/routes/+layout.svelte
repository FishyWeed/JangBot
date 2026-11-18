<script lang="ts">
	import { onMount } from 'svelte';
	import { onNavigate } from '$app/navigation';
	import favicon from '#lib/assets/favicon.svg';
	import '#lib/jangbot/styles/tokens.css';
	import '#lib/jangbot/styles/jangbot.css';
	import { initTheme } from '#lib/jangbot/index.js';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	onMount(initTheme);

	onNavigate((navigation) => {
		if (!document.startViewTransition) return;
		return new Promise((resolve) => {
			document.startViewTransition(async () => {
				resolve();
				await navigation.complete;
			});
		});
	});
</script>

<svelte:head>
	<link rel="icon" type="image/svg+xml" href={favicon} />
</svelte:head>

{@render children()}

<style>
	:global(html) {
		scroll-behavior: smooth;
	}

	:global(html, body) {
		margin: 0;
		padding: 0;
	}

	:global(::view-transition-old(root)),
	:global(::view-transition-new(root)) {
		animation-duration: 240ms;
		animation-timing-function: cubic-bezier(0.22, 0.8, 0.24, 1);
	}

	@media (prefers-reduced-motion: reduce) {
		:global(html) {
			scroll-behavior: auto;
		}
		:global(::view-transition-old(root)),
		:global(::view-transition-new(root)) {
			animation-duration: 1ms;
		}
	}
</style>
