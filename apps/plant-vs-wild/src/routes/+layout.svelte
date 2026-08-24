<script lang="ts">
	import { type Snippet } from 'svelte';
	import { GlobalStyle } from 'components-ui-html';
	import { LoadI18n } from 'components-shared';

	import Game from '../components/Game.svelte';
	import { setContext } from '../game/context';

	import messagesMap from '../i18n/messagesMap';

	/**
	 * <Authenticate> n'est PAS monté à ce stade : sans session RGS il échoue et
	 * recouvre le jeu d'une modale d'erreur. Il sera remonté quand le flux de
	 * pari et le RGS seront branchés. Aucun contournement n'est ajouté ici.
	 */
	type Props = { children: Snippet };

	const props: Props = $props();

	setContext();
</script>

<GlobalStyle>
	<LoadI18n {messagesMap}>
		<Game />
	</LoadI18n>
</GlobalStyle>

{@render props.children()}
