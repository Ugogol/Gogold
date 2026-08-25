<script lang="ts" module>
	import type { Position } from '../game/types';

	/**
	 * Déplacement du Wild vers la case que le Book lui a désignée.
	 *
	 * Un seul emitterEvent : le mouvement, le changement de charge et la
	 * libération de l'ancienne case forment une seule étape indivisible.
	 */
	export type EmitterEventWildFlight = {
		type: 'boardWildMove';
		from: Position;
		to: Position;
		charge: number;
	};
</script>

<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { cubicInOut, backOut } from 'svelte/easing';
	import { Sprite } from 'pixi-svelte';

	import BoardContainer from './BoardContainer.svelte';
	import { getSymbolX, getSymbolY } from '../game/utils';
	import { getContext } from '../game/context';
	import {
		SYMBOL_DISPLAY_SIZE,
		WILD_CHARGE_ASSET_MAP,
		WILD_MOVE_DURATION,
	} from '../game/constants';

	/**
	 * Le Wild en vol, dessiné AU-DESSUS du plateau.
	 *
	 * Pourquoi un calque séparé : un symbole de plateau tire son x de son index de
	 * reel, pas de son état. Un déplacement d'une colonne à l'autre n'est donc pas
	 * exprimable en déplaçant un symbole de reel — il faut un sprite qui vole.
	 *
	 * Pendant le vol, la case de départ passe en `hidden` : il n'y a jamais deux
	 * Wild à l'écran. Le Wild lui-même n'est jamais détruit.
	 *
	 * Les positions viennent de `getSymbolX` / `getSymbolY`, les mêmes fonctions
	 * que les symboles : aucune coordonnée en pixels, donc le trajet suit
	 * automatiquement le layout, desktop comme mobile.
	 */
	const context = getContext();

	const x = new Tween(0);
	const y = new Tween(0);
	const sizeRatio = new Tween(1);

	let show = $state(false);
	let charge = $state(0);

	/** `Position.row` est un index de reel paddé : la ligne 0 est hors champ. */
	const rowToY = (row: number) => getSymbolY(row - 1);

	const assetKey = $derived(WILD_CHARGE_ASSET_MAP[charge] ?? WILD_CHARGE_ASSET_MAP[0]);
	const size = $derived(SYMBOL_DISPLAY_SIZE * sizeRatio.current);

	context.eventEmitter.subscribeOnMount({
		boardWildMove: async (event) => {
			const { from, to } = event;
			const source = context.stateGame.board[from.reel]?.reelState.symbols[from.row];
			const target = context.stateGame.board[to.reel]?.reelState.symbols[to.row];

			if (!source || !target) {
				console.error('boardWildMove : position hors plateau', { from, to });
				return;
			}

			// Le vol part avec la charge actuelle et n'affiche la nouvelle qu'à
			// l'arrivée : le joueur voit d'abord le déplacement, puis la montée.
			charge = source.rawSymbol.charge ?? 0;
			x.set(getSymbolX(from.reel), { duration: 0 });
			y.set(rowToY(from.row), { duration: 0 });
			sizeRatio.set(1, { duration: 0 });
			show = true;
			source.symbolState = 'hidden';

			await Promise.all([
				x.set(getSymbolX(to.reel), { duration: WILD_MOVE_DURATION, easing: cubicInOut }),
				y.set(rowToY(to.row), { duration: WILD_MOVE_DURATION, easing: cubicInOut }),
			]);

			// Montée de charge : la valeur vient du Book, jamais d'un incrément.
			charge = event.charge;
			await sizeRatio.set(1.18, { duration: 130, easing: backOut });
			await sizeRatio.set(1, { duration: 130, easing: cubicInOut });

			// Le Wild et le symbole de sa case d'arrivée ÉCHANGENT leurs places.
			//
			// Les deux cases appartiennent à la connexion : celle d'arrivée garde le
			// Wild, celle de départ récupère un symbole qui allait de toute façon
			// disparaître avec le reste du groupe. Aucun symbole n'est inventé,
			// aucune donnée du Book n'est contournée, et il n'y a jamais deux Wild
			// — le plateau reste cohérent pour le `tumbleBoard` qui suit.
			const vacated = target.rawSymbol;
			target.rawSymbol = { name: 'W', charge: event.charge };
			target.symbolState = 'static';
			source.rawSymbol = vacated;
			source.symbolState = 'static';
			show = false;
		},
	});
</script>

{#if show}
	<BoardContainer>
		<Sprite
			key={assetKey}
			x={x.current}
			y={y.current}
			anchor={{ x: 0.5, y: 0.5 }}
			width={size}
			height={size}
		/>
	</BoardContainer>
{/if}
