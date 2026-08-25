<script lang="ts">
	/**
	 * Lecteur de books mockés — OUTIL DE DÉVELOPPEMENT UNIQUEMENT.
	 *
	 * Il ne fabrique aucun résultat : il donne un book écrit à la main au pipeline
	 * Stake normal, exactement comme le Debug Panel de `apps/lines` le fait avec
	 * un book produit par le Math.
	 *
	 * Monté uniquement sous `import.meta.env.DEV` (voir routes/+layout.svelte).
	 */
	import { playBookEvents } from '../game/utils';
	import { WILD_MAX_CHARGE } from '../game/config';
	import cascade from '../stories/data/base_book_cascade';
	import wild from '../stories/data/base_book_wild';
	import multiplier from '../stories/data/base_book_multiplier';

	const SCENARIOS = [
		{ id: 'cascade', label: 'Cascade simple (sans Wild)', events: cascade.bookEvents },
		{ id: 'wild-reveal', label: 'A · Wild présent au reveal', events: wild.bookWildAtReveal.state },
		{ id: 'wild-refill', label: 'B · Wild arrivé au refill', events: wild.bookWildFromRefill.state },
		{
			id: 'wild-released',
			label: 'C · Wild dans une case libérée',
			events: wild.bookWildInReleasedCell.state,
		},
		{ id: 'charge-1', label: 'Connexion · charge 0 → 1', events: wild.bookWildCharge1.state },
		{ id: 'charge-2', label: 'Connexion · charge 1 → 2', events: wild.bookWildCharge2.state },
		{ id: 'charge-3', label: 'Connexion · charge 2 → 3', events: wild.bookWildCharge3.state },
		{
			id: 'bonus-pending',
			label: `Connexion · charge 3 → ${WILD_MAX_CHARGE} (bonus pending)`,
			events: wild.bookWildBonusPending.state,
		},
		{
			id: 'mult-cascade',
			label: 'Multiplicateurs · 2 cascades (x2 puis x4)',
			events: multiplier.bookMultiplierCascade.state,
		},
		{
			id: 'mult-reset',
			label: 'Multiplicateurs · nouveau spin (reset)',
			events: multiplier.bookMultiplierResetSpin.state,
		},
		{
			id: 'mult-final',
			label: 'Multiplicateurs · fin de pari (finalWin)',
			events: multiplier.bookMultiplierFinalWin.state,
		},
		{
			id: 'mult-full',
			label: 'Multiplicateurs · grille pleine, jusqu au cap x4096',
			events: [multiplier.multiplierEvents.reveal, multiplier.multiplierEvents.full],
		},
		{
			id: 'mult-wild',
			label: 'Multiplicateurs · avec le Wild',
			events: multiplier.bookMultiplierWithWild.state,
		},
	];

	let scenarioId = $state(SCENARIOS[0].id);
	let playing = $state(false);
	let plays = $state(0);
	let lastError = $state('');

	const scenario = $derived(SCENARIOS.find((item) => item.id === scenarioId) ?? SCENARIOS[0]);

	const play = async () => {
		if (playing) return;
		playing = true;
		lastError = '';
		try {
			await playBookEvents(scenario.events);
			plays += 1;
		} catch (error) {
			lastError = error instanceof Error ? error.message : String(error);
		} finally {
			playing = false;
		}
	};
</script>

<aside class="book-player">
	<select bind:value={scenarioId} disabled={playing}>
		{#each SCENARIOS as item (item.id)}
			<option value={item.id}>{item.label}</option>
		{/each}
	</select>
	<button onclick={play} disabled={playing}>
		{playing ? 'lecture…' : '▶ PLAY'}
	</button>
	<span>lectures : {plays}</span>
	{#if lastError}<span class="error">{lastError}</span>{/if}
</aside>

<style>
	.book-player {
		position: fixed;
		left: 8px;
		bottom: 8px;
		z-index: 99999;
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 10px;
		font: 12px/1.4 ui-monospace, Menlo, Consolas, monospace;
		color: #e7e7e7;
		background: rgba(16, 16, 20, 0.94);
		border: 1px solid #4a4a55;
		border-radius: 4px;
	}

	select,
	button {
		padding: 6px 10px;
		background: #2a2a33;
		color: #e7e7e7;
		border: 1px solid #4a4a55;
		border-radius: 3px;
		cursor: pointer;
		font: inherit;
	}

	button {
		letter-spacing: 0.08em;
	}

	button:disabled,
	select:disabled {
		opacity: 0.5;
		cursor: default;
	}

	.error {
		color: #ff6b6b;
	}
</style>
