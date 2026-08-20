<script lang="ts">
	/**
	 * Debug Panel — OUTIL DE DÉVELOPPEMENT UNIQUEMENT.
	 *
	 * Ne fabrique jamais un résultat : il sélectionne un Book déjà produit par le
	 * Math SDK et le donne au pipeline Stake normal via `playBet`, exactement comme
	 * la machine XState le fait dans `onPlayGame`.
	 *
	 * Monté uniquement sous `import.meta.env.DEV` (voir routes/+layout.svelte).
	 */
	import { onMount } from 'svelte';

	import { playBet } from '../game/utils';
	import type { Bet } from '../game/typesBookEvent';
	import { debugScenarios, type DebugBook } from './debugScenarios.generated';

	let open = $state(false);
	let scenarioId = $state(debugScenarios[0]?.id ?? '');
	let bookIndex = $state(0);
	let playing = $state(false);
	let lastError = $state('');

	let fps = $state(0);
	let viewport = $state({ width: 0, height: 0 });

	const scenario = $derived(debugScenarios.find((item) => item.id === scenarioId));
	const book = $derived(scenario?.books[bookIndex]);
	const orientation = $derived(viewport.width >= viewport.height ? 'landscape' : 'portrait');

	const play = async (selected: DebugBook | undefined) => {
		if (!selected || playing) return;
		playing = true;
		lastError = '';
		try {
			// Le Book généré est typé de façon lâche (events: unknown[]) car il vient
			// d'un fichier de fixtures. Sa forme est garantie par le Math SDK : c'est
			// le même contrat que celui que le RGS renvoie dans `round`.
			await playBet({ ...selected, state: selected.events } as unknown as Bet);
		} catch (error) {
			lastError = error instanceof Error ? error.message : String(error);
			console.error('[debug] playBet a échoué', error);
		} finally {
			playing = false;
		}
	};

	const onScenarioChange = () => {
		bookIndex = 0;
	};

	onMount(() => {
		const readViewport = () => {
			viewport = { width: window.innerWidth, height: window.innerHeight };
		};
		readViewport();
		window.addEventListener('resize', readViewport);

		let frames = 0;
		let since = performance.now();
		let raf = 0;
		const tick = (now: number) => {
			frames += 1;
			if (now - since >= 500) {
				fps = Math.round((frames * 1000) / (now - since));
				frames = 0;
				since = now;
			}
			raf = requestAnimationFrame(tick);
		};
		raf = requestAnimationFrame(tick);

		return () => {
			window.removeEventListener('resize', readViewport);
			cancelAnimationFrame(raf);
		};
	});
</script>

<div class="debug-panel" class:open>
	<button class="toggle" onclick={() => (open = !open)}>
		{open ? '▼' : '▲'} DEBUG
	</button>

	{#if open}
		<div class="body">
			<label>
				Scénario
				<select bind:value={scenarioId} onchange={onScenarioChange}>
					{#each debugScenarios as item (item.id)}
						<option value={item.id}>[{item.mode}] {item.label}</option>
					{/each}
				</select>
			</label>

			{#if scenario && scenario.books.length > 1}
				<label>
					Book
					<select bind:value={bookIndex}>
						{#each scenario.books as candidate, index (candidate.id)}
							<option value={index}>#{candidate.id} — payout {candidate.payoutMultiplier}</option>
						{/each}
					</select>
				</label>
			{/if}

			<div class="actions">
				<button onclick={() => play(book)} disabled={playing || !book}>PLAY</button>
				<button onclick={() => play(book)} disabled={playing || !book}>REPLAY</button>
			</div>

			<dl>
				<dt>mode</dt>
				<dd>{scenario?.mode ?? '—'}</dd>
				<dt>scénario</dt>
				<dd>{scenario?.id ?? '—'}</dd>
				<dt>book ID</dt>
				<dd>{book?.id ?? '—'}</dd>
				<dt>payoutMultiplier</dt>
				<dd>{book?.payoutMultiplier ?? '—'}</dd>
				<dt>bookEvents</dt>
				<dd>{book?.events.length ?? '—'}</dd>
				<dt>viewport</dt>
				<dd>{viewport.width} × {viewport.height} ({orientation})</dd>
				<dt>FPS</dt>
				<dd>{fps}</dd>
				<dt>état</dt>
				<dd>{playing ? 'lecture en cours…' : 'prêt'}</dd>
			</dl>

			{#if lastError}
				<p class="error">{lastError}</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	.debug-panel {
		position: fixed;
		right: 8px;
		bottom: 8px;
		z-index: 99999;
		font: 12px/1.4 ui-monospace, Menlo, Consolas, monospace;
		color: #e7e7e7;
		background: rgba(16, 16, 20, 0.94);
		border: 1px solid #4a4a55;
		border-radius: 4px;
		max-width: 320px;
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
		gap: 8px;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	select {
		font: inherit;
		padding: 3px;
		background: #1e1e25;
		color: #e7e7e7;
		border: 1px solid #4a4a55;
		border-radius: 3px;
	}

	.actions {
		display: flex;
		gap: 6px;
	}

	.actions button {
		flex: 1;
		padding: 6px;
		font: inherit;
		background: #3a5a8a;
		color: #fff;
		border: 0;
		border-radius: 3px;
		cursor: pointer;
	}

	.actions button:disabled {
		background: #33333d;
		color: #7a7a85;
		cursor: default;
	}

	dl {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 1px 8px;
		margin: 0;
	}

	dt {
		color: #9a9aa6;
	}

	dd {
		margin: 0;
		text-align: right;
		overflow-wrap: anywhere;
	}

	.error {
		margin: 0;
		color: #ff8f8f;
		overflow-wrap: anywhere;
	}
</style>
