<script lang="ts" module>
	/**
	 * Mêmes noms d'events que `apps/cluster` : la grille s'affiche, se met à jour,
	 * se vide, se cache. Aucun event inventé — `updateGrid` suffit côté Book.
	 */
	export type EmitterEventMultiplierGrid =
		| { type: 'multiplierGridShow' }
		| { type: 'multiplierGridHide' }
		| { type: 'multiplierGridUpdate'; grid: number[][] }
		| { type: 'multiplierGridClear' };
</script>

<script lang="ts">
	import _ from 'lodash';
	import { Container, Rectangle, Text } from 'pixi-svelte';

	import BoardContainer from './BoardContainer.svelte';
	import { getSymbolX, getSymbolY } from '../game/utils';
	import { getContext } from '../game/context';
	import { BOARD_DIMENSIONS, CELL_SIZE, MULTIPLIER_BADGE, zIndexes } from '../game/constants';

	/**
	 * Multiplicateurs de case.
	 *
	 * Le multiplicateur appartient à LA POSITION, jamais au symbole : ce calque
	 * est indexé par la case et ne connaît rien du contenu du plateau. Un symbole
	 * peut exploser, tomber, être remplacé — la valeur reste.
	 *
	 * ⚠️ INDEXATION — `grid[reel][row]` utilise les LIGNES VISIBLES (0 à 4), pas
	 * l'indexation paddée du board. `getSymbolY` attend précisément un index de
	 * ligne visible : la valeur s'y branche donc sans conversion. Voir
	 * `boardRowToGridRow` dans `game/utils.ts` pour la frontière entre les deux.
	 *
	 * Le frontend ne calcule aucune progression : il affiche la grille reçue.
	 */
	const context = getContext();

	/** Grille neutre : que des zéros, donc aucun badge. */
	const emptyGrid = () =>
		_.range(BOARD_DIMENSIONS.x).map(() => _.range(BOARD_DIMENSIONS.y).map(() => 0));

	let show = $state(false);
	let grid = $state(emptyGrid());

	context.eventEmitter.subscribeOnMount({
		multiplierGridShow: () => (show = true),
		multiplierGridHide: () => (show = false),
		multiplierGridUpdate: (emitterEvent) => (grid = emitterEvent.grid),
		multiplierGridClear: () => (grid = emptyGrid()),
	});

	/**
	 * `0` comme `1` valent le x1 implicite : rien n'est dessiné. Les books Stake
	 * réels envoient `0` pour une case neutre ; on accepte les deux.
	 */
	const badges = $derived(
		grid.flatMap((reel, reelIndex) =>
			reel.flatMap((multiplier, gridRow) =>
				multiplier > 1
					? [{ key: `${reelIndex}-${gridRow}`, reelIndex, gridRow, multiplier }]
					: [],
			),
		),
	);

	/** Le badge se rétrécit pour les grandes valeurs : `x4096` ne déborde jamais. */
	const badgeWidth = (multiplier: number) =>
		Math.min(CELL_SIZE * 0.92, MULTIPLIER_BADGE.paddingX * 2 + `x${multiplier}`.length * MULTIPLIER_BADGE.charWidth);
</script>

{#if show}
	<BoardContainer zIndex={zIndexes.multiplierGrid}>
		{#each badges as badge (badge.key)}
			<Container
				x={getSymbolX(badge.reelIndex)}
				y={getSymbolY(badge.gridRow) + CELL_SIZE * MULTIPLIER_BADGE.offsetRatio}
			>
				<Rectangle
					anchor={{ x: 0.5, y: 0.5 }}
					width={badgeWidth(badge.multiplier)}
					height={MULTIPLIER_BADGE.height}
					borderRadius={MULTIPLIER_BADGE.height * 0.5}
					backgroundColor={MULTIPLIER_BADGE.backgroundColor}
					backgroundAlpha={MULTIPLIER_BADGE.backgroundAlpha}
					borderColor={MULTIPLIER_BADGE.borderColor}
					borderAlpha={MULTIPLIER_BADGE.borderAlpha}
					borderWidth={1}
				/>
				<Text
					anchor={{ x: 0.5, y: 0.5 }}
					text={`x${badge.multiplier}`}
					style={{
						fontFamily: MULTIPLIER_BADGE.fontFamily,
						fontSize: MULTIPLIER_BADGE.fontSize,
						fontWeight: 'bold',
						fill: MULTIPLIER_BADGE.fill,
					}}
				/>
			</Container>
		{/each}
	</BoardContainer>
{/if}
