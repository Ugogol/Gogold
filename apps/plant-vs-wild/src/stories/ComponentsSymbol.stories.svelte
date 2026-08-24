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
	import { Container, Text } from 'pixi-svelte';
	import { StoryPixiApp } from 'components-storybook';

	import Symbol from '../components/Symbol.svelte';
	import { SYMBOL_STATES } from '../game/types';
	import type { SymbolName } from '../game/types';
	import assets from '../game/assets';

	const CELL = 150;

	// Jeu de symboles déterministe : aucun tirage aléatoire.
	const SYMBOLS: SymbolName[] = ['H1', 'H2', 'H3', 'H4', 'L1', 'L2', 'L3', 'L4', 'W', 'S'];
</script>

<Story name="component">
	{#snippet template(args)}
		<StoryPixiApp {assets}>
			<Symbol {...args} />
		</StoryPixiApp>
	{/snippet}
</Story>

<Story name="symbols">
	{#snippet template()}
		<StoryPixiApp {assets}>
			<Container scale={0.62}>
				{#each SYMBOLS as name, rowIndex (name)}
					{#each SYMBOL_STATES as state, columnIndex (state)}
						{@const x = (columnIndex + 1) * CELL}
						{@const y = (rowIndex + 1) * CELL}
						<Text
							{x}
							y={y - 62}
							anchor={{ x: 0.5, y: 0 }}
							text={`${name}: ${state}`}
							style={{ fontSize: 20, fill: 0x2b2b2b }}
						/>
						<Symbol {x} {y} rawSymbol={{ name }} {state} />
					{/each}
				{/each}
			</Container>
		</StoryPixiApp>
	{/snippet}
</Story>
