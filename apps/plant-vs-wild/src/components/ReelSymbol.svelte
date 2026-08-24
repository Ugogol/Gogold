<script lang="ts">
	import Symbol from './Symbol.svelte';
	import SymbolWrap from './SymbolWrap.svelte';
	import { getSymbolX } from '../game/utils';
	import type { ReelSymbol } from '../game/stateGame.svelte';

	type Props = {
		reelIndex: number;
		reelSymbol: ReelSymbol;
	};

	const props: Props = $props();
</script>

<SymbolWrap
	x={getSymbolX(props.reelIndex)}
	y={props.reelSymbol.symbolY.current}
	animating={props.reelSymbol.symbolState === 'land' || props.reelSymbol.symbolState === 'win'}
>
	<Symbol state={props.reelSymbol.symbolState} rawSymbol={props.reelSymbol.rawSymbol} />
</SymbolWrap>
