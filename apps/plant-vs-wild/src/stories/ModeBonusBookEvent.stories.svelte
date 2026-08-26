<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	const { Story } = defineMeta({
		title: 'MODE_BONUS/bookEvent',
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
	import bonus from './data/base_book_bonus';

	/**
	 * Un bookEvent Bonus à la fois, joué par le vrai pipeline.
	 * Organisation reprise du sample `apps/cluster` : MODE_BONUS/bookEvent.
	 *
	 * Aucun de ces events n'est spécifique à PLANT VS WILD : ce sont ceux de
	 * Stake, `freeSpinTrigger`, `updateFreeSpin`, `freeSpinRetrigger`,
	 * `freeSpinEnd`.
	 */
	setContext();

	const events = bonus.bonusEvents;
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

<!-- Plateau de Bonus : il contient H4, rendu comme n'importe quel symbole. -->
<Story
	name="board bonus avec H4"
	args={templateArgs({
		skipLoadingScreen: true,
		data: events.bonusReveal,
		action: async (data) => await playBookEvent(data, { bookEvents: [] }),
	})}
	{template}
/>

<!-- Déclenchement : bandeau d'intro puis compteur à 10. -->
<Story
	name="freeSpinTrigger"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.bonusReveal, events.freeSpinTrigger],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Compteur seul : les deux valeurs viennent du Book. -->
<Story
	name="updateFreeSpin"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.bonusReveal, events.updateFreeSpin],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Retrigger : totalFs est le NOUVEAU total, 15, jamais un incrément. -->
<Story
	name="freeSpinRetrigger +5"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.bonusReveal, events.updateFreeSpin, events.freeSpinRetrigger],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Grille héritée du spin déclencheur, sans aucun recalcul. -->
<Story
	name="grille heritee"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.bonusReveal, events.inheritedGrid],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Sortie du Bonus : bandeau, retour au mode Base, compteur masqué. -->
<Story
	name="freeSpinEnd"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.bonusReveal, events.updateFreeSpin, events.freeSpinEnd],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>
