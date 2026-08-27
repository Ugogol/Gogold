<script lang="ts">
	/**
	 * Debug Panel — OUTIL DE DÉVELOPPEMENT UNIQUEMENT.
	 *
	 * C'est un LANCEUR DE BOOKS, rien d'autre. Il sélectionne un book écrit à la
	 * main et le donne au pipeline Stake normal :
	 *
	 *     Book → playBookEvent → bookEventHandlerMap → emitterEvents → composants
	 *
	 * Il n'anime rien lui-même, ne touche jamais au plateau, ne calcule aucun
	 * cluster, ne tire rien au hasard. Aucune seconde boucle de gameplay.
	 *
	 * Monté uniquement sous `import.meta.env.DEV` (voir routes/+layout.svelte),
	 * donc absent du bundle de production.
	 */
	import { playBookEvent } from '../game/utils';
	import { eventEmitter } from '../game/eventEmitter';
	import { stateGame } from '../game/stateGame.svelte';
	import { debugScenarios, genericSpins, genericMathSpins, resetBook } from './debugScenarios';
	import { WILD_MAX_CHARGE } from '../game/config';

	let open = $state(true);
	let scenarioId = $state(debugScenarios[0].id);
	let playing = $state(false);
	let replayCount = $state(0);
	let genericIndex = $state(0);
	let genericMode = $state(false);
	/** Quelle série générique défile : books MOCK ou books MATH. */
	let genericSource = $state<'mock' | 'math'>('math');
	let currentEvent = $state('');
	let eventStep = $state(0);
	let eventTotal = $state(0);
	let lastError = $state('');

	const scenario = $derived(
		debugScenarios.find((item) => item.id === scenarioId) ?? debugScenarios[0],
	);
	const genericList = $derived(genericSource === 'math' ? genericMathSpins : genericSpins);
	const mode = $derived(stateGame.gameType === 'freegame' ? 'BONUS' : 'BASE');

	/**
	 * Joue un book event par event.
	 *
	 * C'est exactement ce que fait `playBookEvents` — même handler map, même
	 * contexte `{ bookEvents }` — déroulé ici pour pouvoir afficher l'avancement.
	 * Rien n'est contrôlé ni court-circuité : chaque event est simplement awaité
	 * dans l'ordre du book.
	 */
	const play = async (bookEvents: typeof resetBook) => {
		if (playing) return;
		playing = true;
		lastError = '';
		eventTotal = bookEvents.length;
		try {
			for (const [index, bookEvent] of bookEvents.entries()) {
				eventStep = index + 1;
				currentEvent = bookEvent.type;
				await playBookEvent(bookEvent, { bookEvents });
			}
			currentEvent = '';
		} catch (error) {
			lastError = error instanceof Error ? error.message : String(error);
		} finally {
			playing = false;
		}
	};

	/**
	 * Remet le jeu à un état Base propre AVANT de lancer un book.
	 *
	 * Les éléments d'UI du Bonus sont masqués par leurs emitterEvents existants ;
	 * le mode et le plateau, eux, sont remis par un book de reset joué
	 * normalement. Aucun état parallèle, aucune seconde state machine.
	 */
	const clearBonusUi = () => {
		eventEmitter.broadcast({ type: 'freeSpinCounterHide' });
		eventEmitter.broadcast({ type: 'freeSpinIntroHide' });
		eventEmitter.broadcast({ type: 'freeSpinOutroHide' });
		eventEmitter.broadcast({ type: 'multiplierGridClear' });
		eventEmitter.broadcast({ type: 'multiplierGridHide' });
		eventEmitter.broadcast({ type: 'tumbleBoardReset' });
		eventEmitter.broadcast({ type: 'tumbleBoardHide' });
		eventEmitter.broadcast({ type: 'boardShow' });
	};

	const spin = async () => {
		if (genericMode) return spinGeneric();
		clearBonusUi();
		replayCount = 1;
		await play(scenario.events);
	};

	const replay = async () => {
		clearBonusUi();
		replayCount += 1;
		await play(genericMode ? genericList[genericIndex].events : scenario.events);
	};

	const spinGeneric = async () => {
		clearBonusUi();
		await play(genericList[genericIndex].events);
	};

	/**
	 * Spin suivant de la série demandée. Changer de série repart de son début :
	 * les deux listes n'ont ni la même longueur ni le même contenu.
	 */
	const nextGeneric = async (source: 'mock' | 'math') => {
		if (playing) return;
		const restart = !genericMode || genericSource !== source;
		genericSource = source;
		genericMode = true;
		genericIndex = restart ? 0 : (genericIndex + 1) % genericList.length;
		replayCount = 0;
		await spinGeneric();
	};

	const reset = async () => {
		if (playing) return;
		genericMode = false;
		genericIndex = 0;
		replayCount = 0;
		clearBonusUi();
		await play(resetBook);
		currentEvent = '';
		eventStep = 0;
		eventTotal = 0;
	};

	/**
	 * Charge du Wild, lue directement sur le plateau — OBSERVATION PURE.
	 *
	 * Rien n'est calculé ni déduit : `rawSymbol.charge` est écrit par le handler
	 * `wildMove` à partir de la valeur du Book. Le panneau l'affiche, comme il
	 * affiche déjà le mode et l'event courant.
	 *
	 * Les lignes du plateau sont des index PADDÉS — 0 est hors champ, 1 à 5 sont
	 * visibles. On n'inspecte que les lignes visibles, et la case est affichée
	 * `(reel,row)`, exactement comme une `Position` de Book : les coordonnées se
	 * comparent au JSON sans conversion.
	 */
	const wildState = $derived.by(() => {
		const wilds: { reel: number; row: number; charge: number; temporary: boolean }[] = [];

		for (const [reelIndex, reel] of stateGame.board.entries()) {
			for (const [rowIndex, symbol] of reel.reelState.symbols.entries()) {
				if (rowIndex < 1 || rowIndex > 5) continue;
				if (symbol?.rawSymbol.name !== 'W') continue;
				wilds.push({
					reel: reelIndex,
					row: rowIndex,
					charge: symbol.rawSymbol.charge ?? 0,
					temporary: Boolean(symbol.rawSymbol.temporary),
				});
			}
		}

		return {
			main: wilds.find((wild) => !wild.temporary) ?? null,
			temporary: wilds.filter((wild) => wild.temporary).length,
		};
	});

	const status = $derived(playing ? 'Playing' : 'Ready');
	const currentLabel = $derived(
		genericMode
			? `${genericSource.toUpperCase()} ${genericIndex + 1}/${genericList.length} — ${genericList[genericIndex].label}`
			: `${scenario.group} · ${scenario.label}`,
	);
