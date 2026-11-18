# JangBot · Danbi — Svelte 5 components

Drop this `jangbot/` folder into `src/lib/` of your SvelteKit app. The styles (`styles/tokens.css`, `styles/jangbot.css`) and fonts (`styles/fonts/`) are already in place.

Steps 1–2 of the design system's Svelte guide are done for you. Continue from step 3:

1. Import the styles once and start the theme in `src/routes/+layout.svelte`:

```svelte
<script>
  import '$lib/jangbot/styles/tokens.css';
  import '$lib/jangbot/styles/jangbot.css';
  import { onMount } from 'svelte';
  import { initTheme } from '$lib/jangbot';
  let { children } = $props();
  onMount(initTheme);
</script>

{@render children()}
```

2. To avoid a flash of the wrong theme before hydration, add this inline script to `src/app.html`, inside `<head>`:

```html
<script>
  try {
    document.documentElement.dataset.theme = localStorage.getItem('jangbot-theme') || 'dark';
  } catch (e) {}
</script>
```

## Components

| Component | Key props | Events |
| --- | --- | --- |
| `AppShell` | `bind:collapsed` (desktop panel, remembered), `bind:open` (tablet/mobile drawer), wraps itself in `.jb-app` and picks desktop/tablet/mobile from its own width, `rain` (default `true`), `href` (logo link), snippets `sidebar` + children | renders the brand bar; Ctrl/⌘+B toggles; Esc and backdrop close the drawer |
| `BrandBar` | `panelOpen`, `href` | `ontoggle` (used inside `AppShell`) |
| `Logo` | `href`, `word` | — |
| `Sidebar` | `profiles`, `activeId`, `connected`, `backend`, `busy` | `onnew`, `onselect(id)`, `onrename(id, title)`, `ondelete(id)` |
| `ProfileCard` | `profile`, `active` | `onselect`, `onrename`, `ondelete` (rename is inline: Enter saves, Esc cancels) |
| `ChatHeader` | `title`, `thinking`, `mascotState`, `memoryOpen`, `canReset` | `ontogglememory`, `onreset` (the panel toggle lives in the brand bar) |
| `MemoryDrawer` | `memories: string[]` | `onclose` (also on Esc) |
| `ErrorBanner` | `message` | `ondismiss` |
| `MessageFeed` | `messages`, `thinking`, `connecting`, `speakingId`, snippet `empty` | auto-scrolls while pinned to the bottom |
| `MessageBubble` | `role`, `content`, `citations`, `mascotState`, optional children snippet (e.g. rendered markdown) | — |
| `Citations` | `citations`, `bind:open` | — |
| `StarterPrompts` | `prompts`, `greeting` | `onpick(prompt)` |
| `Composer` | `bind:value`, `disabled`, `busy`, `placeholder` | `onsend(text)` (Enter sends, Shift+Enter adds a line, IME-safe) |
| `Mascot` | `size`, `state` (`idle`, `thinking` or `speaking`), `framed`, `label` | — |
| `Button` | `variant` (`primary`, `ghost`, `ink` or `outline`), `icon`, `label`, `block`, `hideLabelOnMobile` | `onclick` and other native attributes pass through |
| `IconButton` | `icon`, `label` (required, becomes the aria-label), `variant` (`default`, `danger` or `confirm`), `size` | native |
| `ThemeToggle` | — | toggles Rainy night and Misty dawn, and saves the choice |
| `Scene` | `name` (`hanokNight`, `eavesRain`, `palaceGate`, `pagodaCourtyard`, `mountainMist`, `signboard`, `lantern`, `windBell` or `giwaBand`), `still` | — |
| `Danbi` | `pose` (`drumming`, `sticks`, `lantern`, `umbrella`, `wave`, `bow`, `read`, `sleep` or `sad`), `size`, `still` | — |
| `RainLayer` | — | quiet background rain, included by `AppShell` (`rain={false}` to remove) |
| `Landing` | `mascotSrc` (final art replaces the placeholder), `mascotAlt` | `onstart` |

Data shapes (`Profile`, `Message`, `Citation`, `MascotState`) are in `types.d.ts`.

## Theme

- `data-theme="dark"` (Rainy night, the default) or `"light"` (Misty dawn) on `<html>` switches every token, including the scenes.
- `initTheme()` applies the saved choice, or Rainy night when nothing is saved.
- `setTheme('dark')` and `toggleTheme()` change the theme and save the choice.
- The reactive `theme.current` holds the active theme.
- `ThemeToggle` sits in the sidebar footer.

## Wiring example

`ChatExample.svelte` wires the whole chat page together with fake data. Copy it into `+page.svelte` and replace `ask()` with your backend call. Two rules it follows:

- Set `thinking` from send until the first token arrives.
- Set `speakingId` to the reply's id while it streams. Danbi's header and bubble avatars follow both.

## Art

`art.js` holds the scene and pose drawings, from the same source as `components/bundle.js`. `<Scene>` and `<Danbi>` render them with `{@html}`. The output is static SVG with no user input, so this is safe. All motion is CSS in `jangbot.css`, and it stops under reduced motion or with `still`.
