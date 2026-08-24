<script lang="ts">
	import { Sprite } from 'pixi-svelte';

	import type { SymbolState, RawSymbol } from '../game/types';
	import { SYMBOL_ASSET_MAP, SYMBOL_DISPLAY_SIZE } from '../game/constants';

	/**
	 * Rend un symbole depuis l'atlas `sprites/symbols`.
	 *
	 * Aucun état visuel n'est encore différencié : `state` est accepté pour que
	 * la signature reste stable, mais tous les états affichent la frame statique.
	 * Les animations viendront avec les assets correspondants.
	 */
	type Props = {
		x?: number;
		y?: number;
		state: SymbolState;
		rawSymbol: RawSymbol;
	};

	const props: Props = $props();
	const assetKey = $derived(SYMBOL_ASSET_MAP[props.rawSymbol.name]);
	const size = SYMBOL_DISPLAY_SIZE;
</script>

<Sprite
	key={assetKey}
	x={props.x ?? 0}
	y={props.y ?? 0}
	anchor={{ x: 0.5, y: 0.5 }}
	width={size}
	height={size}
/>
