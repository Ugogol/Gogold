<script lang="ts">
	import { Rectangle, Sprite } from 'pixi-svelte';
	import { FadeContainer } from 'components-pixi';

	import { getContext } from '../game/context';
	import { zIndexes, TRANSITION_DURATION } from '../game/constants';

	const context = getContext();

	/**
	 * Quatre fonds : Base et Bonus, chacun couché ou debout.
	 *
	 * `isStacked()` est le regroupement Stake des layouts « debout » — portrait et
	 * presque carré. `gameType` est l'unique source du mode, celle que les
	 * handlers `freeSpinTrigger` et `freeSpinEnd` basculent : aucun état parallèle
	 * n'est créé pour le Bonus.
	 *
	 * Chaque fond a son helper de cadrage : `normalBackgroundLayout` et
	 * `portraitBackgroundLayout` lisent respectivement `backgroundRatio.normal` et
	 * `backgroundRatio.portrait`, déclarés d'après les dimensions RÉELLES des
	 * assets. Les quatre partagent les deux mêmes ratios, aucun réglage à ajouter.
	 *
	 * Le passage Base ↔ Bonus est un fondu croisé : `FadeContainer` de
	 * `components-pixi`, comme dans `apps/cluster`. Aucun système de transition
	 * maison.
	 */
	const stacked = $derived(context.stateLayoutDerived.isStacked());
	const isBonus = $derived(context.stateGame.gameType === 'freegame');

	const backgroundProps = $derived(
		stacked
			? context.stateLayoutDerived.portraitBackgroundLayout({ scale: 1 })
			: context.stateLayoutDerived.normalBackgroundLayout({ scale: 1 }),
	);

	const baseKey = $derived(stacked ? 'backgroundMobile' : 'background');
	const bonusKey = $derived(stacked ? 'backgroundBonusMobile' : 'backgroundBonus');
</script>

<Rectangle
	{...context.stateLayoutDerived.canvasSizes()}
	backgroundColor={0x000000}
	zIndex={zIndexes.background.backdrop}
/>

<FadeContainer show={!isBonus} duration={TRANSITION_DURATION.background} zIndex={zIndexes.background.normal}>
	<Sprite key={baseKey} anchor={{ x: 0.5, y: 0.5 }} {...backgroundProps} />
</FadeContainer>

<FadeContainer show={isBonus} duration={TRANSITION_DURATION.background} zIndex={zIndexes.background.bonus}>
	<Sprite key={bonusKey} anchor={{ x: 0.5, y: 0.5 }} {...backgroundProps} />
</FadeContainer>
