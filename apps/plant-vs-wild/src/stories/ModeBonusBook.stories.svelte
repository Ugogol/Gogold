<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	const { Story } = defineMeta({
		title: 'MODE_BONUS/book',
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
	import bonus from './data/base_book_bonus';

	/**
	 * Books Bonus complets.
	 *
	 * Le premier enchaîne tout : spin déclencheur, transition, Free Spins,
	 * retrigger, sortie. Le second démontre qu'aucun état de Bonus ne survit.
	 */
	setContext();

	/** Les 8 premiers events : le spin Base qui déclenche, retrigger exclu. */
	const triggerSpin = bonus.bookBonus.state.slice(0, 8);
	/** Jusqu'au premier Free Spin inclus : héritage des multiplicateurs. */
	const untilFirstFreeSpin = bonus.bookBonus.state.slice(0, 14);
	/** Jusqu'au deuxième : la grille du FS1 est toujours là. */
	const untilSecondFreeSpin = bonus.bookBonus.state.slice(0, 17);
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

<!-- Base Game seul : la 4e connexion n'interrompt pas la cascade. -->
<Story
	name="spin declencheur"
	args={templateArgs({
		skipLoadingScreen: true,
		data: triggerSpin,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Free Spin 1 : la grille du spin déclencheur est conservée. -->
<Story
	name="FS1 grille heritee"
	args={templateArgs({
		skipLoadingScreen: true,
		data: untilFirstFreeSpin,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Free Spin 2 : aucun reset entre deux Free Spins, et le Wild n'a pas bougé. -->
<Story
	name="FS1 vers FS2 persistance"
	args={templateArgs({
		skipLoadingScreen: true,
		data: untilSecondFreeSpin,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Le book entier : Base, Bonus, retrigger, sortie. -->
<Story
	name="bonus complet"
	args={templateArgs({
		skipLoadingScreen: true,
		data: bonus.bookBonus.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Deux Free Spins sans aucune connexion : updateFreeSpin, reveal, setTotalWin. -->
<Story
	name="free spins sans gain"
	args={templateArgs({
		skipLoadingScreen: true,
		data: bonus.bookBonusNoWinSpins.state,
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>

<!-- Le spin Base qui suit : plus aucun état de Bonus. -->
<Story
	name="retour base game"
	args={templateArgs({
		skipLoadingScreen: true,
		data: [...bonus.bookBonus.state, ...bonus.bookAfterBonus.state],
		action: async (data) => await playBookEvents(data),
	})}
	{template}
/>
