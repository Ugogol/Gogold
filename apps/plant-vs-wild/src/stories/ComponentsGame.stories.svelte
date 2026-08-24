<script lang="ts" module>
	import { defineMeta } from '@storybook/addon-svelte-csf';

	const { Story } = defineMeta({
		title: 'COMPONENTS/<Game>',
	});
</script>

<script lang="ts">
	import { StoryLocale } from 'components-storybook';

	import Game from '../components/Game.svelte';
	import { setContext } from '../game/context';

	setContext();
</script>



<Story name="board 5x5">
	<StoryLocale lang="en">
		<Game />
	</StoryLocale>
</Story>
