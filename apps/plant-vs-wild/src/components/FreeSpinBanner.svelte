<script lang="ts" module>
	/**
	 * Intro, retrigger et outro partagent un seul composant et gardent les noms
	 * d'events de `apps/cluster`. Le sample réutilise lui aussi son intro pour le
	 * retrigger : rien de nouveau n'est inventé ici.
	 *
	 * `freeSpinOutroCountUp` perd le `winLevelData` du sample — il dépend d'un
	 * `winLevelMap` et de sons que nous n'avons pas.
	 */
	export type EmitterEventFreeSpinBanner =
		| { type: 'freeSpinIntroShow' }
		| { type: 'freeSpinIntroHide' }
		| { type: 'freeSpinIntroUpdate'; totalFreeSpins: number }
		| { type: 'freeSpinOutroShow' }
		| { type: 'freeSpinOutroHide' }
		| { type: 'freeSpinOutroCountUp'; amount: number }
		/** Annonce d'une feature Bonus — même bandeau, autre texte. */
		| { type: 'featureAnnounce'; title: string; subtitle: string };
</script>

<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { Container, Rectangle, Text } from 'pixi-svelte';
	import { FadeContainer } from 'components-pixi';
	import { CanvasSizeRectangle } from 'components-layout';

	import { getContext } from '../game/context';
	import { FREE_SPIN_BANNER, TRANSITION_DURATION } from '../game/constants';

	/**
	 * Bandeau d'annonce du Bonus.
	 *
	 * `apps/cluster` s'appuie sur des animations Spine, une police bitmap et un
	 * écran « press to continue ». Nous n'avons rien de tout cela : le bandeau est
	 * un simple voile plus un texte, apparu et retiré en fondu.
	 *
	 * Le maintien à l'écran est un `Tween` awaité, pas un `setTimeout` : le
	 * bookEvent suivant ne démarre pas avant la fin de l'annonce.
	 */
	const context = getContext();

	let show = $state(false);
	let title = $state('');
	let subtitle = $state('');

	const hold = new Tween(0);

	/**
	 * Le bandeau est dessiné en coordonnées CANVAS, pas dans l'espace de design :
	 * sa largeur fixe déborderait d'un écran étroit. On la borne au viewport, et
	 * les textes suivent la même réduction.
	 */
	const canvasWidth = $derived(context.stateLayoutDerived.canvasSizes().width);
	const scale = $derived(
		Math.min(1, (canvasWidth * FREE_SPIN_BANNER.maxWidthRatio) / FREE_SPIN_BANNER.width),
	);

	const announce = async (nextTitle: string, nextSubtitle: string) => {
		title = nextTitle;
		subtitle = nextSubtitle;
		show = true;
		hold.set(0, { duration: 0 });
		await hold.set(1, { duration: FREE_SPIN_BANNER.holdDuration });
	};

	context.eventEmitter.subscribeOnMount({
		freeSpinIntroShow: () => (show = true),
		freeSpinIntroHide: () => (show = false),
		freeSpinIntroUpdate: async (emitterEvent) =>
			await announce(`${emitterEvent.totalFreeSpins} FREE SPINS`, 'BONUS'),
		freeSpinOutroShow: () => (show = true),
		freeSpinOutroHide: () => (show = false),
		freeSpinOutroCountUp: async (emitterEvent) =>
			await announce('BONUS TERMINE', `TOTAL ${emitterEvent.amount} (MOCK)`),
		featureAnnounce: async (emitterEvent) => {
			await announce(emitterEvent.title, emitterEvent.subtitle);
			show = false;
		},
	});
</script>

{#if show}
	<CanvasSizeRectangle
		backgroundColor={FREE_SPIN_BANNER.veilColor}
		backgroundAlpha={FREE_SPIN_BANNER.veilAlpha}
		zIndex={FREE_SPIN_BANNER.zIndex}
	/>
{/if}

<FadeContainer {show} duration={TRANSITION_DURATION.banner} zIndex={FREE_SPIN_BANNER.zIndex + 1}>
	<Container
		x={context.stateLayoutDerived.canvasSizes().width * 0.5}
		y={context.stateLayoutDerived.canvasSizes().height * 0.5}
	>
		<Rectangle
			anchor={{ x: 0.5, y: 0.5 }}
			width={FREE_SPIN_BANNER.width * scale}
			height={FREE_SPIN_BANNER.height * scale}
			borderRadius={18}
			backgroundColor={FREE_SPIN_BANNER.backgroundColor}
			backgroundAlpha={FREE_SPIN_BANNER.backgroundAlpha}
			borderColor={FREE_SPIN_BANNER.borderColor}
			borderAlpha={FREE_SPIN_BANNER.borderAlpha}
			borderWidth={2}
		/>
		<Text
			y={-FREE_SPIN_BANNER.height * scale * 0.16}
			anchor={{ x: 0.5, y: 0.5 }}
			text={title}
			style={{
				fontFamily: FREE_SPIN_BANNER.fontFamily,
				fontSize: FREE_SPIN_BANNER.titleSize * scale,
				fontWeight: 'bold',
				fill: FREE_SPIN_BANNER.titleFill,
			}}
		/>
		<Text
			y={FREE_SPIN_BANNER.height * scale * 0.2}
			anchor={{ x: 0.5, y: 0.5 }}
			text={subtitle}
			style={{
				fontFamily: FREE_SPIN_BANNER.fontFamily,
				fontSize: FREE_SPIN_BANNER.subtitleSize * scale,
				fill: FREE_SPIN_BANNER.subtitleFill,
			}}
		/>
	</Container>
</FadeContainer>
