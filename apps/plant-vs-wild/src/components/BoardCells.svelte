<script lang="ts">
	import _ from 'lodash';
	import { Rectangle } from 'pixi-svelte';

	import BoardContainer from './BoardContainer.svelte';
	import { getSymbolX, getSymbolY } from '../game/utils';
	import { SYMBOL_SIZE, CELL_GAP, CELL_SIZE, BOARD_DIMENSIONS } from '../game/constants';

	/**
	 * Zone de jeu provisoire : une case translucide par position visible.
	 *
	 * Remplace le décor `sprites/board`, retiré en attendant un nouveau cadre.
	 * Les cases sont posées avec `getSymbolX` / `getSymbolY`, les mêmes fonctions
	 * que les symboles : l'alignement est garanti par construction.
	 */
	const columns = _.range(BOARD_DIMENSIONS.x);
	const rows = _.range(BOARD_DIMENSIONS.y);

	/**
	 * Le fond est cadré sur les cases réellement dessinées, pas sur `BOARD_SIZES` :
	 * `REEL_PADDING` décale les centres de colonnes, un cadrage sur le pas de la
	 * grille laisserait une gouttière asymétrique.
	 */
	const span = (count: number) => SYMBOL_SIZE * (count - 1) + CELL_SIZE + CELL_GAP * 2;

	const zone = {
		x: (getSymbolX(0) + getSymbolX(BOARD_DIMENSIONS.x - 1)) / 2,
		y: (getSymbolY(0) + getSymbolY(BOARD_DIMENSIONS.y - 1)) / 2,
		width: span(BOARD_DIMENSIONS.x),
		height: span(BOARD_DIMENSIONS.y),
	};
</script>

<BoardContainer>
	<Rectangle
		anchor={{ x: 0.5, y: 0.5 }}
		x={zone.x}
		y={zone.y}
		width={zone.width}
		height={zone.height}
		borderRadius={18}
		backgroundColor={0x000000}
		backgroundAlpha={0.25}
		borderColor={0xffffff}
		borderAlpha={0.12}
		borderWidth={1}
	/>

	{#each columns as column (column)}
		{#each rows as row (row)}
			<Rectangle
				anchor={{ x: 0.5, y: 0.5 }}
				x={getSymbolX(column)}
				y={getSymbolY(row)}
				width={CELL_SIZE}
				height={CELL_SIZE}
				borderRadius={10}
				backgroundColor={0xffffff}
				backgroundAlpha={0.08}
				borderColor={0xffffff}
				borderAlpha={0.16}
				borderWidth={1}
			/>
		{/each}
	{/each}
</BoardContainer>
