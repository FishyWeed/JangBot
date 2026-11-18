<script>
  import Mascot from './Mascot.svelte';
  import Icon from './Icon.svelte';
  import ProfileCard from './ProfileCard.svelte';
  import StatusIndicator from './StatusIndicator.svelte';
  import ThemeToggle from './ThemeToggle.svelte';

  /**
   * The panel under the brand bar: New Chat, chat profiles, and the Danbi card (status + theme).
   * @type {{ profiles?: import('./types').Profile[], activeId?: string, connected?: boolean, backend?: string, busy?: boolean,
   *   onnew?: () => void, onselect?: (id: string) => void, onrename?: (id: string, title: string) => void, ondelete?: (id: string) => void }}
   */
  let { profiles = [], activeId, connected = false, backend, busy = false, onnew, onselect, onrename, ondelete } = $props();
</script>

<aside class="jb-sidebar" id="jb-sidebar" aria-label="Chat profiles">
  <div class="jb-sidebar__inner">
    <div class="jb-sidebar__new">
      <button type="button" class="jb-newchat" disabled={busy || !connected} onclick={onnew}>
        <span class="jb-newchat__plus"><Icon name="plus" size={16} /></span>New Chat<span class="jb-newchat__ko" lang="ko">새 대화</span>
      </button>
    </div>

    <div class="jb-sidebar__section">
      <span class="jb-label">Chat profiles <span class="jb-ko" lang="ko">· 대화 목록</span></span>
      <span class="jb-count">{profiles.length}</span>
    </div>

    <nav class="jb-sidebar__list">
      {#each profiles as profile (profile.id)}
        <ProfileCard {profile} active={profile.id === activeId} {onselect} {onrename} {ondelete} />
      {:else}
        <div class="jb-sidebar__empty">No chats yet. Start one above.</div>
      {/each}
    </nav>

    <div class="jb-sidebar__foot">
      <div class="jb-danbicard">
        <Mascot size={36} state={busy ? 'thinking' : 'idle'} />
        <div class="jb-danbicard__text">
          <span class="jb-danbicard__name">Danbi <small lang="ko">단비</small></span>
          <span class="jb-danbicard__sub">Janggu Expert System</span>
          <StatusIndicator {connected} {backend} />
        </div>
        <ThemeToggle />
      </div>
    </div>
  </div>
</aside>
