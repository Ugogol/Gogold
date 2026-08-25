<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	const { Story } = defineMeta({
		title: 'MODE_BASE/multiplier',
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
	import multiplier from './data/base_book_multiplier';

	/**
	 * Multiplicateurs de case, grille par grille.
	 *
	 * Chaque story envoie un `updateGrid` écrit à la main : le frontend affiche
	 * exactement ce qu'il reçoit et ne calcule aucune progression.
	 */
	setContext();

	const events = multiplier.multiplierEvents;
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
	name="grille vide"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.reveal, events.empty],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<Story
	name="une case x2"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.reveal, events.single],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<Story
	name="plusieurs x2"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.reveal, events.severalX2],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<Story
	name="x2 x4 x8"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.reveal, events.stack],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<Story
	name="valeurs elevees"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.reveal, events.mixed],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<Story
	name="cap x4096"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.reveal, events.cap],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Pire cas d'encombrement : les 25 cases occupées. -->
<Story
	name="grille pleine"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.reveal, events.full],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- updateGrid seul, sans plateau : la grille ne dépend pas du contenu du board. -->
<Story
	name="updateGrid isole"
	args={templateArgs({
		skipLoadingScreen: true,
		data: events.mixed,
		action: async (data) => await playBookEvent(data, { bookEvents: [] }),
	})}
	{template}
/>

<!-- Deux cascades : x2 puis x4 sur les cases réutilisées. -->
<Story
	name="cascade x2 puis x4"
	args={templateArgs({
		skipLoadingScreen: true,
		data: multiplier.bookMultiplierCascade.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Nouveau spin : la grille repart vide, sur ordre du Book. -->
<Story
	name="reset base game"
	args={templateArgs({
		skipLoadingScreen: true,
		data: multiplier.bookMultiplierResetSpin.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Fin de pari : finalWin vide et masque la grille. -->
<Story
	name="fin de pari"
	args={templateArgs({
		skipLoadingScreen: true,
		data: multiplier.bookMultiplierFinalWin.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Wild et multiplicateurs dans la même connexion, sans dépendance entre eux. -->
<Story
	name="avec le Wild"
	args={templateArgs({
		skipLoadingScreen: true,
		data: multiplier.bookMultiplierWithWild.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>
