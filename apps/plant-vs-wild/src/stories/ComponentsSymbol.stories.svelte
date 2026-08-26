<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	const { Story } = defineMeta({
		title: 'COMPONENTS/<Symbol>',
		component: Symbol,
		args: {
			x: 120,
			y: 120,
			rawSymbol: { name: 'W' },
			state: 'static',
		},
	});
</script>

<script lang="ts">
	import { Container, Rectangle, Text } from 'pixi-svelte';
	import { StoryPixiApp } from 'components-storybook';

	import Symbol from '../components/Symbol.svelte';
	import type { SymbolName } from '../game/types';
	import { SYMBOL_SIZE, CELL_SIZE } from '../game/constants';
	import assets from '../game/assets';

	/**
	 * Galeries de contrôle visuel des symboles.
	 *
	 * Elles montent le VRAI composant `Symbol.svelte` et le vrai `assets.ts` :
	 * les textures viennent de l'atlas TexturePacker, jamais de PNG isolés.
	 * Le texte affiché n'est qu'une étiquette sous le visuel.
	 */

	// Ordre déterministe : H1..H4, puis L1..L4, puis W.
	const ROWS: SymbolName[][] = [
		['H1', 'H2', 'H3', 'H4'],
		['L1', 'L2', 'L3', 'L4'],
		['W'],
	];

	// Une cellule = la taille du board (SYMBOL_SIZE) + de la marge pour l'étiquette.
	const CELL = SYMBOL_SIZE + 64;
	const LABEL_OFFSET = SYMBOL_SIZE * 0.62;

	const cellX = (column: number) => (column + 0.5) * CELL;
	const cellY = (row: number) => (row + 0.5) * CELL + 24;

	// Fonds de contrôle : révèlent halo, détourage et transparence.
	const CONTRAST_BACKGROUNDS = [0xffffff, 0x000000, 0xff00ff, 0x00ff88];

	const SIZES = [48, 96, 144, 192];
</script>

<!-- Un symbole isolé, réglable via les args Storybook. -->
<Story name="component">
	{#snippet template(args)}
		<StoryPixiApp {assets}>
			<Symbol {...args} />
		</StoryPixiApp>
	{/snippet}
</Story>

<!--
	Galerie principale : les 9 symboles à leur taille de board (96 px logiques).
	Une seule frame statique existe par symbole à ce stade.
-->
<Story name="symbols">
	{#snippet template()}
		<StoryPixiApp {assets}>
			{#each ROWS as row, rowIndex (rowIndex)}
				{#each row as name, columnIndex (name)}
					{@const x = cellX(columnIndex)}
					{@const y = cellY(rowIndex)}
					<Symbol {x} {y} rawSymbol={{ name }} state="static" />
					<Text
						{x}
						y={y + LABEL_OFFSET}
						anchor={{ x: 0.5, y: 0 }}
						text={name}
						style={{ fontFamily: 'system-ui, sans-serif', fontSize: 16, fill: 0x6b6b6b }}
					/>
				{/each}
			{/each}
		</StoryPixiApp>
	{/snippet}
</Story>

<!--
	Contrôle de découpe : chaque symbole sur quatre fonds unis très contrastés.
	Le liseré indique la case du board (CELL_SIZE) — il révèle centrage et débordement.
-->
<Story name="contrast check">
	{#snippet template()}
		<StoryPixiApp {assets}>
			<!-- 9 colonnes de CELL px dépassent la largeur du canvas : on met à l'échelle. -->
			<Container scale={0.85}>
			{#each CONTRAST_BACKGROUNDS as background, rowIndex (background)}
				{@const y = cellY(rowIndex)}
				<Rectangle
					x={0}
					y={y - CELL / 2}
					width={CELL * 9}
					height={CELL}
					backgroundColor={background}
				/>
				{#each ROWS.flat() as name, columnIndex (name)}
					{@const x = cellX(columnIndex)}
					<Rectangle
						anchor={{ x: 0.5, y: 0.5 }}
						{x}
						{y}
						width={CELL_SIZE}
						height={CELL_SIZE}
						backgroundAlpha={0}
						borderColor={0xff2d55}
						borderWidth={1}
					/>
					<Symbol {x} {y} rawSymbol={{ name }} state="static" />
				{/each}
			{/each}
			</Container>
		</StoryPixiApp>
	{/snippet}
</Story>

<!-- Comparaison d'échelle : 48 / 96 / 144 / 192 px logiques. -->
<Story name="sizes">
	{#snippet template()}
		<StoryPixiApp {assets}>
			{#each SIZES as size, index (size)}
				{@const x = 140 + index * 230}
				{@const y = 220}
				<Container scale={size / SYMBOL_SIZE} {x} {y}>
					<Symbol rawSymbol={{ name: 'W' }} state="static" />
				</Container>
				<Text
					{x}
					y={y + 130}
					anchor={{ x: 0.5, y: 0 }}
					text={`${size} px`}
					style={{ fontFamily: 'system-ui, sans-serif', fontSize: 16, fill: 0x6b6b6b }}
				/>
			{/each}
		</StoryPixiApp>
	{/snippet}
</Story>
