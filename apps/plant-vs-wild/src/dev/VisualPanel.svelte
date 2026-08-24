<script lang="ts">
	/**
	 * Panneau de revue visuelle — OUTIL DE DÉVELOPPEMENT UNIQUEMENT.
	 *
	 * Il n'affiche que ce que `VisualOverlay` a publié : le composant qui vit dans
	 * l'arbre Pixi connaît le `scale` réellement appliqué, ce panneau non. Rien
	 * n'est recalculé ici, donc rien ne peut diverger du rendu.
	 *
	 * Monté uniquement sous `import.meta.env.DEV` (voir routes/+layout.svelte).
	 */
	import { onMount } from 'svelte';

	import {
		CELL_GAP,
		CELL_SIZE,
		CELL_OPACITY,
		SYMBOL_SIZE,
		BOARD_SIZES,
		SYMBOL_DISPLAY_SIZE,
		SYMBOL_DISPLAY_RATIO,
		CELL_OPACITY_PRESETS,
	} from '../game/constants';
	import { visualGuides, visualMetrics } from './visualMode.svelte';

	let open = $state(true);
	let fps = $state(0);

	const round = (value: number) => Math.round(value * 10) / 10;

	const opacityName = $derived(
		Object.entries(CELL_OPACITY_PRESETS).find(([, value]) => value === CELL_OPACITY)?.[0] ??
			'personnalisée',
	);

	onMount(() => {
		let frames = 0;
		let last = performance.now();
		let raf = 0;

		const tick = () => {
			frames += 1;
			const now = performance.now();
			if (now - last >= 500) {
				fps = Math.round((frames * 1000) / (now - last));
				frames = 0;
				last = now;
			}
			raf = requestAnimationFrame(tick);
		};

		raf = requestAnimationFrame(tick);
		return () => cancelAnimationFrame(raf);
	});
</script>

<aside class="visual-panel">
	<button class="toggle" onclick={() => (open = !open)}>
		{open ? '▼' : '▲'} VISUAL
	</button>

	{#if open}
		<div class="body">
			<section>
				<h2>viewport</h2>
				<dl>
					<dt>viewport</dt>
					<dd>{visualMetrics.viewportWidth} × {visualMetrics.viewportHeight}</dd>
					<dt>layoutType</dt>
					<dd>{visualMetrics.layoutType}</dd>
					<dt>design</dt>
					<dd>{visualMetrics.designWidth} × {visualMetrics.designHeight}</dd>
					<dt>scale</dt>
					<dd>{round(visualMetrics.scale * 1000) / 1000}</dd>
					<dt>fps</dt>
					<dd>{fps}</dd>
				</dl>
			</section>

			<section>
				<h2>rendu (px)</h2>
				<dl>
					<dt>grille</dt>
					<dd>{round(visualMetrics.gridWidth)} × {round(visualMetrics.gridHeight)}</dd>
					<dt>case</dt>
					<dd>{round(visualMetrics.cellSize)}</dd>
					<dt>symbole</dt>
					<dd>{round(visualMetrics.symbolSize)}</dd>
					<dt>gap</dt>
					<dd>{round(visualMetrics.gap)}</dd>
					<dt>bande logo</dt>
					<dd>{round(visualMetrics.logoBand)}</dd>
					<dt>bande bar</dt>
					<dd>{round(visualMetrics.gameBarBand)}</dd>
					{#if visualMetrics.spinSize}
						<dt>spin</dt>
						<dd>{round(visualMetrics.spinSize)}</dd>
					{/if}
				</dl>
			</section>

			<section>
				<h2>logique</h2>
				<dl>
					<dt>grille</dt>
					<dd>{BOARD_SIZES.width} × {BOARD_SIZES.height}</dd>
					<dt>pas</dt>
					<dd>{SYMBOL_SIZE}</dd>
					<dt>case</dt>
					<dd>{CELL_SIZE}</dd>
					<dt>symbole</dt>
					<dd>{round(SYMBOL_DISPLAY_SIZE)}</dd>
					<dt>gap</dt>
					<dd>{CELL_GAP}</dd>
					<dt>sym / case</dt>
					<dd>{SYMBOL_DISPLAY_RATIO}</dd>
					<dt>opacité</dt>
					<dd>{CELL_OPACITY} ({opacityName})</dd>
				</dl>
			</section>

			<section>
				<h2>repères</h2>
				<label><input type="checkbox" bind:checked={visualGuides.gridBounds} /> Grid bounds</label>
				<label><input type="checkbox" bind:checked={visualGuides.cellBounds} /> Cell bounds</label>
				<label><input type="checkbox" bind:checked={visualGuides.centers} /> Centers</label>
				<label><input type="checkbox" bind:checked={visualGuides.safeZones} /> Safe zones</label>
			</section>

			<p class="note">
				Opacité réglable dans <code>game/constants.ts</code> → <code>CELL_OPACITY</code> :
				faible {CELL_OPACITY_PRESETS.faible} · moyen {CELL_OPACITY_PRESETS.moyen} · appuyé
				{CELL_OPACITY_PRESETS.appuye}
			</p>
		</div>
	{/if}
</aside>

<style>
	.visual-panel {
		position: fixed;
		right: 8px;
		top: 8px;
		z-index: 99999;
		font: 12px/1.4 ui-monospace, Menlo, Consolas, monospace;
		color: #e7e7e7;
		background: rgba(16, 16, 20, 0.94);
		border: 1px solid #4a4a55;
		border-radius: 4px;
		width: 240px;
	}

	.toggle {
		display: block;
		width: 100%;
		padding: 6px 10px;
		background: #2a2a33;
		color: #e7e7e7;
		border: 0;
		border-radius: 3px;
		cursor: pointer;
		font: inherit;
		text-align: left;
		letter-spacing: 0.08em;
	}

	.body {
		padding: 10px;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	h2 {
		margin: 0 0 4px;
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: #8d8d9c;
	}

	dl {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 1px 8px;
		margin: 0;
	}

	dt {
		color: #9a9aa8;
	}

	dd {
		margin: 0;
		text-align: right;
		font-variant-numeric: tabular-nums;
	}

	label {
		display: flex;
		align-items: center;
		gap: 6px;
		cursor: pointer;
	}

	.note {
		margin: 0;
		color: #8d8d9c;
		font-size: 11px;
	}

	code {
		color: #c8c8d4;
	}
</style>
