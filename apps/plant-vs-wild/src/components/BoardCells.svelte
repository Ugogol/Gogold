<script lang="ts">
	import _ from 'lodash';
	import { Rectangle } from 'pixi-svelte';

	import BoardContainer from './BoardContainer.svelte';
	import { getSymbolX, getSymbolY } from '../game/utils';
	import { CELL_SIZE, CELL_STYLE, BOARD_DIMENSIONS } from '../game/constants';

	/**
	 * Les 25 cases de la grille, dessinées sous les symboles.
	 *
	 * Il n'y a volontairement AUCUN cadre ni panneau autour : la grille est
	 * constituée des seules cases, posées directement sur le décor. Le cadre
	 * décoratif a été abandonné (étape 3).
	 *
	 * Les cases sont positionnées avec `getSymbolX` / `getSymbolY`, les mêmes
	 * fonctions que les symboles : l'alignement est garanti par construction, pas
	 * par des valeurs recopiées.
	 */
	const columns = _.range(BOARD_DIMENSIONS.x);
	const rows = _.range(BOARD_DIMENSIONS.y);
</script>

<BoardContainer>
	{#each columns as column (column)}
		{#each rows as row (row)}
			<Rectangle
				{...CELL_STYLE}
				anchor={{ x: 0.5, y: 0.5 }}
				x={getSymbolX(column)}
				y={getSymbolY(row)}
				width={CELL_SIZE}
				height={CELL_SIZE}
			/>
		{/each}
	{/each}
</BoardContainer>
