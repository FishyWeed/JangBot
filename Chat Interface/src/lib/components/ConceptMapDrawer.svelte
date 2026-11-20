<script lang="ts">
	import { Icon, IconButton, Button } from '#lib/jangbot/index.js';
	import { api } from '../api';
	import type {
		ConceptNode,
		ConceptNodeDetails,
		SemanticGraphOverview,
		SemanticPathResult
	} from '../types';

	interface Props {
		open?: boolean;
		busy?: boolean;
		onask: (prompt: string) => void;
		onclose: () => void;
	}

	let { open = false, busy = false, onask, onclose }: Props = $props();

	let tab = $state<'explore' | 'path'>('explore');
	let loading = $state(false);
	let errorMsg = $state<string | null>(null);
	let graph = $state<SemanticGraphOverview | null>(null);
	let selectedId = $state('ullimtong');
	let nodeDetails = $state<ConceptNodeDetails | null>(null);
	let searchText = $state('');
	let typeFilter = $state('all');

	// Path finder state
	let fromConcept = $state('acoustic_choke');
	let toConcept = $state('paulownia_coreana');
	let pathLoading = $state(false);
	let pathResult = $state<SemanticPathResult | null>(null);

	const TYPE_LABELS: Record<string, string> = {
		all: 'All',
		instrument: 'Instruments',
		component: 'Parts',
		material: 'Materials',
		implement: 'Sticks',
		technique_stroke: 'Strokes & Craft',
		rhythm: 'Rhythms',
		genre_tradition: 'Traditions',
		acoustic_concept: 'Acoustics',
		historical_record: 'Records',
		person_institution_tech: 'People & Science'
	};

	const PATH_PRESETS = [
		{ label: 'Choke → Paulownia', from: 'acoustic_choke', to: 'paulownia_coreana' },
		{ label: 'Idakka → UNESCO', from: 'idakka', to: 'unesco_nongak' },
		{ label: 'King Sejong → EBNF', from: 'king_sejong', to: 'jeongganbo_ebnf' },
		{ label: 'Byeonjuk → Bamboo', from: 'byeonjuk', to: 'bamboo' }
	];

	let filteredNodes = $derived<ConceptNode[]>(
		(graph?.nodes ?? []).filter((n) => {
			if (typeFilter !== 'all' && n.node_type !== typeFilter) return false;
			const q = searchText.trim().toLowerCase();
			if (!q) return true;
			return (
				n.id.toLowerCase().includes(q) ||
				n.label.toLowerCase().includes(q) ||
				(n.korean_name ?? '').toLowerCase().includes(q) ||
				n.aliases.some((a) => a.toLowerCase().includes(q))
			);
		})
	);

	// Deduplicated radial neighbors for local SVG map (max 10 around center)
	let radialNeighbors = $derived.by(() => {
		if (!nodeDetails) return [];
		const seen = new Set<string>();
		const items: Array<{
			id: string;
			label: string;
			predicate: string;
			direction: 'outgoing' | 'incoming';
			fact_id: string;
			x: number;
			y: number;
			lx: number;
			ly: number;
		}> = [];
		const allRels = [...nodeDetails.outgoing, ...nodeDetails.incoming];
		const uniqueRels = allRels.filter((r) => {
			if (seen.has(r.neighbor_id)) return false;
			seen.add(r.neighbor_id);
			return true;
		});
		const capped = uniqueRels.slice(0, 10);
		const cx = 190;
		const cy = 128;
		const rx = 132;
		const ry = 88;
		capped.forEach((rel, idx) => {
			const angle = (2 * Math.PI * idx) / Math.max(capped.length, 1) - Math.PI / 2;
			const x = cx + rx * Math.cos(angle);
			const y = cy + ry * Math.sin(angle);
			const lx = cx + rx * 0.52 * Math.cos(angle);
			const ly = cy + ry * 0.52 * Math.sin(angle);
			items.push({
				id: rel.neighbor_id,
				label: rel.neighbor_label,
				predicate: rel.predicate.replace(/_/g, ' '),
				direction: rel.direction,
				fact_id: rel.fact_id,
				x,
				y,
				lx,
				ly
			});
		});
		return items;
	});

	async function ensureLoaded() {
		if (graph) return;
		loading = true;
		errorMsg = null;
		try {
			graph = await api.getGraph();
			await selectNode(selectedId);
		} catch (err) {
			errorMsg = err instanceof Error ? err.message : 'Failed to load semantic graph.';
		} finally {
			loading = false;
		}
	}

	async function selectNode(conceptId: string) {
		selectedId = conceptId;
		errorMsg = null;
		try {
			nodeDetails = await api.getGraphNode(conceptId);
		} catch (err) {
			errorMsg = err instanceof Error ? err.message : 'Failed to load concept node.';
		}
	}

	async function runPathFinder(src = fromConcept, tgt = toConcept) {
		fromConcept = src;
		toConcept = tgt;
		pathLoading = true;
		errorMsg = null;
		try {
			pathResult = await api.getGraphPath(src, tgt, 5);
		} catch (err) {
			errorMsg = err instanceof Error ? err.message : 'Could not trace path between concepts.';
			pathResult = null;
		} finally {
			pathLoading = false;
		}
	}

	$effect(() => {
		if (open) {
			ensureLoaded();
		}
	});

	function shortLabel(text: string, max = 18): string {
		return text.length > max ? `${text.slice(0, max - 1)}…` : text;
	}
