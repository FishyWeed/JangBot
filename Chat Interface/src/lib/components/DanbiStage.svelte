<script lang="ts">
	import { Danbi, Mascot } from '#lib/jangbot/index.js';

	type DanbiPose =
		| 'drumming'
		| 'wave'
		| 'umbrella'
		| 'read'
		| 'lantern'
		| 'bow'
		| 'sleep'
		| 'sad';

	interface Props {
		pose?: DanbiPose;
		speaking?: boolean;
		thinking?: boolean;
		hasError?: boolean;
		collapsed?: boolean;
		ontoggle?: () => void;
	}

	let {
		pose = 'wave',
		speaking = false,
		thinking = false,
		hasError = false,
		collapsed = false,
		ontoggle
	}: Props = $props();

	const POSE_META: Record<DanbiPose, { title: string; ko: string; line: string }> = {
		drumming: {
			title: 'Speaking',
			ko: '장구 이야기',
			line: 'Sharing verified janggu knowledge with you!'
		},
		read: {
			title: 'Thinking',
			ko: '찾아보는 중',
			line: 'Checking historical records & sources…'
		},
		wave: {
			title: 'Greeting',
			ko: '안녕!',
			line: 'Ask me anything about the Korean janggu.'
		},
		lantern: {
			title: 'Listening',
			ko: '듣고 있어요',
			line: 'Ready for your next question whenever you are.'
		},
		bow: {
			title: 'Clarifying',
			ko: '안내',
			line: 'I specialize solely in the Korean janggu.'
		},
		sad: {
			title: 'Connection issue',
			ko: '잠시만요',
			line: 'Having trouble reaching the server right now.'
		},
		umbrella: {
			title: 'Rainy walk',
			ko: '우산 아래',
			line: 'Listening to the rain fall.'
		},
		sleep: {
			title: 'Resting',
			ko: '쿨쿨',
			line: 'Taking a quick breather.'
		}
	};

	let meta = $derived(POSE_META[pose] ?? POSE_META.lantern);
	let moodClass = $derived(
		hasError ? 'is-error' : thinking ? 'is-thinking' : speaking ? 'is-speaking' : 'is-idle'
	);
</script>

