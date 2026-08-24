<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	const { Story } = defineMeta({
		title: 'MODE_BASE/tumble step',
	});
</script>

<script lang="ts">
	import {
		StoryGameTemplate,
		StoryLocale,
		type TemplateArgs,
		templateArgs,
	} from 'components-storybook';

	import Game from '../components/Game.svelte';
	import { setContext } from '../game/context';
	import { playBookEvent } from '../game/utils';
	import { eventEmitter } from '../game/eventEmitter';
	import book from './data/base_book_cascade';

	/**
	 * Les étapes du tumble, une par une.
	 *
	 * `tumbleBoard` est un bookEvent qui se décompose en emitterEvents simples.
	 * Ces stories les déclenchent isolément pour pouvoir observer chaque étape
	 * sans que la suivante l'efface. Elles s'arrêtent volontairement en cours de
	 * cascade — le plateau y est donc dans un état intermédiaire, c'est voulu.
	 */
	setContext();

	/** Amène le plateau à l'entrée du tumble, avec les arrivants déjà préparés. */
	const enterTumble = async () => {
		await playBookEvent(book.reveal, { bookEvents: [] });
		eventEmitter.broadcast({ type: 'boardHide' });
		eventEmitter.broadcast({ type: 'tumbleBoardShow' });
		eventEmitter.broadcast({ type: 'tumbleBoardInit', addingBoard: book.tumbleBoard.newSymbols });
	};

	const explode = async () => {
		await enterTumble();
		await eventEmitter.broadcastAsync({
			type: 'tumbleBoardExplode',
			explodingPositions: book.tumbleBoard.explodingSymbols,
		});
	};

	const removeExploded = async () => {
		await explode();
		eventEmitter.broadcast({ type: 'tumbleBoardRemoveExploded' });
	};

	const slideDown = async () => {
		await removeExploded();
		await eventEmitter.broadcastAsync({ type: 'tumbleBoardSlideDown' });
	};
</script>

{#snippet template(args: TemplateArgs<any>)}
	<StoryGameTemplate
		skipLoadingScreen={args.skipLoadingScreen}
		action={async () => {
			await args.action?.(args.data);
		}}
	>
		<StoryLocale lang="en">
			<Game />
		</StoryLocale>
	</StoryGameTemplate>
{/snippet}

<!-- B — le plateau de tumble prend le relais, les arrivants attendent hors champ -->
<Story
	name="step 1 init"
	args={templateArgs({ skipLoadingScreen: true, action: enterTumble })}
	{template}
/>

<!-- C — les cases désignées par le book explosent -->
<Story name="step 2 explode" args={templateArgs({ skipLoadingScreen: true, action: explode })} {template} />

<!-- D — les symboles explosés sont retirés, des trous apparaissent -->
<Story
	name="step 3 remove exploded"
	args={templateArgs({ skipLoadingScreen: true, action: removeExploded })}
	{template}
/>

<!-- E — tout descend et les nouveaux symboles entrent -->
<Story
	name="step 4 slide down"
	args={templateArgs({ skipLoadingScreen: true, action: slideDown })}
	{template}
/>
