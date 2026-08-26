<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	const { Story } = defineMeta({
		title: 'MODE_BONUS/feature',
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
	import feature from './data/base_book_feature';

	/**
	 * Features Bonus. Tout vient de Books écrits à la main : aucune fréquence,
	 * aucun trajet, aucun symbole n'est choisi par le frontend.
	 */
	setContext();

	const events = feature.featureEvents;
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

<!-- Snake : trajet court, conversion vers un Low. -->
<Story
	name="snake move court Low"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.snakeReveal, events.rageGrid, events.snakeShort],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Snake : trajet long, conversion vers un High. -->
<Story
	name="snake move long High"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [events.snakeReveal, events.rageGrid, events.snakeLong],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Snake puis résolution normale sur le plateau produit. -->
<Story
	name="snake book complet"
	args={templateArgs({
		skipLoadingScreen: true,
		data: feature.bookWildSnake.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Rage : recentrage, renouvellement, multiplicateurs conservés. -->
<Story
	name="rage book complet"
	args={templateArgs({
		skipLoadingScreen: true,
		data: feature.bookRage.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Wild Split : 1 permanent + 3 temporaires, consommation, nettoyage. -->
<Story
	name="wild split book complet"
	args={templateArgs({
		skipLoadingScreen: true,
		data: feature.bookWildSplit.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>
