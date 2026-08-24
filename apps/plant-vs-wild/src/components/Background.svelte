<script lang="ts">
	import { Rectangle, Sprite } from 'pixi-svelte';

	import { getContext } from '../game/context';
	import { zIndexes } from '../game/constants';

	const context = getContext();

	/**
	 * Deux fonds, un par orientation.
	 *
	 * `isStacked()` est le regroupement Stake des layouts « debout » — portrait et
	 * presque carré. `apps/lines` s'en sert déjà pour son positionnement portrait.
	 *
	 * Chaque fond a son propre helper de cadrage : `normalBackgroundLayout` et
	 * `portraitBackgroundLayout` lisent respectivement `backgroundRatio.normal` et
	 * `backgroundRatio.portrait`, déclarés dans `stateLayout.ts` d'après les
	 * dimensions RÉELLES de chaque asset. C'est ce qui produit le comportement
	 * cover : un ratio faux étirerait sur le mauvais axe et laisserait des bandes.
	 */
	const stacked = $derived(context.stateLayoutDerived.isStacked());

	const backgroundProps = $derived(
		stacked
			? context.stateLayoutDerived.portraitBackgroundLayout({ scale: 1 })
			: context.stateLayoutDerived.normalBackgroundLayout({ scale: 1 }),
	);
</script>

<Rectangle
	{...context.stateLayoutDerived.canvasSizes()}
	backgroundColor={0x000000}
	zIndex={zIndexes.background.backdrop}
/>

<Sprite
	key={stacked ? 'backgroundMobile' : 'background'}
	anchor={{ x: 0.5, y: 0.5 }}
	zIndex={zIndexes.background.normal}
	{...backgroundProps}
/>
