<script>
  // Reference wiring for the chat page. Replace the fake `ask()` with your backend call.
  import { onMount } from 'svelte';
  import { AppShell, Sidebar, ChatHeader, MemoryDrawer, ErrorBanner, MessageFeed, StarterPrompts, Composer, initTheme } from './index.js';

  /** @type {import('./types').Profile[]} */
  let profiles = $state([
    { id: 'p1', title: 'Playing techniques', lastMessage: 'Use the yeolchae on the right head.' },
    { id: 'p2', title: 'Janggu rhythms', lastMessage: 'Gutgeori is a 12/8 rhythm cycle…' },
    { id: 'p3', title: 'New chat', lastMessage: '' }
  ]);
  let activeId = $state('p1');
  /** @type {Record<string, import('./types').Message[]>} */
  let chats = $state({
    p1: [
      { id: 'm1', role: 'user', content: 'How do I hold the yeolchae?' },
      { id: 'm2', role: 'assistant', content: 'Hold the yeolchae lightly between thumb and index finger, about a third of the way up, and let it bounce off the right head.',
        citations: [{ id: 'JG-022', detail: 'Players strike the right head with a thin bamboo stick called the yeolchae.', publisher: 'Encyclopedia of Korean Culture', tier: 'Tier 2', tierLevel: 2, url: '#' }] }
    ],
    p2: [], p3: []
  });
  let memories = $state(['Beginner learning janggu at a university club.', 'Prefers short answers with examples.']);
  let drawerOpen = $state(false);
  let memoryOpen = $state(false);
  let thinking = $state(false);
  let speakingId = $state('');
  let connected = $state(true);
  let error = $state('');
  let draft = $state('');

  let active = $derived(profiles.find((p) => p.id === activeId));
  let messages = $derived(chats[activeId] ?? []);

  onMount(initTheme);

  async function ask(/** @type {string} */ text) {
    error = '';
    chats[activeId].push({ id: crypto.randomUUID(), role: 'user', content: text });
    thinking = true;
    await new Promise((r) => setTimeout(r, 900));
    thinking = false;
    const id = crypto.randomUUID();
    chats[activeId].push({ id, role: 'assistant', content: 'The janggu’s left head gives a deep tone and the right head a sharp one.' });
    speakingId = id;
    setTimeout(() => (speakingId = ''), 1200);
  }
  function newChat() {
    const id = crypto.randomUUID();
    profiles.unshift({ id, title: 'New chat', lastMessage: '' });
    chats[id] = [];
    activeId = id;
    drawerOpen = false;
  }
</script>

<AppShell bind:open={drawerOpen}>
  {#snippet sidebar()}
    <Sidebar {profiles} {activeId} {connected} backend="mem0" busy={thinking}
      onnew={newChat}
      onselect={(id) => { activeId = id; drawerOpen = false; }}
      onrename={(id, title) => { const p = profiles.find((x) => x.id === id); if (p) p.title = title; }}
      ondelete={(id) => { if (confirm('Delete this chat?')) profiles = profiles.filter((p) => p.id !== id); }} />
  {/snippet}

  <ChatHeader title={active?.title ?? 'Danbi'} {thinking} mascotState={speakingId ? 'speaking' : undefined} {memoryOpen}
    canReset={messages.length > 0}
    ontogglememory={() => (memoryOpen = !memoryOpen)}
    onreset={() => { if (confirm('Reset this conversation?')) chats[activeId] = []; }} />
  {#if memoryOpen}<MemoryDrawer {memories} onclose={() => (memoryOpen = false)} />{/if}
  {#if error}<ErrorBanner message={error} ondismiss={() => (error = '')} />{/if}
  <MessageFeed {messages} {thinking} connecting={!connected} {speakingId}>
    {#snippet empty()}<StarterPrompts onpick={ask} />{/snippet}
  </MessageFeed>
  <Composer bind:value={draft} disabled={!connected} busy={thinking} onsend={ask} />
</AppShell>
