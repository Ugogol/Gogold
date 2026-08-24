<script lang="ts">
	import { Container, Rectangle, Text } from 'pixi-svelte';

	import type { SymbolState, RawSymbol } from '../game/types';
	import { SYMBOL_SIZE, SYMBOL_STATE_STYLE } from '../game/constants';
	import { getSymbolPlaceholder } from '../game/utils';

	/**
	 * Rendu PROVISOIRE d'un symbole.
	 *
	 * Aucun asset n'est intégré : le symbole est dessiné avec les primitives
	 * PixiJS pour rendre la grille lisible. Ce composant sera remplacé par le
	 * rendu sprite/Spine du sample Stake quand les assets du jeu existeront.
	 */
	type Props = {
		x?: number;
		y?: number;
		state: SymbolState;
		rawSymbol: RawSymbol;
	};

	const props: Props = $props();
	const placeholder = $derived(getSymbolPlaceholder({ rawSymbol: props.rawSymbol }));
	const stateStyle = $derived(SYMBOL_STATE_STYLE[props.state] ?? SYMBOL_STATE_STYLE.static);
	const size = $derived(SYMBOL_SIZE * 0.88);
</script>

<Container x={props.x ?? 0} y={props.y ?? 0}>
	<Rectangle
		anchor={{ x: 0.5, y: 0.5 }}
		width={size}
		height={size}
		borderRadius={12}
		backgroundColor={placeholder.fill}
		backgroundAlpha={stateStyle.alpha}
		borderColor={stateStyle.borderColor}
		borderWidth={3}
	/>
	<Text
		anchor={{ x: 0.5, y: 0.5 }}
		text={placeholder.label}
		style={{
			fontFamily: 'system-ui, sans-serif',
			fontSize: SYMBOL_SIZE * 0.3,
			fontWeight: '700',
			fill: 0xf5f5f0,
		}}
	/>
</Container>
