<script lang="ts" module>
	import type { Position, SymbolName } from '../game/types';

	/**
	 * Déplacement du Wild vers la case que le Book lui a désignée.
	 *
	 * Un seul emitterEvent : le mouvement, le changement de charge et la
	 * libération de l'ancienne case forment une seule étape indivisible.
	 */
	export type EmitterEventWildFlight =
		| {
				type: 'boardWildMove';
				from: Position;
				to: Position;
				charge: number;
		  }
		/**
		 * Wild Snake : le Wild rampe de `from` vers `to` en suivant `path`, dans
		 * l'ordre exact fourni par le Book. Chaque case traversée prend `symbol`.
		 * Aucun trajet n'est calculé ici — ni direction, ni longueur, ni symbole.
		 */
		| {
				type: 'boardWildSnake';
				from: Position;
				path: Position[];
				to: Position;
				symbol: SymbolName;
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
		WILD_SNAKE_STEP_DURATION,
		zIndexes,
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

	/** Le symbole du plateau à une position, ou `undefined` si hors limites. */
	const symbolAt = (position: Position) =>
		context.stateGame.board[position.reel]?.reelState.symbols[position.row];

	/**
	 * Contrôle de COHÉRENCE DE FIXTURE, développement uniquement.
	 *
	 * Trajet non vide, cases dans les limites, pas orthogonal, aucune case
	 * revisitée. Rien n'est corrigé ni calculé : on signale un Book incohérent.
	 * `import.meta.env.DEV` est replié à `false` en production, la fonction y
	 * disparaît.
	 */
	const assertSnakePath = (from: Position, path: Position[], to: Position) => {
		if (!import.meta.env.DEV) return;

		const steps = [from, ...path, to];
		if (path.length === 0) console.error('boardWildSnake : trajet vide', { from, to });

		const seen = new Set<string>();
		steps.forEach((step, index) => {
			const key = `${step.reel}:${step.row}`;
			if (seen.has(key)) console.error('boardWildSnake : case revisitée', step);
			seen.add(key);

			if (!symbolAt(step)) console.error('boardWildSnake : case hors plateau', step);

			if (index === 0) return;
			const previous = steps[index - 1];
			const distance =
				Math.abs(step.reel - previous.reel) + Math.abs(step.row - previous.row);
			if (distance !== 1) {
				console.error('boardWildSnake : pas non orthogonal', { previous, step });
			}
		});
	};

	context.eventEmitter.subscribeOnMount({
		boardWildSnake: async (event) => {
			const { from, path, to, symbol } = event;
			assertSnakePath(from, path, to);

			const source = symbolAt(from);
			if (!source) return;

			charge = source.rawSymbol.charge ?? 0;
			x.set(getSymbolX(from.reel), { duration: 0 });
			y.set(rowToY(from.row), { duration: 0 });
			sizeRatio.set(1, { duration: 0 });
			show = true;
			source.symbolState = 'hidden';

			// Un pas à la fois, dans l'ordre du Book. Chaque case traversée est
			// convertie au symbole fourni dès que le Wild y arrive.
			for (const step of path) {
				await Promise.all([
					x.set(getSymbolX(step.reel), {
						duration: WILD_SNAKE_STEP_DURATION,
						easing: cubicInOut,
					}),
					y.set(rowToY(step.row), { duration: WILD_SNAKE_STEP_DURATION, easing: cubicInOut }),
				]);

				const crossed = symbolAt(step);
				if (crossed) {
					crossed.rawSymbol = { name: symbol };
					crossed.symbolState = 'static';
				}
			}

			await Promise.all([
				x.set(getSymbolX(to.reel), { duration: WILD_SNAKE_STEP_DURATION, easing: cubicInOut }),
				y.set(rowToY(to.row), { duration: WILD_SNAKE_STEP_DURATION, easing: cubicInOut }),
			]);

			// Le plateau final vient du Book : le handler applique `boardSettle`
			// juste après. Rien n'est déduit ici de la case d'arrivée.
			show = false;
		},
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
	<BoardContainer zIndex={zIndexes.wildFlight}>
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
