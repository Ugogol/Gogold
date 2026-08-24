<script lang="ts">
	import { App } from 'pixi-svelte';
	import { EnablePixiExtension } from 'components-pixi';
	import { MainContainer } from 'components-layout';

	import Background from './Background.svelte';
	import BoardCells from './BoardCells.svelte';
	import Board from './Board.svelte';

	/**
	 * Squelette de PLANT VS WILD.
	 *
	 * Ni UI de mise, ni son, ni écran de chargement, ni machine de pari : ces
	 * briques arriveront avec le contrat RGS/math. Seuls le fond, la zone de jeu
	 * et le plateau sont montés, pour valider l'intégration des assets.
	 *
	 * Le décor `sprites/board` n'est plus monté : `BoardCells` tient lieu de zone
	 * de jeu en attendant un nouveau cadre.
	 */
</script>

<App>
	<EnablePixiExtension />

	<Background />

	<MainContainer>
		<BoardCells />
		<Board />
	</MainContainer>
</App>
