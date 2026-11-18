<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '../../lib/api';
	import DanbiStage from '../../lib/components/DanbiStage.svelte';
	import {
		AppShell,
		Sidebar,
		ChatHeader,
		MemoryDrawer,
		ErrorBanner,
		MessageFeed,
		StarterPrompts,
		Composer,
		Button,
		Icon
	} from '#lib/jangbot/index.js';
	import type {
		Message as DesignMessage,
		Profile as DesignProfile
	} from '#lib/jangbot/types.d.ts';
	import type { BotConfig, ChatMessage, ChatProfile, ChatProfileSummary } from '../../lib/types';

	const STARTER_PROMPTS = [
		'What is the janggu and where did it originate?',
		'How do court and folk playing techniques differ?',
		'Explain the five foundational strokes.',
		'What are the main jangdan rhythmic cycles?'
	];

	let botConfig = $state<BotConfig | null>(null);
	let profiles = $state<ChatProfileSummary[]>([]);
	let activeProfile = $state<ChatProfile | null>(null);
	let inputText = $state('');
	let isLoading = $state(true);
	let isSending = $state(false);
	let speakingId = $state('');
	let lastReplyStatus = $state<string>('social');
	let errorBanner = $state<string | null>(null);
	let sidebarOpen = $state(false);

	let stagePose = $derived<'drumming' | 'wave' | 'read' | 'lantern' | 'bow' | 'sad'>(
		errorBanner
			? 'sad'
			: isSending
				? 'read'
				: speakingId
					? lastReplyStatus === 'social'
						? 'wave'
						: lastReplyStatus === 'off_topic' ||
							  lastReplyStatus === 'fallback' ||
							  lastReplyStatus === 'clarification'
							? 'bow'
							: 'drumming'
					: (activeProfile?.messages.length ?? 0) <= 1
						? 'wave'
						: 'lantern'
	);

	// Memories & confirm UI state
	let memoriesOpen = $state(false);
	let resetConfirmOpen = $state(false);
	let profileMemories = $state<Array<Record<string, unknown>>>([]);

	let sidebarProfiles = $derived<DesignProfile[]>(
		profiles.map((p) => ({
			id: p.session_id,
			title: p.title,
			lastMessage: p.last_preview
		}))
	);

	let feedMessages = $derived<DesignMessage[]>(
		(activeProfile?.messages ?? []).map((m) => ({
			id: m.id,
			role: m.role,
			content: m.content,
			citations: m.citations?.map((c) => ({
				id: c.fact_id,
				detail: c.detail,
				publisher: c.publisher,
				tier: `Tier ${c.tier}`,
				tierLevel: c.tier,
				url: c.url ?? undefined
			}))
		}))
	);

	let memoryStrings = $derived<string[]>(
		profileMemories.map((mem) => String(mem.memory ?? mem.text ?? JSON.stringify(mem)))
	);

	async function refreshProfiles() {
		profiles = await api.listSessions();
	}

	async function selectProfile(sessionId: string) {
		errorBanner = null;
		memoriesOpen = false;
		const profile = await api.getSession(sessionId);
		activeProfile = profile;
		localStorage.setItem('jangbot_active_session', profile.session_id);
		sidebarOpen = false;
	}

	async function createNewProfile() {
		errorBanner = null;
		memoriesOpen = false;
		const profile = await api.createSession('New Chat');
		await refreshProfiles();
		activeProfile = profile;
		localStorage.setItem('jangbot_active_session', profile.session_id);
		sidebarOpen = false;
	}

	async function confirmResetProfile() {
		resetConfirmOpen = false;
		await handleResetProfile();
	}

	async function handleResetProfile() {
		if (!activeProfile || isSending) return;
		errorBanner = null;
		const reset = await api.resetSession(activeProfile.session_id);
		activeProfile = reset;
		localStorage.setItem('jangbot_active_session', reset.session_id);
		await refreshProfiles();
	}

	async function handleDeleteProfile(sessionId: string) {
		if (isSending) return;
		await api.deleteSession(sessionId);
		await refreshProfiles();

		if (activeProfile?.session_id === sessionId) {
			if (profiles.length > 0) {
				await selectProfile(profiles[0].session_id);
			} else {
				await createNewProfile();
			}
		}
	}

	async function handleRenameProfile(sessionId: string, title: string) {
		const trimmed = title.trim();
		if (!trimmed) return;
		const updated = await api.renameSession(sessionId, trimmed);
		if (activeProfile?.session_id === sessionId) {
			activeProfile = updated;
		}
		await refreshProfiles();
	}

	async function toggleMemoriesDrawer() {
		if (!activeProfile) return;
		memoriesOpen = !memoriesOpen;
		if (memoriesOpen) {
			try {
				profileMemories = await api.getMemories(activeProfile.user_id);
			} catch {
				profileMemories = [];
			}
		}
	}

	async function sendMessage(textOverride?: string) {
		const text = (textOverride ?? inputText).trim();
		if (!text || !activeProfile || isSending) return;

		errorBanner = null;
		if (!textOverride) inputText = '';

		const optimisticUserMsg: ChatMessage = {
			id: `temp-${Date.now()}`,
			role: 'user',
			content: text,
			created_at: new Date().toISOString()
		};

		activeProfile = {
			...activeProfile,
			messages: [...activeProfile.messages, optimisticUserMsg]
		};
		isSending = true;

		try {
			const pacing = botConfig?.pacing;
			const minDelay = pacing?.enabled ? Math.min(pacing.min_delay_ms ?? 300, 600) : 0;
			const start = performance.now();

			const response = await api.sendMessage(activeProfile.session_id, text);

			const elapsed = performance.now() - start;
			if (minDelay > elapsed) {
				await new Promise((r) => setTimeout(r, minDelay - elapsed));
			}

			// Replace optimistic user message with server-persisted turn + assistant reply
			const withoutTemp = activeProfile.messages.filter((m) => m.id !== optimisticUserMsg.id);
			activeProfile = {
				...activeProfile,
				title: response.title,
				messages: [...withoutTemp, response.user_message, response.assistant_message]
			};
			speakingId = response.assistant_message.id;
			lastReplyStatus = response.assistant_message.status ?? 'answered';
			const speakDuration = Math.min(
				Math.max(response.assistant_message.content.length * 18, 2800),
				5500
			);
			setTimeout(() => {
				if (speakingId === response.assistant_message.id) {
					speakingId = '';
				}
			}, speakDuration);
			await refreshProfiles();
		} catch (err) {
			errorBanner = err instanceof Error ? err.message : 'Failed to reach JangBot server.';
		} finally {
			isSending = false;
		}
	}

	onMount(async () => {
		try {
			botConfig = await api.getConfig();
			await refreshProfiles();

			const savedId = localStorage.getItem('jangbot_active_session');
			const match = savedId && profiles.find((p) => p.session_id === savedId);
			if (match) {
				await selectProfile(match.session_id);
			} else if (profiles.length > 0) {
				await selectProfile(profiles[0].session_id);
			} else {
				await createNewProfile();
			}
		} catch (err) {
			errorBanner =
				err instanceof Error
					? err.message
					: 'Could not connect to JangBot API. Make sure the Python server is running.';
		} finally {
			isLoading = false;
		}
	});