{#if collapsed}
	<button
		type="button"
		class="jb-stage-reopen"
		onclick={ontoggle}
		title="Show full-size Danbi"
		aria-label="Show full-size Danbi"
	>
		<Mascot size={36} state={thinking ? 'thinking' : speaking ? 'speaking' : 'idle'} />
	</button>
{:else}
	<aside class="jb-danbi-stage {moodClass}" aria-label="Danbi live mascot stage">
		{#if ontoggle}
			<button
				type="button"
				class="jb-stage-close"
				onclick={ontoggle}
				title="Minimize Danbi stage"
				aria-label="Minimize Danbi stage"
			>
				×
			</button>
		{/if}

		<div class="jb-stage-glow" aria-hidden="true"></div>

		<div class="jb-stage-figure">
			{#key pose}
				<Danbi {pose} />
			{/key}
		</div>

		<div class="jb-stage-info">
			<div class="jb-stage-badge">
				{#if speaking}
					<span class="jb-stage-bars" aria-hidden="true">
						<span></span><span></span><span></span>
					</span>
				{:else}
					<span class="jb-stage-dot" aria-hidden="true"></span>
				{/if}
				<b>{meta.title}</b>
				<span class="jb-stage-ko" lang="ko">{meta.ko}</span>
			</div>
			<p class="jb-stage-line">{meta.line}</p>
		</div>
	</aside>
{/if}

<style>
	.jb-danbi-stage {
		position: relative;
		width: 300px;
		flex: 0 0 300px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 18px;
		padding: 24px 20px;
		border-left: 1px solid var(--border-default);
		background: linear-gradient(
			180deg,
			color-mix(in srgb, var(--bg-sidebar) 88%, transparent) 0%,
			color-mix(in srgb, var(--bg-elevated) 92%, transparent) 100%
		);
		overflow: hidden;
	}

	.jb-stage-glow {
		position: absolute;
		width: 240px;
		height: 240px;
		border-radius: 50%;
		background: radial-gradient(
			circle,
			color-mix(in srgb, var(--accent) 22%, transparent) 0%,
			transparent 70%
		);
		pointer-events: none;
		transition: transform 0.35s ease, opacity 0.35s ease;
		opacity: 0.7;
	}

	.jb-danbi-stage.is-speaking .jb-stage-glow {
		opacity: 1;
		transform: scale(1.14);
	}

	.jb-danbi-stage.is-thinking .jb-stage-glow {
		opacity: 0.9;
		transform: scale(1.05);
	}

	.jb-stage-figure {
		position: relative;
		z-index: 1;
		width: 224px;
		max-width: 100%;
		transition: transform 0.25s ease;
	}

	.jb-danbi-stage.is-speaking .jb-stage-figure {
		transform: translateY(-2px);
	}

	.jb-stage-info {
		position: relative;
		z-index: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		gap: 8px;
		max-width: 240px;
	}

	.jb-stage-badge {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 5px 12px;
		border-radius: var(--radius-pill);
		background: var(--bg-canvas);
		border: 1px solid var(--border-default);
		font-size: 12px;
		line-height: 16px;
		color: var(--text-primary);
	}

	.jb-danbi-stage.is-speaking .jb-stage-badge {
		border-color: var(--accent);
		background: var(--bg-selected);
	}

	.jb-danbi-stage.is-thinking .jb-stage-badge {
		border-color: var(--highlight);
	}

	.jb-stage-ko {
		color: var(--text-secondary);
		font-weight: 500;
	}

	.jb-stage-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--status-online);
		flex: none;
	}

	.jb-danbi-stage.is-thinking .jb-stage-dot {
		background: var(--highlight);
		animation: jb-stage-pulse 1s ease-in-out infinite;
	}

	.jb-danbi-stage.is-error .jb-stage-dot {
		background: var(--danger);
	}

	.jb-stage-bars {
		display: inline-flex;
		align-items: flex-end;
		gap: 2px;
		height: 12px;
	}

	.jb-stage-bars span {
		width: 2.5px;
		height: 4px;
		border-radius: 2px;
		background: var(--accent);
		animation: jb-stage-eq 0.7s ease-in-out infinite alternate;
	}

	.jb-stage-bars span:nth-child(2) {
		animation-delay: 0.18s;
	}

	.jb-stage-bars span:nth-child(3) {
		animation-delay: 0.34s;
	}

	.jb-stage-line {
		margin: 0;
		font-size: 13px;
		line-height: 19px;
		color: var(--text-secondary);
	}

	.jb-stage-close {
		position: absolute;
		top: 10px;
		right: 10px;
		z-index: 2;
		width: 28px;
		height: 28px;
		border-radius: var(--radius-sm);
		border: 1px solid transparent;
		background: transparent;
		color: var(--text-secondary);
		font-size: 18px;
		line-height: 1;
		cursor: pointer;
		display: grid;
		place-items: center;
	}

	.jb-stage-close:hover {
		background: var(--bg-hover);
		color: var(--text-primary);
	}

	.jb-stage-reopen {
		position: fixed;
		right: 18px;
		bottom: 92px;
		z-index: 15;
		padding: 5px;
		border-radius: 16px;
		border: 1.5px solid var(--border-ink);
		background: var(--bg-elevated);
		box-shadow: var(--shadow-sticker);
		cursor: pointer;
		display: grid;
		place-items: center;
	}

	@keyframes jb-stage-eq {
		from {
			height: 4px;
		}
		to {
			height: 12px;
		}
	}

	@keyframes jb-stage-pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.35;
		}
	}

	@container jbapp (max-width: 1023px) {
		.jb-danbi-stage {
			order: -1;
			width: 100%;
			flex: 0 0 auto;
			flex-direction: row;
			justify-content: flex-start;
			gap: 14px;
			padding: 10px 40px 10px 16px;
			border-left: 0;
			border-bottom: 1px solid var(--border-default);
		}

		.jb-stage-glow {
			width: 120px;
			height: 120px;
			left: 8px;
		}

		.jb-stage-figure {
			width: 88px;
			flex: none;
		}

		.jb-stage-info {
			align-items: flex-start;
			text-align: left;
			max-width: none;
			gap: 4px;
		}

		.jb-stage-line {
			font-size: 12px;
			line-height: 17px;
		}
	}
</style>
