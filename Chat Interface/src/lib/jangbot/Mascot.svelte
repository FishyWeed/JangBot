<script>
  /**
   * Danbi, the janggu mascot.
   * @type {{ size?: number, state?: 'idle' | 'thinking' | 'speaking', framed?: boolean, label?: string }}
   */
  let { size = 40, state = 'idle', framed = true, label } = $props();
  let aria = $derived(label ?? `Danbi, ${state}`);
</script>

{#snippet figure()}
  <svg class="jb-danbi" viewBox="0 0 64 64" aria-hidden="true" focusable="false">
    <g class="dn-figure">
      <ellipse class="dn-hoop" cx="32" cy="52.5" rx="21.5" ry="6.5" />
      <path class="dn-body" d="M11.5 14.5 C13 25.5 23.5 28.5 26.5 33.5 C23.5 38.5 14 41.5 12.5 51.5 L51.5 51.5 C50 41.5 40.5 38.5 37.5 33.5 C40.5 28.5 51 25.5 52.5 14.5 Z" />
      <path class="dn-shade" d="M44.5 23.5 C47.5 21.5 50 18.5 51 15.5 L52.5 15 C51.5 22 47 25.5 41.5 28.5 Z" />
      <path class="dn-shade" d="M42 41.5 C46 43.5 49.5 46.5 50.5 50.5 L46.5 50.5 C45.5 47 43.5 44 40 42 Z" />
      <path class="dn-cord" d="M17.5 49 L29 37.5 M25 50.5 L30.5 37.5 M39 50.5 L33.5 37.5 M46.5 49 L35 37.5" />
      <rect class="dn-waist" x="25" y="31" width="14" height="5.5" rx="2.2" />
      <ellipse class="dn-hoop" cx="32" cy="13.5" rx="22" ry="7" />
      <ellipse class="dn-head" cx="32" cy="12.6" rx="16.5" ry="4.2" />
      <g class="dn-face" transform="translate(0 1.9)">
        <ellipse class="dn-blush" cx="19" cy="24.6" rx="3.4" ry="2" />
        <ellipse class="dn-blush" cx="45" cy="24.6" rx="3.4" ry="2" />
        <g class="dn-eyes">
          <ellipse class="dn-eye" cx="24.6" cy="21.2" rx="2.7" ry="3.3" />
          <ellipse class="dn-eye" cx="39.4" cy="21.2" rx="2.7" ry="3.3" />
          <circle class="dn-glint" cx="25.6" cy="19.9" r="1" />
          <circle class="dn-glint" cx="40.4" cy="19.9" r="1" />
        </g>
        <path class="dn-mouth dn-mouth-smile" d="M28.6 25 Q32 28.8 35.4 25" />
        <path class="dn-mouth dn-mouth-open" d="M28.4 24.6 Q32 31.4 35.6 24.6 Z" />
        <path class="dn-mouth dn-mouth-think" d="M29.8 26.6 Q31.2 25.4 32.6 26.4 Q33.6 27.2 34.6 26" />
      </g>
    </g>
  </svg>
{/snippet}

{#if framed}
  <span class="jb-avatar jb-mascot" data-state={state} role="img" aria-label={aria} style:--avatar-size="{size}px">{@render figure()}</span>
{:else}
  <span class="jb-mascot" data-state={state} role="img" aria-label={aria} style:width="{size}px" style:height="{size}px">{@render figure()}</span>
{/if}
