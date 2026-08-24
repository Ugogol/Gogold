<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	const { Story } = defineMeta({
		title: 'MODE_BASE/book',
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
	import { playBookEvents } from '../game/utils';
	import book from './data/base_book_cascade';

	/**
	 * Le book complet, du reveal à la fin de résolution.
	 * Rejouable : chaque lancement repart du `reveal`, qui réécrit tout le plateau.
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
	name="cascade simple"
	args={templateArgs({
		skipLoadingScreen: true,
		data: book.bookEvents,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>
