<script lang="ts" module>
	/** Mêmes events que `apps/cluster` : aucun renommage. */
	export type EmitterEventFreeSpinCounter =
		| { type: 'freeSpinCounterShow' }
		| { type: 'freeSpinCounterHide' }
		| { type: 'freeSpinCounterUpdate'; current?: number; total?: number };
</script>

<script lang="ts">
	import { Container, Rectangle, Text } from 'pixi-svelte';
	import { FadeContainer } from 'components-pixi';
	import { MainContainer } from 'components-layout';

	import { getContext } from '../game/context';
	import { SYMBOL_SIZE, FREE_SPIN_PANEL, TRANSITION_DURATION } from '../game/constants';

	/**
	 * Compteur de Free Spins.
	 *
	 * `apps/cluster` le pose à gauche du plateau, sur un `Sprite` de panneau et en
	 * `BitmapText` police `gold`. Nous n'avons ni ce panneau ni cette police : le
	 * compteur est donc dessiné en `Text` sur une pastille, et placé AU-DESSUS du
	 * plateau — à gauche il déborderait de l'écran en portrait.
	 *
	 * Il n'incrémente rien : il affiche `current` et `total` tels que le Book les
	 * envoie via `updateFreeSpin`.
	 */
	const context = getContext();

	let show = $state(false);
	let current = $state(0);
	let total = $state(0);

	const boardLayout = $derived(context.stateGameDerived.boardLayout());
	const position = $derived({
		x: boardLayout.x,
		y: boardLayout.y - boardLayout.height * 0.5 - SYMBOL_SIZE * 0.42,
	});

	context.eventEmitter.subscribeOnMount({
		freeSpinCounterShow: () => (show = true),
		freeSpinCounterHide: () => (show = false),
		freeSpinCounterUpdate: (emitterEvent) => {
			if (emitterEvent.current !== undefined) current = emitterEvent.current;
			if (emitterEvent.total !== undefined) total = emitterEvent.total;
		},
	});

	const label = $derived(`FREE SPIN ${current} / ${total}`);
</script>

<MainContainer>
	<FadeContainer {show} duration={TRANSITION_DURATION.counter}>
		<Container {...position}>
			<Rectangle
				anchor={{ x: 0.5, y: 0.5 }}
				width={FREE_SPIN_PANEL.width}
				height={FREE_SPIN_PANEL.height}
				borderRadius={FREE_SPIN_PANEL.height * 0.5}
				backgroundColor={FREE_SPIN_PANEL.backgroundColor}
				backgroundAlpha={FREE_SPIN_PANEL.backgroundAlpha}
				borderColor={FREE_SPIN_PANEL.borderColor}
				borderAlpha={FREE_SPIN_PANEL.borderAlpha}
				borderWidth={1}
			/>
			<Text
				anchor={{ x: 0.5, y: 0.5 }}
				text={label}
				style={{
					fontFamily: FREE_SPIN_PANEL.fontFamily,
					fontSize: FREE_SPIN_PANEL.fontSize,
					fontWeight: 'bold',
					fill: FREE_SPIN_PANEL.fill,
				}}
			/>
		</Container>
	</FadeContainer>
</MainContainer>
