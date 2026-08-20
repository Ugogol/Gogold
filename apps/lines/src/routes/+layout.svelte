<script lang="ts">
	import { type Snippet, type Component } from 'svelte';
	import { page } from '$app/state';
	import { GlobalStyle } from 'components-ui-html';
	import { Authenticate, LoaderStakeEngine, LoaderExample, LoadI18n } from 'components-shared';
	import Game from '../components/Game.svelte';
	import { setContext } from '../game/context';
	import { DEBUG_QUERY_KEY } from '../game/devDebugMode';

	import messagesMap from '../i18n/messagesMap';

	type Props = { children: Snippet };

	const props: Props = $props();

	let showYourLoader = $state(false);

	// ── GOGOLD — mode debug local, DÉVELOPPEMENT UNIQUEMENT ────────────────────
	// Activé par `?debug=true` sur un serveur de dev (voir docs/DEBUG_PANEL.md).
	//
	// Ce mode saute uniquement <Authenticate> : sans session Stake, l'appel à
	// /wallet/authenticate échoue et affiche une modale « Failed to fetch » qui
	// masque le jeu. Tout le reste (états, machine, pipeline de books) est
	// inchangé et repose sur les valeurs par défaut de `state-shared`, exactement
	// comme le fait StoryGameTemplate dans Storybook.
	//
	// Aucun wallet, aucun solde et aucun RGS n'est simulé.
	//
	// IS_DEV est une constante de module : Vite la replie à `false` en production,
	// la branche devient inatteignable et Rollup élimine le panel et ses fixtures.
	const IS_DEV = import.meta.env.DEV;

	const debugMode = $derived(IS_DEV && page.url.searchParams.get(DEBUG_QUERY_KEY) === 'true');

	let DebugPanel = $state<Component | null>(null);

	$effect(() => {
		if (IS_DEV && debugMode && !DebugPanel) {
			import('../dev/DebugPanel.svelte').then((module) => (DebugPanel = module.default));
		}
	});

	const loaderUrlStakeEngine = new URL('../../stake-engine-loader.gif', import.meta.url).href;
	const loaderUrl = new URL('../../loader.gif', import.meta.url).href;

	setContext();
</script>

{#snippet gameTree()}
	<LoadI18n {messagesMap}>
		<Game />
	</LoadI18n>
{/snippet}

<GlobalStyle>
	{#if debugMode}
		{@render gameTree()}
	{:else}
		<Authenticate>
			{@render gameTree()}
		</Authenticate>
	{/if}
</GlobalStyle>

<LoaderStakeEngine src={loaderUrlStakeEngine} oncomplete={() => (showYourLoader = true)} />

{#if showYourLoader}
	<LoaderExample src={loaderUrl} />
	<!-- '/loader.gif' is served from static folder of sveltekit -->
	<!-- File location: apps/scatter/static/loader.gif -->
{/if}

{@render props.children()}

{#if DebugPanel}
	<DebugPanel />
{/if}
