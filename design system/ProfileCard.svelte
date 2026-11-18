<script>
  import { tick } from 'svelte';
  import IconButton from './IconButton.svelte';
  import Icon from './Icon.svelte';

  /**
   * @type {{ profile: import('./types').Profile, active?: boolean, onselect?: (id: string) => void,
   *   onrename?: (id: string, title: string) => void, ondelete?: (id: string) => void }}
   */
  let { profile, active = false, onselect, onrename, ondelete } = $props();

  let editing = $state(false);
  let draft = $state('');
  /** @type {HTMLInputElement | undefined} */
  let input = $state();

  async function startEdit(/** @type {Event} */ e) {
    e.stopPropagation();
    draft = profile.title;
    editing = true;
    await tick();
    input?.focus();
    input?.select();
  }
  function save() {
    const t = draft.trim();
    if (t && t !== profile.title) onrename?.(profile.id, t);
    editing = false;
  }
  function onInputKey(/** @type {KeyboardEvent} */ e) {
    if (e.key === 'Enter') { e.preventDefault(); save(); }
    else if (e.key === 'Escape') { e.preventDefault(); editing = false; }
  }
  function onCardKey(/** @type {KeyboardEvent} */ e) {
    if (e.target !== e.currentTarget) return;
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onselect?.(profile.id); }
  }
</script>

{#if editing}
  <div class="jb-profile is-editing">
    <input bind:this={input} bind:value={draft} class="jb-input" aria-label="Chat name" onkeydown={onInputKey} />
    <IconButton icon="check" label="Save name" variant="confirm" size="sm" onclick={save} />
    <IconButton icon="x" label="Cancel rename" size="sm" onclick={() => (editing = false)} />
  </div>
{:else}
  <div class="jb-profile" class:is-active={active} role="button" tabindex="0" aria-current={active ? 'true' : undefined}
    onclick={() => onselect?.(profile.id)} onkeydown={onCardKey}>
    <span class="jb-profile__icon"><Icon name="messageCircle" size={15} /></span>
    <div class="jb-profile__text">
      <span class="jb-profile__title">{profile.title}</span>
      <span class="jb-profile__preview" class:is-empty={!profile.lastMessage}>{profile.lastMessage || 'Empty conversation'}</span>
    </div>
    <div class="jb-profile__actions">
      <IconButton icon="pencil" label="Rename {profile.title}" size="sm" iconSize={15} onclick={startEdit} />
      <IconButton icon="trash" label="Delete {profile.title}" variant="danger" size="sm" iconSize={15}
        onclick={(/** @type {Event} */ e) => { e.stopPropagation(); ondelete?.(profile.id); }} />
    </div>
  </div>
{/if}
