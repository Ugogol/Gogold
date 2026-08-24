<script lang="ts">
	import { type Snippet, type Component } from 'svelte';
	import { GlobalStyle } from 'components-ui-html';
	import { LoadI18n } from 'components-shared';

	import Game from '../components/Game.svelte';
	import { setContext } from '../game/context';
	import { isLocalVisualMode } from '../game/devVisualMode';

	import messagesMap from '../i18n/messagesMap';

	/**
	 * <Authenticate> n'est PAS monté à ce stade : sans session RGS il échoue et
	 * recouvre le jeu d'une modale d'erreur. Il sera remonté quand le flux de
	 * pari et le RGS seront branchés. Aucun contournement n'est ajouté ici.
	 */
	type Props = { children: Snippet };

	const props: Props = $props();

	// ── GOGOLD — panneau de revue visuelle, DÉVELOPPEMENT UNIQUEMENT ───────────
	// Activé par `?visual=true`. Vite replie IS_DEV à `false` en production : la
	// branche devient inatteignable et Rollup élimine le panneau.
	const IS_DEV = import.meta.env.DEV;
	const visualMode = IS_DEV && isLocalVisualMode();

	let VisualPanel = $state<Component | null>(null);

	$effect(() => {
		if (IS_DEV && visualMode && !VisualPanel) {
			import('../dev/VisualPanel.svelte').then((module) => (VisualPanel = module.default));
		}
	});

	setContext();
</script>

<GlobalStyle>
	<LoadI18n {messagesMap}>
		<Game />
	</LoadI18n>
</GlobalStyle>

{@render props.children()}

{#if VisualPanel}
	<VisualPanel />
{/if}
