<script lang="ts">
	import type { Component } from 'svelte';
	import { App } from 'pixi-svelte';
	import { EnablePixiExtension } from 'components-pixi';
	import { MainContainer } from 'components-layout';

	import Background from './Background.svelte';
	import BoardCells from './BoardCells.svelte';
	import MultiplierGrid from './MultiplierGrid.svelte';
	import Board from './Board.svelte';
	import TumbleBoard from './TumbleBoard.svelte';
	import WildFlight from './WildFlight.svelte';
	import { isLocalVisualMode } from '../game/devVisualMode';

	/**
	 * Squelette de PLANT VS WILD.
	 *
	 * Composition : décor → grille 5×5 → 25 cases → symboles → multiplicateurs.
	 * Il n'y a volontairement aucun cadre autour de la grille (étape 3).
	 *
	 * ⚠️ Le calque des multiplicateurs est dessiné AU-DESSUS des symboles, alors
	 * que `apps/cluster` le place en dessous. Ses symboles sont des Spine posés
	 * dans un cadre `payframe` qui laisse la place au chiffre ; les nôtres sont
	 * des cartes opaques qui remplissent la case — en dessous, le badge est
	 * totalement masqué (vérifié à l'écran). Le multiplicateur reste malgré tout
	 * un calque indexé par la case, jamais lié au Sprite d'un symbole.
	 *
	 * Ni UI de mise, ni son, ni écran de chargement, ni machine de pari : ces
	 * briques arriveront avec le contrat RGS/math.
	 *
	 * IS_DEV est une constante de module : Vite la replie à `false` en production,
	 * la branche devient inatteignable et Rollup élimine l'overlay de revue.
	 */
	const IS_DEV = import.meta.env.DEV;
	const visualMode = IS_DEV && isLocalVisualMode();

	let VisualOverlay = $state<Component | null>(null);

	$effect(() => {
		if (IS_DEV && visualMode && !VisualOverlay) {
			import('../dev/VisualOverlay.svelte').then((module) => (VisualOverlay = module.default));
		}
	});
</script>

<App>
	<EnablePixiExtension />

	<Background />

	<MainContainer>
		<BoardCells />
		<Board />
		<TumbleBoard />
		<MultiplierGrid />
		<WildFlight />
	</MainContainer>

	{#if VisualOverlay}
		<VisualOverlay />
	{/if}
</App>
