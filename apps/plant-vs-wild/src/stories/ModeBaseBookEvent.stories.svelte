<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	const { Story } = defineMeta({
		title: 'MODE_BASE/bookEvent',
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
	import { playBookEvent, playBookEvents } from '../game/utils';
	import book from './data/base_book_cascade';

	/**
	 * Un bookEvent à la fois, joué par le vrai pipeline.
	 * Organisation reprise du sample `apps/cluster` : MODE_BASE/bookEvent.
	 *
	 * `winInfo` et `tumbleBoard` supposent un plateau déjà révélé : leur action
	 * rejoue donc `reveal` d'abord. C'est du séquencement de fixtures, pas de la
	 * logique de jeu.
	 */
	setContext();
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

<Story
	name="reveal"
	args={templateArgs({
		skipLoadingScreen: true,
		data: book.reveal,
		action: async (data) => await playBookEvent(data, { bookEvents: [] }),
	})}
	{template}
/>

<Story
	name="winInfo — cluster mis en évidence"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [book.reveal, book.winInfo],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<Story
	name="tumbleBoard — explosion, chute, refill"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [book.reveal, book.tumbleBoard],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<Story
	name="setTotalWin"
	args={templateArgs({
		skipLoadingScreen: true,
		data: book.setTotalWin,
		action: async (data) => await playBookEvent(data, { bookEvents: [] }),
	})}
	{template}
/>