</script>

<aside class="debug-panel">
	<button class="toggle" onclick={() => (open = !open)}>
		{open ? '▼' : '▲'} DEBUG
	</button>

	{#if open}
		<div class="body">
			<label>
				<span class="hint">Scenario</span>
				<select
					bind:value={scenarioId}
					disabled={playing}
					onchange={() => {
						genericMode = false;
						replayCount = 0;
					}}
				>
					{#each debugScenarios as item (item.id)}
						<option value={item.id}>{item.group} · {item.label}</option>
					{/each}
				</select>
			</label>

			<div class="row">
				<button onclick={spin} disabled={playing}>SPIN</button>
				<button onclick={replay} disabled={playing}>REPLAY</button>
			</div>
			<div class="row">
				<button onclick={() => nextGeneric('math')} disabled={playing}>NEXT MATH</button>
				<button onclick={() => nextGeneric('mock')} disabled={playing}>NEXT MOCK</button>
			</div>
			<div class="row">
				<button onclick={reset} disabled={playing}>RESET</button>
			</div>

			<dl>
				<dt>état</dt>
				<dd class:playing>{status}</dd>
				<dt>mode</dt>
				<dd>{mode}</dd>
				<dt>charge</dt>
				<dd class:charged={(wildState.main?.charge ?? 0) >= WILD_MAX_CHARGE}>
					{#if wildState.main}
						{wildState.main.charge}/{WILD_MAX_CHARGE} · ({wildState.main.reel},{wildState.main.row})
					{:else}
						pas de Wild
					{/if}
				</dd>
				{#if wildState.temporary > 0}
					<dt>temporaires</dt>
					<dd>{wildState.temporary}</dd>
				{/if}
				<dt>courant</dt>
				<dd class="wrap">{currentLabel}</dd>
				{#if replayCount > 0}
					<dt>lecture</dt>
					<dd>#{replayCount}</dd>
				{/if}
				{#if eventTotal > 0}
					<dt>event</dt>
					<dd class="wrap">{currentEvent || '—'} · {eventStep}/{eventTotal}</dd>
				{/if}
			</dl>

			{#if lastError}<p class="error">{lastError}</p>{/if}
		</div>
	{/if}
</aside>

<style>
	.debug-panel {
		position: fixed;
		left: 8px;
		bottom: 8px;
		z-index: 99999;
		width: 236px;
		max-width: calc(100vw - 16px);
		font: 12px/1.4 ui-monospace, Menlo, Consolas, monospace;
		color: #e7e7e7;
		background: rgba(16, 16, 20, 0.94);
		border: 1px solid #4a4a55;
		border-radius: 4px;
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
		padding: 8px 10px 10px;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.hint {
		color: #8d8d9c;
		font-size: 10px;
		letter-spacing: 0.14em;
		text-transform: uppercase;
	}

	select,
	button {
		padding: 5px 8px;
		background: #2a2a33;
		color: #e7e7e7;
		border: 1px solid #4a4a55;
		border-radius: 3px;
		cursor: pointer;
		font: inherit;
	}

	.row {
		display: flex;
		gap: 6px;
	}

	.row button {
		flex: 1;
		letter-spacing: 0.06em;
	}

	button:disabled,
	select:disabled {
		opacity: 0.45;
		cursor: default;
	}

	dl {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 1px 8px;
		margin: 0;
	}

	dt {
		color: #9a9aa8;
	}

	dd {
		margin: 0;
		text-align: right;
	}

	dd.wrap {
		text-align: right;
		overflow-wrap: anywhere;
	}

	dd.playing {
		color: #7ee787;
	}

	dd.charged {
		color: #ffcc4d;
	}

	.error {
		margin: 0;
		color: #ff6b6b;
	}
</style>
