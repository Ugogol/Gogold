<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { cubicOut } from 'svelte/easing';
	import { Sprite } from 'pixi-svelte';

	import type { SymbolState, RawSymbol } from '../game/types';
	import {
		SYMBOL_ASSET_MAP,
		SYMBOL_DISPLAY_SIZE,
		WILD_CHARGE_ASSET_MAP,
		WILD_TEMPORARY,
	} from '../game/constants';

	/**
	 * Rend un symbole depuis l'atlas `sprites/symbols`.
	 *
	 * Pour le Wild, la texture dépend de la charge que le Book a placée sur le
	 * symbole. Le frontend ne calcule ni n'incrémente rien : il lit une table.
	 *
	 * `oncomplete` est le contrat Stake : le plateau change l'état d'un symbole
	 * puis ATTEND ce rappel avant de passer à l'étape suivante. Il doit donc être
	 * appelé pour TOUS les états, y compris ceux qui n'animent rien — sinon la
	 * promesse côté plateau ne se résout jamais et la cascade se fige.
	 * `SymbolSprite` de `apps/cluster` fait la même chose, en résolvant
	 * immédiatement faute d'animation Spine.
	 *
	 * Les transitions ci-dessous sont volontairement minimales : elles servent à
	 * rendre l'ordre des étapes lisible, pas à être le rendu final.
	 */
	type Props = {
		x?: number;
		y?: number;
		state: SymbolState;
		rawSymbol: RawSymbol;
		oncomplete?: () => void;
	};

	const props: Props = $props();

	/**
	 * Un Wild TEMPORAIRE n'a pas de charge : il garde la texture de l'état 0, et
	 * se distingue du Wild permanent par une opacité et une taille réduites.
	 */
	const isTemporaryWild = $derived(props.rawSymbol.name === 'W' && props.rawSymbol.temporary === true);

	const assetKey = $derived(
		props.rawSymbol.name === 'W'
			? (WILD_CHARGE_ASSET_MAP[isTemporaryWild ? 0 : (props.rawSymbol.charge ?? 0)] ??
				WILD_CHARGE_ASSET_MAP[0])
			: SYMBOL_ASSET_MAP[props.rawSymbol.name],
	);

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
		} else if (state === 'hidden') {
			// Le Wild en vol est dessiné par `WildFlight` : la case le réserve
			// sans l'afficher, pour qu'il n'y ait jamais deux Wild à l'écran.
			sizeRatio.set(1, { duration: 0 });
			alpha.set(0, { duration: 0 });
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

	const size = $derived(
		SYMBOL_DISPLAY_SIZE * sizeRatio.current * (isTemporaryWild ? WILD_TEMPORARY.sizeRatio : 1),
	);
</script>

<Sprite
	key={assetKey}
	x={props.x ?? 0}
	y={props.y ?? 0}
	anchor={{ x: 0.5, y: 0.5 }}
	width={size}
	height={size}
	alpha={alpha.current * (isTemporaryWild ? WILD_TEMPORARY.alpha : 1)}
/>
