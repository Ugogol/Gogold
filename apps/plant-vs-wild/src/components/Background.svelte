<script lang="ts">
	import { Rectangle } from 'pixi-svelte';

	import { getContext } from '../game/context';
	import { zIndexes } from '../game/constants';

	/** Fond provisoire : aucune image n'est intégrée à ce stade. */
	const context = getContext();
</script>

<Rectangle
	zIndex={zIndexes.background.backdrop}
	width={context.stateLayoutDerived.canvasSizes().width}
	height={context.stateLayoutDerived.canvasSizes().height}
	backgroundColor={0x101a12}
/>
