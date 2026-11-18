<script>
  /**
   * JangBot logo: amber tile with the janggu hourglass in ink + the wordmark.
   * @type {{ href?: string, word?: boolean }}
   */
  let { href, word = true } = $props();
</script>

{#snippet inner()}
  <svg class="jb-logo__mark" viewBox="0 0 32 32" aria-hidden="true" focusable="false">
    <rect class="lg-tile" width="32" height="32" rx="9" />
    <ellipse class="lg-ink" cx="16" cy="8.6" rx="8.4" ry="2.6" />
    <ellipse class="lg-ink" cx="16" cy="23.4" rx="8.4" ry="2.6" />
    <path class="lg-ink" d="M7.6 9 C8.6 13.6 13.4 14.4 14.6 16 C13.4 17.6 8.6 18.4 7.6 23 M24.4 9 C23.4 13.6 18.6 14.4 17.4 16 C18.6 17.6 23.4 18.4 24.4 23" />
    <rect class="lg-dot" x="13.4" y="15" width="5.2" height="2" rx="1" />
  </svg>
  {#if word}<span class="jb-logo__word">JangBot <small lang="ko">장봇</small></span>{/if}
{/snippet}

{#if href}
  <a class="jb-logo" {href} aria-label="JangBot home">{@render inner()}</a>
{:else}
  <span class="jb-logo" aria-label="JangBot">{@render inner()}</span>
{/if}
