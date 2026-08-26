<script lang="ts">
	import type { Snippet } from 'svelte';

	import { Container } from 'pixi-svelte';

	import { getContext } from '../game/context';

	type Props = {
		children: Snippet;
		/**
		 * Ordre de dessin entre les calques du plateau.
		 *
		 * `pixi-svelte` appelle `sortChildren()` du parent après chaque ajout : le
		 * zIndex fait donc autorité, et c'est le SEUL moyen fiable d'ordonner les
		 * calques. L'ordre de montage ne suffit pas — un composant qui se démonte
		 * et se remonte (le plateau pendant un tumble) repasserait devant.
		 */
		zIndex?: number;
	};

	const props: Props = $props();

	const context = getContext();
</script>

<Container
	zIndex={props.zIndex ?? 0}
	x={context.stateGameDerived.boardLayout().x}
	y={context.stateGameDerived.boardLayout().y}
	pivot={context.stateGameDerived.boardLayout().pivot}
>
	{@render props.children()}
</Container>
