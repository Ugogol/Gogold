<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { cubicOut } from 'svelte/easing';
	import { Sprite } from 'pixi-svelte';

	import type { SymbolState, RawSymbol } from '../game/types';
	import { SYMBOL_ASSET_MAP, SYMBOL_DISPLAY_SIZE } from '../game/constants';

	/**
	 * Rend un symbole depuis l'atlas `sprites/symbols`.
	 *
	 * `oncomplete` est le contrat Stake : le plateau change l'état d'un symbole
	 * puis ATTEND ce rappel avant de passer à l'étape suivante. Il doit donc être
	 * appelé pour TOUS les états, y compris ceux qui n'animent rien — sinon la
	 * promesse côté plateau ne se résout jamais et la cascade se fige.
	 * `SymbolSprite` de `apps/cluster` fait la même chose, en résolvant
	 * immédiatement faute d'animation Spine.
	 *
	 * Les transitions ci-dessous sont volontairement minimales : elles servent à
	 * rendre l'ordre des étapes lisible, pas à être le rendu final. Aucune
	 * animation d'explosion n'a encore été livrée.
	 */
	type Props = {
		x?: number;
		y?: number;
		state: SymbolState;
		rawSymbol: RawSymbol;
		oncomplete?: () => void;
	};

	const props: Props = $props();
	const assetKey = $derived(SYMBOL_ASSET_MAP[props.rawSymbol.name]);

	const sizeRatio = new Tween(1);
	const alpha = new Tween(1);

	/** Le dernier état déjà joué : évite de rejouer la transition à chaque rendu. */
	let played: SymbolState | undefined;

	const play = async (state: SymbolState) => {
		if (state === 'win') {
			await sizeRatio.set(1.12, { duration: 160, easing: cubicOut });
			await sizeRatio.set(1, { duration: 160, easing: cubicOut });
		} else if (state === 'explosion') {
			await Promise.all([
				sizeRatio.set(0.15, { duration: 220, easing: cubicOut }),
				alpha.set(0, { duration: 220, easing: cubicOut }),
			]);
		} else {
			// Remise à l'état neutre, sans transition : un symbole réutilisé après
			// une explosion doit redevenir visible immédiatement.
			sizeRatio.set(1, { duration: 0 });
			alpha.set(1, { duration: 0 });
		}

		props.oncomplete?.();
	};

	$effect(() => {
		const state = props.state;
		if (state === played) return;
		played = state;
		void play(state);
	});

	const size = $derived(SYMBOL_DISPLAY_SIZE * sizeRatio.current);
</script>

<Sprite
	key={assetKey}
	x={props.x ?? 0}
	y={props.y ?? 0}
	anchor={{ x: 0.5, y: 0.5 }}
	width={size}
	height={size}
	alpha={alpha.current}
/>
