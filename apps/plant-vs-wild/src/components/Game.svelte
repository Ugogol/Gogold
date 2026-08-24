<script lang="ts">
	import { App } from 'pixi-svelte';
	import { EnablePixiExtension } from 'components-pixi';
	import { MainContainer } from 'components-layout';

	import Background from './Background.svelte';
	import Board from './Board.svelte';

	/**
	 * Squelette de PLANT VS WILD.
	 *
	 * Ne contient volontairement ni UI de mise, ni son, ni écran de chargement,
	 * ni machine de pari : ces briques arriveront avec le contrat RGS/math.
	 * Seul le plateau est monté, pour valider l'architecture de rendu.
	 */
</script>

<App>
	<EnablePixiExtension />

	<Background />

	<MainContainer>
		<Board />
	</MainContainer>
</App>
