<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { Danbi } from '#lib/jangbot/index.js';

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
		messageCount?: number;
	}

	let {
		pose = 'wave',
		speaking = false,
		thinking = false,
		hasError = false,
		messageCount = 0
	}: Props = $props();

	const POSE_META: Record<DanbiPose, { title: string; ko: string }> = {
		drumming: { title: 'Speaking', ko: '장구 이야기' },
		read: { title: 'Thinking', ko: '찾아보는 중' },
		wave: { title: 'Hello!', ko: '안녕!' },
		lantern: { title: 'Listening', ko: '듣고 있어요' },
		bow: { title: 'Clarifying', ko: '안내' },
		sad: { title: 'Connection issue', ko: '잠시만요' },
		umbrella: { title: 'Rainy walk', ko: '우산 아래' },
		sleep: { title: 'Resting', ko: '쿨쿨' }
	};

	let meta = $derived(POSE_META[pose] ?? POSE_META.lantern);
	let moodClass = $derived(
		hasError ? 'is-error' : thinking ? 'is-thinking' : speaking ? 'is-speaking' : 'is-idle'
	);

	// Autonomous floating + draggable position
	let pos = $state<{ x: number; y: number } | null>(null);
	let tilt = $state(0);
	let dragging = $state(false);
	let dragOffset = { x: 0, y: 0 };
	let pauseRoamUntil = 0;
	let danbiEl: HTMLElement | undefined = $state();

	// Live SVG speech tether from Danbi to the latest assistant bubble
	let tether = $state<{
		path: string;
		tailPath: string;
		dots: Array<{ cx: number; cy: number; r: number }>;
		visible: boolean;
	}>({ path: '', tailPath: '', dots: [], visible: false });

	function getBounds() {
		const w = danbiEl?.offsetWidth || 240;
		const h = danbiEl?.offsetHeight || 260;
		const sidebar = document.querySelector('.jb-shell:not(.is-collapsed) .jb-sidebar');
		const isDesktop = window.innerWidth >= 1024;
		const minX = isDesktop && sidebar ? Math.min(304, window.innerWidth * 0.3) : 10;
		const maxX = Math.max(minX + 10, window.innerWidth - w - 18);
		const minY = 74;
		const maxY = Math.max(minY + 10, window.innerHeight - h - 102);
		return { minX, maxX, minY, maxY, w, h };
	}

	function clampPos(x: number, y: number) {
		const b = getBounds();
		return {
			x: Math.max(b.minX, Math.min(b.maxX, x)),
			y: Math.max(b.minY, Math.min(b.maxY, y))
		};
	}

	function pickRoamWaypoint(): { x: number; y: number } {
		const b = getBounds();
		const bubbles = document.querySelectorAll('.jb-bubble--assistant');
		const latest = bubbles.length ? (bubbles[bubbles.length - 1] as HTMLElement) : null;

		// When speaking or thinking, gently drift near the latest assistant bubble on the open side
		if ((speaking || thinking) && latest) {
			const r = latest.getBoundingClientRect();
			const spaceRight = b.maxX - (r.right + 20);
			const spaceLeft = r.left - 20 - b.minX;
			const targetY = r.top + Math.min(r.height * 0.35, 70) - b.h * 0.35;

			if (spaceRight > 40) {
				return clampPos(r.right + 28 + Math.random() * Math.min(90, spaceRight), targetY);
			}
			if (spaceLeft > 40) {
				return clampPos(r.left - b.w - 24 - Math.random() * Math.min(60, spaceLeft), targetY);
			}
		}

		// Calmly roam around the open chat canvas (favoring spacious edges on desktop)
		const spanX = b.maxX - b.minX;
		const spanY = b.maxY - b.minY;
		let tx: number;
		if (window.innerWidth >= 1024 && spanX > 260) {
			// 70% right side (open area), 30% left/mid drift for lively presence
			const pickRight = Math.random() < 0.7;
			tx = pickRight
				? b.minX + spanX * (0.68 + Math.random() * 0.32)
				: b.minX + spanX * (Math.random() * 0.25);
		} else {
			tx = b.minX + Math.random() * spanX;
		}
		const ty = b.minY + Math.random() * spanY;
		return clampPos(tx, ty);
	}

	function computeTether() {
		if (typeof window === 'undefined' || !danbiEl) {
			tether = { path: '', tailPath: '', dots: [], visible: false };
			return;
		}

		const bubbles = document.querySelectorAll('.jb-bubble--assistant');
		const target = bubbles.length ? (bubbles[bubbles.length - 1] as HTMLElement) : null;
		if (!target) {
			tether = { path: '', tailPath: '', dots: [], visible: false };
			return;
		}

		const b = target.getBoundingClientRect();
		const d = danbiEl.getBoundingClientRect();

		if (b.bottom < 70 || b.top > window.innerHeight - 60 || d.width === 0) {
			tether = { path: '', tailPath: '', dots: [], visible: false };
			return;
		}

		const dCx = d.left + d.width * 0.5;
		const dCy = d.top + d.height * 0.44;
		const bCy = Math.max(
			78,
			Math.min(window.innerHeight - 96, b.top + Math.min(b.height * 0.5, 90))
		);

		let endX: number;
		let endY: number;
		let startX: number;
		let startY: number;

		if (dCx > b.right + 16) {
			endX = b.right + 2;
			endY = bCy;
			startX = d.left + d.width * 0.16;
			startY = dCy;
		} else if (dCx < b.left - 16) {
			endX = b.left - 2;
			endY = bCy;
			startX = d.right - d.width * 0.16;
			startY = dCy;
		} else if (dCy > b.bottom) {
			endX = Math.max(b.left + 24, Math.min(b.right - 24, dCx));
			endY = b.bottom + 2;
			startX = dCx;
			startY = d.top + d.height * 0.14;
		} else {
			endX = Math.max(b.left + 24, Math.min(b.right - 24, dCx));
			endY = b.top - 2;
			startX = dCx;
			startY = d.bottom - d.height * 0.14;
		}

		const dx = endX - startX;
		const dy = endY - startY;
		const dist = Math.hypot(dx, dy);
		if (dist < 24) {
			tether = { path: '', tailPath: '', dots: [], visible: false };
			return;
		}

		const midX = (startX + endX) / 2;
		const midY = (startY + endY) / 2 - Math.min(36, dist * 0.14);

		const qPoint = (t: number) => {
			const mt = 1 - t;
			return {
				x: mt * mt * startX + 2 * mt * t * midX + t * t * endX,
				y: mt * mt * startY + 2 * mt * t * midY + t * t * endY
			};
		};

		const p1 = qPoint(0.22);
		const p2 = qPoint(0.5);
		const p3 = qPoint(0.78);

		const ang = Math.atan2(startY - endY, startX - endX);
		const tipLen = 13;
		const baseSpread = 0.45;
		const bx1 = endX + Math.cos(ang + baseSpread) * tipLen;
		const by1 = endY + Math.sin(ang + baseSpread) * tipLen;
		const bx2 = endX + Math.cos(ang - baseSpread) * tipLen;
		const by2 = endY + Math.sin(ang - baseSpread) * tipLen;

		tether = {
			path: `M ${startX.toFixed(1)} ${startY.toFixed(1)} Q ${midX.toFixed(1)} ${midY.toFixed(1)} ${endX.toFixed(1)} ${endY.toFixed(1)}`,
			tailPath: `M ${endX.toFixed(1)} ${endY.toFixed(1)} L ${bx1.toFixed(1)} ${by1.toFixed(1)} L ${bx2.toFixed(1)} ${by2.toFixed(1)} Z`,
			dots: [
				{ cx: p1.x, cy: p1.y, r: 4.5 },
				{ cx: p2.x, cy: p2.y, r: 6 },
				{ cx: p3.x, cy: p3.y, r: 4 }
			],
			visible: true
		};
	}

	function onPointerDown(e: PointerEvent) {
		if (!danbiEl) return;
		const rect = danbiEl.getBoundingClientRect();
		dragging = true;
		dragOffset = { x: e.clientX - rect.left, y: e.clientY - rect.top };
		pos = { x: rect.left, y: rect.top };
		tilt = 0;
		danbiEl.setPointerCapture(e.pointerId);
	}

	function onPointerMove(e: PointerEvent) {
		if (!dragging || !danbiEl) return;
		const next = clampPos(e.clientX - dragOffset.x, e.clientY - dragOffset.y);
		pos = next;
		computeTether();
	}

	function onPointerUp(e: PointerEvent) {
		if (!dragging || !danbiEl) return;
		dragging = false;
		pauseRoamUntil = performance.now() + 3500;
		try {
			danbiEl.releasePointerCapture(e.pointerId);
		} catch {}
		computeTether();
	}

	// Re-pick target gently whenever Danbi starts speaking or thinking
	let forceRetarget = false;
	$effect(() => {
		messageCount;
		pose;
		speaking;
		thinking;
		forceRetarget = true;
		tick().then(() => requestAnimationFrame(computeTether));
	});

	onMount(() => {
		const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		const initB = getBounds();
		let curX = initB.maxX - 12;
		let curY = initB.maxY - 10;
		let velX = 0;
		let velY = 0;
		let target = clampPos(curX, curY);
		let nextPickAt = performance.now() + 1800;
		pos = { x: curX, y: curY };

		let raf = 0;
		let lastT = performance.now();

		const step = (now: number) => {
			const dt = Math.min(0.05, (now - lastT) / 1000);
			lastT = now;

			if (!reducedMotion && !dragging) {
				if (pos) {
					curX = pos.x;
					curY = pos.y;
				}

				if (forceRetarget && now >= pauseRoamUntil) {
					forceRetarget = false;
					target = pickRoamWaypoint();
					nextPickAt = now + (speaking || thinking ? 3400 : 5200);
				} else if (now >= nextPickAt && now >= pauseRoamUntil) {
					target = pickRoamWaypoint();
					nextPickAt = now + 4500 + Math.random() * 3200;
				}

				// Soft spring-like drift toward waypoint + gentle sinusoidal float bob
				const bobY = Math.sin(now * 0.0018) * 10;
				const bobX = Math.cos(now * 0.0011) * 5;
				const dx = target.x + bobX - curX;
				const dy = target.y + bobY - curY;

				const stiffness = speaking || thinking ? 2.1 : 1.15;
				const damping = 0.86;
				velX = (velX + dx * stiffness * dt) * Math.pow(damping, dt * 60);
				velY = (velY + dy * stiffness * dt) * Math.pow(damping, dt * 60);

				// Cap max cruise speed so Danbi floats serenely
				const speed = Math.hypot(velX, velY);
				const maxSpeed = speaking || thinking ? 160 : 95;
				if (speed > maxSpeed) {
					velX = (velX / speed) * maxSpeed;
					velY = (velY / speed) * maxSpeed;
				}

				const clamped = clampPos(curX + velX * dt, curY + velY * dt);
				curX = clamped.x;
				curY = clamped.y;
				pos = { x: curX, y: curY };
				tilt = Math.max(-5, Math.min(5, velX * 0.045));
			} else if (dragging && pos) {
				curX = pos.x;
				curY = pos.y;
				velX = 0;
				velY = 0;
				target = { x: curX, y: curY };
			}

			computeTether();
			raf = requestAnimationFrame(step);
		};

		const onResize = () => {
			if (pos) {
				const c = clampPos(pos.x, pos.y);
				curX = c.x;
				curY = c.y;
				pos = c;
				target = clampPos(target.x, target.y);
			}
			computeTether();
		};

		window.addEventListener('resize', onResize, { passive: true });
		raf = requestAnimationFrame(step);

		return () => {
			cancelAnimationFrame(raf);
			window.removeEventListener('resize', onResize);
		};
	});
