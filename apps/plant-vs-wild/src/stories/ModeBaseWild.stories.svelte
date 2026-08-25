<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	const { Story } = defineMeta({
		title: 'MODE_BASE/wild',
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
	import wild from './data/base_book_wild';

	/**
	 * Le Wild, état par état et scénario par scénario.
	 *
	 * Tout vient de Books écrits à la main : le frontend ne fait apparaître aucun
	 * Wild, n'en déplace aucun de sa propre initiative et ne compte aucune charge.
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

<!-- Les 4 états graphiques, plus l'état d'attente du Bonus. -->
<Story
	name="state 0"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.wildEvents.revealCharge0,
		action: async (data) => await playBookEvent(data, { bookEvents: [] }),
	})}
	{template}
/>

<Story
	name="state 1"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.wildEvents.revealCharge1,
		action: async (data) => await playBookEvent(data, { bookEvents: [] }),
	})}
	{template}
/>

<Story
	name="state 2"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.wildEvents.revealCharge2,
		action: async (data) => await playBookEvent(data, { bookEvents: [] }),
	})}
	{template}
/>

<Story
	name="state 3"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.wildEvents.revealCharge3,
		action: async (data) => await playBookEvent(data, { bookEvents: [] }),
	})}
	{template}
/>

<Story
	name="state 4 bonus pending"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.wildEvents.revealCharge4,
		action: async (data) => await playBookEvent(data, { bookEvents: [] }),
	})}
	{template}
/>

<!-- A — le Wild est déjà sur le plateau initial. -->
<Story
	name="apparition A reveal"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.bookWildAtReveal.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- B — le Wild arrive parmi les nouveaux symboles d'un refill. -->
<Story
	name="apparition B refill"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.bookWildFromRefill.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- C — le Wild occupe une case que la connexion vient de libérer. -->
<Story
	name="apparition C case liberee"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.bookWildInReleasedCell.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- La connexion 3 symboles + Wild, mise en évidence seule. -->
<Story
	name="connexion highlight"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [wild.wildEvents.revealCharge0, wild.wildEvents.winInfo],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Le déplacement seul : reveal puis wildMove, sans refill. -->
<Story
	name="wildMove isole"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [wild.wildEvents.revealCharge0, wild.wildEvents.wildMove],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- La connexion complète : highlight, déplacement, montée de charge, refill. -->
<Story
	name="connexion complete 0 vers 1"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.bookWildCharge1.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<Story
	name="connexion 1 vers 2"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.bookWildCharge2.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<Story
	name="connexion 2 vers 3"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.bookWildCharge3.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- 4e connexion : la charge atteint le maximum, le Bonus NE démarre PAS. -->
<Story
	name="connexion 3 vers 4 bonus pending"
	args={templateArgs({
		skipLoadingScreen: true,
		data: wild.bookWildBonusPending.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>
