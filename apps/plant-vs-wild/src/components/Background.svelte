<script lang="ts">
	import { Rectangle, Sprite } from 'pixi-svelte';

	import { getContext } from '../game/context';
	import { zIndexes } from '../game/constants';

	const context = getContext();

	// `normalBackgroundLayout` fixe une seule dimension : le sprite garde son
	// ratio et couvre le canvas quel que soit le format d'écran.
	const backgroundProps = $derived(
		context.stateLayoutDerived.normalBackgroundLayout({ scale: 1 }),
	);
</script>

<Rectangle
	{...context.stateLayoutDerived.canvasSizes()}
	backgroundColor={0x000000}
	zIndex={zIndexes.background.backdrop}
/>

<Sprite key="background" anchor={{ x: 0.5, y: 0.5 }} zIndex={zIndexes.background.normal} {...backgroundProps} />
