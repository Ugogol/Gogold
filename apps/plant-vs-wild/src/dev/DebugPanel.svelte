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
	import { debugScenarios, genericSpins, resetBook } from './debugScenarios';

	let open = $state(true);
	let scenarioId = $state(debugScenarios[0].id);
	let playing = $state(false);
	let replayCount = $state(0);
	let genericIndex = $state(0);
	let genericMode = $state(false);
	let currentEvent = $state('');
	let eventStep = $state(0);
	let eventTotal = $state(0);
	let lastError = $state('');

	const scenario = $derived(
		debugScenarios.find((item) => item.id === scenarioId) ?? debugScenarios[0],
	);
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
		await play(genericMode ? genericSpins[genericIndex].events : scenario.events);
	};

	const spinGeneric = async () => {
		clearBonusUi();
		await play(genericSpins[genericIndex].events);
	};

	const nextGeneric = async () => {
		if (playing) return;
		genericMode = true;
		genericIndex = (genericIndex + 1) % genericSpins.length;
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

	const status = $derived(playing ? 'Playing' : 'Ready');
	const currentLabel = $derived(
		genericMode
			? `GENERIC ${genericIndex + 1}/${genericSpins.length} — ${genericSpins[genericIndex].label}`
			: scenario.label,
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
				<button onclick={nextGeneric} disabled={playing}>NEXT GENERIC</button>
				<button onclick={reset} disabled={playing}>RESET</button>
			</div>

			<dl>
				<dt>état</dt>
				<dd class:playing>{status}</dd>
				<dt>mode</dt>
				<dd>{mode}</dd>
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

	.error {
		margin: 0;
		color: #ff6b6b;
	}
</style>
