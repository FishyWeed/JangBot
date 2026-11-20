<script lang="ts">
	import { Icon, IconButton } from '#lib/jangbot/index.js';

	export interface TopicItem {
		id: string;
		title: string;
		ko: string;
		prompt: string;
	}

	interface Props {
		open?: boolean;
		busy?: boolean;
		topics: TopicItem[];
		onpick: (prompt: string) => void;
		onclose: () => void;
	}

	let { open = false, busy = false, topics, onpick, onclose }: Props = $props();
</script>

{#if open}
	<div class="jb jb-topics-backdrop" aria-hidden="true" onclick={onclose}></div>
{/if}

<aside
	class="jb jb-topics-panel"
	class:is-open={open}
	aria-label="Ask Danbi about"
	aria-hidden={!open}
>
	<div class="jb-topics-head">
		<div class="jb-topics-heading">
			<span class="jb-topics-icon" aria-hidden="true"><Icon name="sparkles" size={16} /></span>
			<div>
				<h2 class="jb-topics-title">Ask Danbi about</h2>
				<span class="jb-topics-ko" lang="ko">단비에게 물어보세요</span>
			</div>
		</div>
		<IconButton icon="x" label="Close topics panel" onclick={onclose} />
	</div>

	<div class="jb-topics-list" role="list">
		{#each topics as topic (topic.id)}
			<button
				type="button"
				class="jb-topic-row"
				disabled={busy}
				onclick={() => onpick(topic.prompt)}
			>
				<div class="jb-topic-row__text">
					<span class="jb-topic-row__top">
						<span class="jb-topic-row__title">{topic.title}</span>
						<span class="jb-topic-row__ko" lang="ko">{topic.ko}</span>
					</span>
					<span class="jb-topic-row__prompt">{topic.prompt}</span>
				</div>
				<span class="jb-topic-row__arrow" aria-hidden="true">
					<Icon name="arrowRight" size={15} />
				</span>
			</button>
		{/each}
	</div>
</aside>

<style>
	.jb-topics-backdrop {
		position: fixed;
		inset: var(--header-height) 0 0 0;
		z-index: 44;
		background: var(--overlay-backdrop);
		animation: jb-topics-fade 0.18s ease-out;
	}

	.jb-topics-panel {
		position: fixed;
		top: var(--header-height);
		right: 0;
		bottom: 0;
		width: min(336px, 88vw);
		z-index: 45;
		display: flex;
		flex-direction: column;
		background: var(--bg-sidebar);
		border-left: 1px solid var(--border-default);
		box-shadow: -12px 0 36px rgba(0, 0, 0, 0.32);
		transform: translateX(100%);
		visibility: hidden;
		transition:
			transform 0.24s cubic-bezier(0.22, 0.8, 0.24, 1),
			visibility 0s linear 0.24s;
	}

	.jb-topics-panel.is-open {
		transform: translateX(0);
		visibility: visible;
		transition: transform 0.24s cubic-bezier(0.22, 0.8, 0.24, 1);
	}

	.jb-topics-head {
		flex: none;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-2);
		padding: var(--space-4) var(--space-3) var(--space-4) var(--space-4);
		border-bottom: 1px solid var(--border-subtle);
	}

	.jb-topics-heading {
		display: flex;
		align-items: center;
		gap: 10px;
		min-width: 0;
	}

	.jb-topics-icon {
		width: 30px;
		height: 30px;
		border-radius: var(--radius-sm);
		display: grid;
		place-items: center;
		background: var(--accent-soft);
		color: var(--accent);
		border: 1px solid color-mix(in srgb, var(--accent) 45%, var(--border-default));
		flex: none;
	}

	.jb-topics-title {
		margin: 0;
		font-family: var(--font-display);
		font-size: 16px;
		line-height: 20px;
		font-weight: 700;
		color: var(--text-primary);
	}

	.jb-topics-ko {
		display: block;
		font-size: 12px;
		line-height: 16px;
		color: var(--text-secondary);
		margin-top: 2px;
	}

	.jb-topics-list {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		padding: var(--space-3);
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.jb-topic-row {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 11px 12px;
		border-radius: var(--radius-md);
		border: 1px solid var(--border-default);
		background: var(--bg-elevated);
		color: var(--text-primary);
		text-align: left;
		cursor: pointer;
		transition:
			border-color 0.15s ease,
			background-color 0.15s ease,
			transform 0.1s ease;
	}

	.jb-topic-row:hover:not(:disabled) {
		border-color: var(--accent);
		background: var(--bg-selected);
		transform: translateX(-2px);
	}

	.jb-topic-row:active:not(:disabled) {
		transform: translateX(0);
	}

	.jb-topic-row:disabled {
		opacity: 0.55;
		cursor: not-allowed;
	}

	.jb-topic-row__text {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.jb-topic-row__top {
		display: flex;
		align-items: baseline;
		gap: 6px;
		flex-wrap: wrap;
	}

	.jb-topic-row__title {
		font-size: 14px;
		line-height: 19px;
		font-weight: 700;
		color: var(--text-primary);
	}

	.jb-topic-row__ko {
		font-size: 11px;
		line-height: 14px;
		font-weight: 600;
		color: var(--accent);
	}

	.jb-topic-row__prompt {
		font-size: 12px;
		line-height: 17px;
		color: var(--text-secondary);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.jb-topic-row__arrow {
		flex: none;
		color: var(--text-secondary);
		opacity: 0.65;
		transition: transform 0.15s ease, color 0.15s ease, opacity 0.15s ease;
	}

	.jb-topic-row:hover:not(:disabled) .jb-topic-row__arrow {
		color: var(--accent);
		opacity: 1;
		transform: translateX(2px);
	}

	@keyframes jb-topics-fade {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
</style>