</script>

{#if open}
	<div class="jb jb-map-backdrop" aria-hidden="true" onclick={onclose}></div>
{/if}

<aside
	class="jb jb-map-panel"
	class:is-open={open}
	aria-label="Semantic Concept Map"
	aria-hidden={!open}
>
	<div class="jb-map-head">
		<div class="jb-map-heading">
			<span class="jb-map-icon" aria-hidden="true"><Icon name="network" size={16} /></span>
			<div>
				<h2 class="jb-map-title">Concept Map</h2>
				<span class="jb-map-sub">
					{#if graph}
						{graph.stats.total_nodes} verified concepts · {graph.stats.total_edges} cited links
					{:else}
						Local verified semantic network
					{/if}
				</span>
			</div>
		</div>
		<IconButton icon="x" label="Close concept map" onclick={onclose} />
	</div>

	<div class="jb-map-tabs" role="tablist">
		<button
			type="button"
			role="tab"
			class="jb-map-tab"
			class:is-active={tab === 'explore'}
			aria-selected={tab === 'explore'}
			onclick={() => (tab = 'explore')}
		>
			Explore Graph
		</button>
		<button
			type="button"
			role="tab"
			class="jb-map-tab"
			class:is-active={tab === 'path'}
			aria-selected={tab === 'path'}
			onclick={() => {
				tab = 'path';
				if (!pathResult && graph) runPathFinder();
			}}
		>
			Multi-Hop Path Finder
		</button>
	</div>

	{#if errorMsg}
		<div class="jb-map-error">{errorMsg}</div>
	{/if}

	<div class="jb-map-body">
		{#if loading}
			<p class="jb-map-empty">Loading verified semantic network…</p>
		{:else if tab === 'explore'}
			<div class="jb-map-controls">
				<input
					type="search"
					class="jb-map-search"
					placeholder="Search concepts (e.g., ullimtong, 울림통, Bessel, Sejong)…"
					bind:value={searchText}
				/>
				<div class="jb-map-pills">
					{#each Object.entries(TYPE_LABELS) as [key, label]}
						<button
							type="button"
							class="jb-map-pill"
							class:is-active={typeFilter === key}
							onclick={() => (typeFilter = key)}
						>
							{label}
						</button>
					{/each}
				</div>
			</div>

			{#if nodeDetails}
				<div class="jb-map-canvas-wrap">
					<svg viewBox="0 0 380 256" class="jb-map-svg" role="img" aria-label="Neighborhood graph for {nodeDetails.node.label}">
						{#each radialNeighbors as nb (nb.id)}
							<line
								x1="190"
								y1="128"
								x2={nb.x}
								y2={nb.y}
								class="jb-svg-edge"
								class:is-incoming={nb.direction === 'incoming'}
							/>
							<text x={nb.lx} y={nb.ly} class="jb-svg-pred" text-anchor="middle">
								{shortLabel(nb.predicate, 14)}
							</text>
							<g
								class="jb-svg-node"
								role="button"
								tabindex="0"
								onclick={() => selectNode(nb.id)}
								onkeydown={(e) => {
									if (e.key === 'Enter' || e.key === ' ') {
										e.preventDefault();
										selectNode(nb.id);
									}
								}}
							>
								<rect x={nb.x - 52} y={nb.y - 13} width="104" height="26" rx="13" />
								<text x={nb.x} y={nb.y + 4} text-anchor="middle">{shortLabel(nb.label, 15)}</text>
							</g>
						{/each}

						<g class="jb-svg-center">
							<rect x="122" y="110" width="136" height="36" rx="18" />
							<text x="190" y="132" text-anchor="middle">{shortLabel(nodeDetails.node.label, 18)}</text>
						</g>
					</svg>
				</div>

				<section class="jb-map-card">
					<div class="jb-map-card__top">
						<div>
							<h3 class="jb-map-card__title">
								{nodeDetails.node.label}
								{#if nodeDetails.node.korean_name}
									<span class="jb-map-card__ko" lang="ko">{nodeDetails.node.korean_name}</span>
								{/if}
							</h3>
							<span class="jb-map-badge">{TYPE_LABELS[nodeDetails.node.node_type] ?? nodeDetails.node.node_type}</span>
						</div>
						<Button
							variant="primary"
							label="Ask Danbi"
							icon="arrowRight"
							disabled={busy}
							onclick={() => onask(`Tell me about ${nodeDetails?.node.label} on the janggu.`)}
						/>
					</div>

					<p class="jb-map-card__summary">{nodeDetails.node.summary}</p>

					{#if nodeDetails.outgoing.length > 0}
						<h4 class="jb-map-sec">Outgoing Verified Links ({nodeDetails.outgoing.length})</h4>
						<ul class="jb-map-rels">
							{#each nodeDetails.outgoing as rel}
								<li>
									<button type="button" class="jb-rel-btn" onclick={() => selectNode(rel.neighbor_id)}>
										<span class="jb-rel-pred">{rel.predicate.replace(/_/g, ' ')}</span>
										<span class="jb-rel-target">{rel.neighbor_label}</span>
										<span class="jb-rel-fid">{rel.fact_id}</span>
									</button>
								</li>
							{/each}
						</ul>
					{/if}

					{#if nodeDetails.incoming.length > 0}
						<h4 class="jb-map-sec">Incoming Verified Links ({nodeDetails.incoming.length})</h4>
						<ul class="jb-map-rels">
							{#each nodeDetails.incoming as rel}
								<li>
									<button type="button" class="jb-rel-btn" onclick={() => selectNode(rel.neighbor_id)}>
										<span class="jb-rel-target">{rel.neighbor_label}</span>
										<span class="jb-rel-pred">{rel.predicate.replace(/_/g, ' ')}</span>
										<span class="jb-rel-fid">{rel.fact_id}</span>
									</button>
								</li>
							{/each}
						</ul>
					{/if}

					{#if nodeDetails.citations.length > 0}
						<h4 class="jb-map-sec">Supporting Sources ({nodeDetails.citations.length})</h4>
						<ul class="jb-map-cites">
							{#each nodeDetails.citations.slice(0, 5) as cite}
								<li>
									<strong>[{cite.fact_id}]</strong> {cite.title} — <span>{cite.publisher} (Tier {cite.tier})</span>
								</li>
							{/each}
						</ul>
					{/if}
				</section>
			{/if}

			<div class="jb-map-index">
				<h4 class="jb-map-sec">Browse Concepts ({filteredNodes.length})</h4>
				<div class="jb-map-chips">
					{#each filteredNodes.slice(0, 48) as n (n.id)}
						<button
							type="button"
							class="jb-concept-chip"
							class:is-selected={n.id === selectedId}
							onclick={() => selectNode(n.id)}
						>
							{n.label}
						</button>
					{/each}
				</div>
			</div>
		{:else}
			<div class="jb-path-panel">
				<div class="jb-path-presets">
					{#each PATH_PRESETS as preset}
						<button
							type="button"
							class="jb-map-pill"
							onclick={() => runPathFinder(preset.from, preset.to)}
						>
							{preset.label}
						</button>
					{/each}
				</div>

				<div class="jb-path-form">
					<label>
						<span>From concept</span>
						<select bind:value={fromConcept}>
							{#each graph?.nodes ?? [] as n (n.id)}
								<option value={n.id}>{n.label}</option>
							{/each}
						</select>
					</label>
					<label>
						<span>To concept</span>
						<select bind:value={toConcept}>
							{#each graph?.nodes ?? [] as n (n.id)}
								<option value={n.id}>{n.label}</option>
							{/each}
						</select>
					</label>
					<Button
						variant="primary"
						label={pathLoading ? 'Tracing…' : 'Trace Verified Path'}
						icon="network"
						disabled={pathLoading}
						onclick={() => runPathFinder()}
					/>
				</div>

				{#if pathResult}
					{#if pathResult.found}
						<div class="jb-map-card">
							<div class="jb-map-card__top">
								<div>
									<h3 class="jb-map-card__title">
										{pathResult.source?.label} → {pathResult.target?.label}
									</h3>
									<span class="jb-map-badge">{pathResult.hop_count} verified hop{pathResult.hop_count === 1 ? '' : 's'}</span>
								</div>
								<Button
									variant="ghost"
									label="Ask Danbi"
									icon="arrowRight"
									disabled={busy}
									onclick={() =>
										onask(`How does ${pathResult?.source?.label} connect to ${pathResult?.target?.label}?`)}
								/>
							</div>

							<ol class="jb-hop-list">
								{#each pathResult.hops as hop}
									<li>
										<div class="jb-hop-line">
											<strong>{hop.from_label}</strong>
											<span class="jb-rel-pred">
												{hop.direction === 'outgoing' ? '→' : '←'} {hop.predicate.replace(/_/g, ' ')}
											</span>
											<strong>{hop.to_label}</strong>
											<span class="jb-rel-fid">{hop.fact_id}</span>
										</div>
										<p class="jb-hop-fact">{hop.fact_statement}</p>
									</li>
								{/each}
							</ol>

							{#if pathResult.citations.length > 0}
								<h4 class="jb-map-sec">Path Citations ({pathResult.citations.length})</h4>
								<ul class="jb-map-cites">
									{#each pathResult.citations as cite}
										<li>
											<strong>[{cite.fact_id}]</strong> {cite.title} — <span>{cite.publisher} (Tier {cite.tier})</span>
										</li>
									{/each}
								</ul>
							{/if}
						</div>
					{:else}
						<p class="jb-map-empty">No verified path found within 5 hops between these two concepts.</p>
					{/if}
				{/if}
			</div>
		{/if}
	</div>
</aside>

<style>
	.jb-map-backdrop {
		position: fixed;
		inset: var(--header-height) 0 0 0;
		z-index: 44;
		background: var(--overlay-backdrop);
	}

	.jb-map-panel {
		position: fixed;
		top: var(--header-height);
		right: 0;
		bottom: 0;
		width: min(460px, 94vw);
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

	.jb-map-panel.is-open {
		transform: translateX(0);
		visibility: visible;
		transition: transform 0.24s cubic-bezier(0.22, 0.8, 0.24, 1);
	}

	.jb-map-head {
		flex: none;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--space-4) var(--space-3) var(--space-3) var(--space-4);
		border-bottom: 1px solid var(--border-subtle);
	}

	.jb-map-heading {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.jb-map-icon {
		width: 30px;
		height: 30px;
		border-radius: var(--radius-sm);
		display: grid;
		place-items: center;
		background: var(--accent-soft);
		color: var(--accent);
		border: 1px solid color-mix(in srgb, var(--accent) 45%, var(--border-default));
	}

	.jb-map-title {
		margin: 0;
		font-family: var(--font-display);
		font-size: 16px;
		color: var(--text-primary);
	}

	.jb-map-sub {
		display: block;
		font-size: 12px;
		color: var(--text-secondary);
		margin-top: 2px;
	}

	.jb-map-tabs {
		flex: none;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 6px;
		padding: var(--space-2) var(--space-3);
		border-bottom: 1px solid var(--border-subtle);
	}

	.jb-map-tab {
		padding: 7px 10px;
		border-radius: var(--radius-sm);
		border: 1px solid var(--border-subtle);
		background: transparent;
		color: var(--text-secondary);
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
	}

	.jb-map-tab.is-active {
		background: var(--accent-soft);
		color: var(--accent);
		border-color: color-mix(in srgb, var(--accent) 50%, var(--border-default));
	}

	.jb-map-body {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		padding: var(--space-3);
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.jb-map-controls {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.jb-map-search {
		width: 100%;
		padding: 8px 10px;
		border-radius: var(--radius-sm);
		border: 1px solid var(--border-default);
		background: var(--bg-elevated);
		color: var(--text-primary);
		font-size: 13px;
	}

	.jb-map-pills,
	.jb-path-presets,
	.jb-map-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}

	.jb-map-pill,
	.jb-concept-chip {
		padding: 4px 9px;
		border-radius: 999px;
		border: 1px solid var(--border-subtle);
		background: var(--bg-elevated);
		color: var(--text-secondary);
		font-size: 11.5px;
		cursor: pointer;
	}

	.jb-map-pill.is-active,
	.jb-concept-chip.is-selected {
		background: var(--accent-soft);
		color: var(--accent);
		border-color: var(--accent);
		font-weight: 600;
	}

	.jb-map-canvas-wrap {
		border: 1px solid var(--border-default);
		border-radius: var(--radius-md);
		background: var(--bg-elevated);
		padding: 4px;
	}

	.jb-map-svg {
		width: 100%;
		height: auto;
		display: block;
	}

	.jb-svg-edge {
		stroke: var(--accent);
		stroke-width: 1.4;
		stroke-opacity: 0.55;
	}

	.jb-svg-edge.is-incoming {
		stroke-dasharray: 4 3;
	}

	.jb-svg-pred {
		font-size: 8.5px;
		fill: var(--text-secondary);
		font-family: var(--font-mono);
	}

	.jb-svg-node {
		cursor: pointer;
	}

	.jb-svg-node rect {
		fill: var(--bg-sidebar);
		stroke: var(--border-default);
		stroke-width: 1.2;
	}

	.jb-svg-node:hover rect {
		stroke: var(--accent);
	}

	.jb-svg-node text {
		font-size: 9.5px;
		fill: var(--text-primary);
		font-weight: 500;
	}

	.jb-svg-center rect {
		fill: var(--accent);
	}

	.jb-svg-center text {
		font-size: 10.5px;
		fill: #fff;
		font-weight: 700;
	}

	.jb-map-card {
		border: 1px solid var(--border-default);
		border-radius: var(--radius-md);
		background: var(--bg-elevated);
		padding: 12px;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.jb-map-card__top {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 8px;
	}

	.jb-map-card__title {
		margin: 0;
		font-size: 15px;
		color: var(--text-primary);
	}

	.jb-map-card__ko {
		font-size: 13px;
		color: var(--text-secondary);
		margin-left: 6px;
		font-weight: 400;
	}

	.jb-map-badge {
		display: inline-block;
		margin-top: 4px;
		font-size: 11px;
		font-family: var(--font-mono);
		color: var(--accent);
		background: var(--accent-soft);
		padding: 2px 7px;
		border-radius: 999px;
	}

	.jb-map-card__summary {
		margin: 0;
		font-size: 13px;
		line-height: 1.45;
		color: var(--text-secondary);
	}

	.jb-map-sec {
		margin: 4px 0 2px;
		font-size: 11.5px;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--text-secondary);
	}

	.jb-map-rels,
	.jb-map-cites,
	.jb-hop-list {
		margin: 0;
		padding: 0;
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.jb-rel-btn {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 6px;
		padding: 6px 8px;
		border-radius: var(--radius-sm);
		border: 1px solid var(--border-subtle);
		background: var(--bg-sidebar);
		color: var(--text-primary);
		font-size: 12px;
		cursor: pointer;
		text-align: left;
	}

	.jb-rel-btn:hover {
		border-color: var(--accent);
	}

	.jb-rel-pred {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--accent);
	}

	.jb-rel-target {
		flex: 1;
		font-weight: 600;
	}

	.jb-rel-fid {
		font-family: var(--font-mono);
		font-size: 10.5px;
		color: var(--text-secondary);
		padding: 1px 5px;
		border-radius: 4px;
		border: 1px solid var(--border-subtle);
	}

	.jb-map-cites li {
		font-size: 11.5px;
		line-height: 1.4;
		color: var(--text-secondary);
	}

	.jb-path-panel {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.jb-path-form {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.jb-path-form label {
		display: flex;
		flex-direction: column;
		gap: 4px;
		font-size: 12px;
		color: var(--text-secondary);
	}

	.jb-path-form select {
		padding: 8px;
		border-radius: var(--radius-sm);
		border: 1px solid var(--border-default);
		background: var(--bg-elevated);
		color: var(--text-primary);
		font-size: 13px;
	}

	.jb-hop-list li {
		padding: 8px;
		border-radius: var(--radius-sm);
		border: 1px solid var(--border-subtle);
		background: var(--bg-sidebar);
	}

	.jb-hop-line {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 6px;
		font-size: 12.5px;
		color: var(--text-primary);
	}

	.jb-hop-fact {
		margin: 5px 0 0;
		font-size: 12px;
		line-height: 1.4;
		color: var(--text-secondary);
	}

	.jb-map-error {
		margin: 8px 12px 0;
		padding: 8px 10px;
		border-radius: var(--radius-sm);
		background: color-mix(in srgb, #c0392b 16%, transparent);
		color: var(--text-primary);
		font-size: 12.5px;
	}

	.jb-map-empty {
		font-size: 13px;
		color: var(--text-secondary);
		text-align: center;
		padding: 16px;
	}
</style>
