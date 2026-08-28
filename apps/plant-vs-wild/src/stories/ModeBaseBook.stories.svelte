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
	import wincapBook from '../dev/generated-books/v5-wincap.json';
	import type { BookEvent } from '../game/typesBookEvent';

	/**
	 * Le book complet, du reveal à la fin de résolution.
	 * Rejouable : chaque lancement repart du `reveal`, qui réécrit tout le plateau.
	 */
	setContext();

	/**
	 * Book V5 réel atteignant le plafond de 10 000x — sim 10917, 158 events.
	 *
	 * Extrait de la population réellement pondérée par BALANCING_V5, sans aucune
	 * retouche. C'est la validation principale du support `wincap` : la séquence
	 * complète, pas l'event isolé. Le Bonus CONTINUE après le plafond, et tous
	 * les `setTotalWin` suivants valent le montant écrêté.
	 */
	const wincapEvents = wincapBook.events as BookEvent[];
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

<Story
	name="WINCAP — Book V5 complet, 10 000x"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wincapEvents,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>