</script>

<svelte:window
	onkeydown={(e) => {
		if (resetConfirmOpen && e.key === 'Escape') resetConfirmOpen = false;
	}}
/>

<AppShell bind:open={sidebarOpen} href="/">
	{#snippet sidebar()}
		<Sidebar
			profiles={sidebarProfiles}
			activeId={activeProfile?.session_id ?? ''}
			connected={!!botConfig}
			backend={botConfig?.memory_backend ?? 'connecting…'}
			busy={isSending}
			onnew={createNewProfile}
			onselect={selectProfile}
			onrename={handleRenameProfile}
			ondelete={handleDeleteProfile}
		/>
	{/snippet}

	<ChatHeader
		title={activeProfile?.title ?? 'JangBot Chat'}
		thinking={isSending}
		mascotState={speakingId ? 'speaking' : undefined}
		memoryOpen={memoriesOpen}
		canReset={!!activeProfile && !isSending && (activeProfile.messages.length > 0)}
		ontogglememory={toggleMemoriesDrawer}
		onreset={() => {
			if (activeProfile && !isSending) resetConfirmOpen = true;
		}}
	/>

	{#if errorBanner}
		<ErrorBanner message={errorBanner} ondismiss={() => (errorBanner = null)} />
	{/if}

	<MessageFeed
		messages={feedMessages}
		thinking={isSending}
		connecting={isLoading}
		{speakingId}
		showAvatar={false}
	>
		{#snippet empty()}
			<StarterPrompts prompts={STARTER_PROMPTS} onpick={sendMessage} />
		{/snippet}
		{#snippet after()}
			{#if activeProfile && activeProfile.messages.length === 1 && !isSending}
				<StarterPrompts greeting={false} prompts={STARTER_PROMPTS} onpick={sendMessage} />
			{/if}
		{/snippet}
	</MessageFeed>

	<Composer
		bind:value={inputText}
		disabled={isLoading || !activeProfile}
		busy={isSending}
		onsend={sendMessage}
	/>
</AppShell>

<DanbiStage
	pose={stagePose}
	speaking={!!speakingId}
	thinking={isSending}
	hasError={!!errorBanner}
	messageCount={feedMessages.length}
/>

{#if memoriesOpen}
	<div
		class="jb jb-modal-backdrop"
		role="presentation"
		onclick={() => (memoriesOpen = false)}
	>
		<div
			class="jb-memory-modal"
			role="dialog"
			aria-modal="true"
			aria-label="Stored memories"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<MemoryDrawer memories={memoryStrings} onclose={() => (memoriesOpen = false)} />
		</div>
	</div>
{/if}

{#if resetConfirmOpen}
	<div
		class="jb jb-modal-backdrop"
		role="presentation"
		onclick={() => (resetConfirmOpen = false)}
	>
		<div
			class="jb-modal"
			role="dialog"
			aria-modal="true"
			aria-labelledby="reset-dialog-title"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<div class="jb-modal__head">
				<span class="jb-modal__icon"><Icon name="rotateCcw" size={18} /></span>
				<h2 id="reset-dialog-title" class="jb-modal__title">Reset this chat?</h2>
			</div>
			<p class="jb-modal__body">
				This will clear all messages and long-term memories stored for
				<strong>{activeProfile?.title ?? 'this profile'}</strong>. This action cannot be undone.
			</p>
			<div class="jb-modal__actions">
				<Button variant="ghost" label="Cancel" onclick={() => (resetConfirmOpen = false)} />
				<Button
					variant="primary"
					class="jb-modal__confirm"
					icon="rotateCcw"
					label="Reset chat"
					onclick={confirmResetProfile}
				/>
			</div>
		</div>
	</div>
{/if}

<style>
	.jb-modal-backdrop {
		position: fixed;
		inset: 0;
		z-index: calc(var(--z-slideover) + 10);
		background: var(--overlay-backdrop);
		display: grid;
		place-items: center;
		padding: var(--space-4);
		animation: jb-fade-in 0.15s ease-out;
	}

	.jb-memory-modal {
		width: min(480px, 100%);
		animation: jb-modal-in 0.18s cubic-bezier(0.22, 0.8, 0.24, 1);
	}

	.jb-memory-modal :global(.jb-drawer) {
		margin: 0 !important;
		border-radius: var(--radius-lg);
	}

	.jb-memory-modal :global(.jb-drawer__body) {
		max-height: min(360px, 60dvh);
	}

	.jb-modal {
		width: min(400px, 100%);
		background: var(--bg-elevated);
		border: 1.5px solid var(--border-ink);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-drawer);
		padding: var(--space-5);
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		animation: jb-modal-in 0.18s cubic-bezier(0.22, 0.8, 0.24, 1);
	}

	.jb-modal__head {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}

	.jb-modal__icon {
		width: 34px;
		height: 34px;
		border-radius: var(--radius-sm);
		background: var(--danger-soft);
		color: var(--danger);
		display: grid;
		place-items: center;
		flex: none;
	}

	.jb-modal__title {
		margin: 0;
		font-size: 17px;
		line-height: 24px;
		font-weight: 700;
		color: var(--text-primary);
	}

	.jb-modal__body {
		margin: 0;
		font-size: 14px;
		line-height: 20px;
		color: var(--text-secondary);
	}

	.jb-modal__actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--space-2);
		margin-top: var(--space-2);
	}

	:global(.jb-modal__confirm) {
		background: var(--danger) !important;
		color: #ffffff !important;
	}

	@keyframes jb-fade-in {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	@keyframes jb-modal-in {
		from { opacity: 0; transform: translateY(6px) scale(0.98); }
		to { opacity: 1; transform: none; }
	}

	@media (prefers-reduced-motion: reduce) {
		.jb-modal-backdrop,
		.jb-memory-modal,
		.jb-modal {
			animation: none;
		}
	}
</style>