</script>

<!-- Dynamic speech connector pointing from Danbi to his latest chat bubble -->
{#if tether.visible}
	<svg class="jb-speech-tether {moodClass}" aria-hidden="true">
		<path class="jb-tether-line" d={tether.path} />
		<path class="jb-tether-tail" d={tether.tailPath} />
		{#each tether.dots as dot, idx}
			<circle
				class="jb-tether-dot"
				cx={dot.cx}
				cy={dot.cy}
				r={dot.r}
				style="animation-delay: {idx * 0.16}s"
			/>
		{/each}
	</svg>
{/if}

<!-- Massive always-on autonomously floating & draggable Danbi -->
<div
	bind:this={danbiEl}
	class="jb-danbi-float {moodClass}"
	class:is-dragging={dragging}
	style:transform={pos
		? `translate3d(${pos.x.toFixed(1)}px, ${pos.y.toFixed(1)}px, 0) rotate(${tilt.toFixed(2)}deg)`
		: undefined}
	role="img"
	aria-label="Danbi ({meta.title}) — drag to move"
	title="Drag Danbi anywhere on screen"
	onpointerdown={onPointerDown}
	onpointermove={onPointerMove}
	onpointerup={onPointerUp}
	onpointercancel={onPointerUp}
>
	<div class="jb-float-aura" aria-hidden="true"></div>

	<div class="jb-float-figure">
		{#key pose}
			<Danbi {pose} />
		{/key}
	</div>

	<div class="jb-float-pill">
		{#if speaking}
			<span class="jb-float-bars" aria-hidden="true">
				<span></span><span></span><span></span>
			</span>
		{:else}
			<span class="jb-float-dot" aria-hidden="true"></span>
		{/if}
		<b>{meta.title}</b>
		<span class="jb-float-ko" lang="ko">{meta.ko}</span>
	</div>
</div>

<style>
	.jb-speech-tether {
		position: fixed;
		inset: 0;
		width: 100vw;
		height: 100dvh;
		pointer-events: none;
		z-index: 7;
		overflow: visible;
	}

	.jb-tether-line {
		fill: none;
		stroke: color-mix(in srgb, var(--accent) 42%, var(--border-ink));
		stroke-width: 2;
		stroke-dasharray: 6 7;
		stroke-linecap: round;
		opacity: 0.55;
		transition: opacity 0.25s ease, stroke 0.25s ease;
	}

	.jb-speech-tether.is-speaking .jb-tether-line,
	.jb-speech-tether.is-thinking .jb-tether-line {
		stroke: var(--accent);
		opacity: 0.9;
		animation: jb-tether-flow 1.1s linear infinite;
	}

	.jb-tether-tail {
		fill: var(--bubble-assistant);
		stroke: color-mix(in srgb, var(--accent) 60%, var(--border-default));
		stroke-width: 1.4;
		opacity: 0.9;
	}

	.jb-tether-dot {
		fill: var(--accent);
		opacity: 0.45;
		transition: opacity 0.25s ease;
	}

	.jb-speech-tether.is-speaking .jb-tether-dot,
	.jb-speech-tether.is-thinking .jb-tether-dot {
		opacity: 0.92;
		animation: jb-tether-pop 0.9s ease-in-out infinite alternate;
	}

	.jb-danbi-float {
		position: fixed;
		left: 0;
		top: 0;
		z-index: 8;
		width: clamp(230px, 23vw, 320px);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
		cursor: grab;
		user-select: none;
		touch-action: none;
		will-change: transform;
		filter: drop-shadow(0 18px 34px rgba(0, 0, 0, 0.42));
		transition: filter 0.25s ease;
	}

	.jb-danbi-float.is-dragging {
		cursor: grabbing;
		filter: drop-shadow(0 24px 44px rgba(0, 0, 0, 0.55));
	}

	.jb-float-aura {
		position: absolute;
		inset: 8% 4%;
		border-radius: 50%;
		background: radial-gradient(
			circle,
			color-mix(in srgb, var(--accent) 28%, transparent) 0%,
			transparent 70%
		);
		pointer-events: none;
		opacity: 0.65;
		transition: transform 0.35s ease, opacity 0.35s ease;
	}

	.jb-danbi-float.is-speaking .jb-float-aura {
		opacity: 1;
		transform: scale(1.14);
	}

	.jb-danbi-float.is-thinking .jb-float-aura {
		opacity: 0.9;
		transform: scale(1.06);
	}

	.jb-float-figure {
		position: relative;
		z-index: 1;
		width: 100%;
		pointer-events: none;
	}

	.jb-float-pill {
		position: relative;
		z-index: 1;
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 5px 12px;
		border-radius: var(--radius-pill);
		background: color-mix(in srgb, var(--bg-elevated) 86%, transparent);
		backdrop-filter: blur(8px);
		border: 1px solid var(--border-default);
		font-size: 12px;
		line-height: 16px;
		color: var(--text-primary);
		pointer-events: none;
	}

	.jb-danbi-float.is-speaking .jb-float-pill {
		border-color: var(--accent);
		background: color-mix(in srgb, var(--bg-selected) 92%, transparent);
	}

	.jb-danbi-float.is-thinking .jb-float-pill {
		border-color: var(--highlight);
	}

	.jb-float-ko {
		color: var(--text-secondary);
		font-weight: 500;
	}

	.jb-float-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--status-online);
		flex: none;
	}

	.jb-danbi-float.is-thinking .jb-float-dot {
		background: var(--highlight);
		animation: jb-float-pulse 1s ease-in-out infinite;
	}

	.jb-danbi-float.is-error .jb-float-dot {
		background: var(--danger);
	}

	.jb-float-bars {
		display: inline-flex;
		align-items: flex-end;
		gap: 2px;
		height: 12px;
	}

	.jb-float-bars span {
		width: 2.5px;
		height: 4px;
		border-radius: 2px;
		background: var(--accent);
		animation: jb-float-eq 0.65s ease-in-out infinite alternate;
	}

	.jb-float-bars span:nth-child(2) {
		animation-delay: 0.16s;
	}

	.jb-float-bars span:nth-child(3) {
		animation-delay: 0.32s;
	}

	@keyframes jb-tether-flow {
		from {
			stroke-dashoffset: 0;
		}
		to {
			stroke-dashoffset: 26;
		}
	}

	@keyframes jb-tether-pop {
		from {
			opacity: 0.45;
		}
		to {
			opacity: 1;
		}
	}

	@keyframes jb-float-eq {
		from {
			height: 4px;
		}
		to {
			height: 12px;
		}
	}

	@keyframes jb-float-pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.35;
		}
	}

	@media (max-width: 1023px) {
		.jb-danbi-float {
			width: 175px;
		}
	}

	@media (max-width: 767px) {
		.jb-danbi-float {
			width: 126px;
		}

		.jb-float-pill {
			padding: 3px 9px;
			font-size: 11px;
		}
	}
</style>
