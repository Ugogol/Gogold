<script lang="ts" module>
	import type { RawSymbol, Position } from '../game/types';

	/**
	 * Un bookEvent complexe se décompose en emitterEvents simples et séquentiels.
	 * Ces sept-là sont ceux de `apps/cluster`, repris tels quels : mêmes noms,
	 * même découpage, même ordre. Aucun scheduler n'est écrit — l'attente se fait
	 * par `await` sur les promesses de `Tween` et sur `oncomplete`.
	 */
	export type EmitterEventTumbleBoard =
		| { type: 'tumbleBoardShow' }
		| { type: 'tumbleBoardHide' }
		| { type: 'tumbleBoardInit'; addingBoard: RawSymbol[][] }
		| { type: 'tumbleBoardReset' }
		| { type: 'tumbleBoardExplode'; explodingPositions: Position[] }
		| { type: 'tumbleBoardRemoveExploded' }
		| { type: 'tumbleBoardSlideDown' };
</script>

<script lang="ts">
	import _ from 'lodash';
	import { Tween } from 'svelte/motion';
	import { backOut } from 'svelte/easing';

	import { BoardContext } from 'components-shared';
	import { waitForResolve } from 'utils-shared/wait';

	import TumbleBoardBase from './TumbleBoardBase.svelte';
	import BoardContainer from './BoardContainer.svelte';
	import BoardMask from './BoardMask.svelte';
	import { getSymbolY } from '../game/utils';
	import { getContext } from '../game/context';
	import type { TumbleSymbol } from '../game/stateGame.svelte';

	/**
	 * Plateau de cascade, adapté de `apps/cluster`.
	 *
	 * Il ne décide rien : les positions qui explosent et les symboles qui
	 * arrivent viennent tous les deux du bookEvent. Aucune recherche de voisins,
	 * aucun flood fill, aucune détection de cluster.
	 *
	 * Les dimensions ne sont écrites nulle part ici : les tableaux sont dérivés de
	 * `boardRaw()`, donc de la configuration du jeu. Aucun 5 ni 7 en dur.
	 */
	const context = getContext();

	let show = $state(false);

	const createTumbleSymbol = ({
		initY,
		rawSymbol,
	}: {
		initY: number;
		rawSymbol: RawSymbol;
	}): TumbleSymbol => {
		const symbolY = new Tween(initY);

		// `$state(...)` doit initialiser une déclaration : pas de `return $state(…)`.
		const tumbleSymbol: TumbleSymbol = $state({
			symbolY,
			rawSymbol,
			symbolState: 'static',
			oncomplete: () => {},
		});

		return tumbleSymbol;
	};

	/** Les arrivants sont empilés AU-DESSUS du champ, dans l'ordre du book. */
	const initTumbleBoardAdding = ({ addingBoard }: { addingBoard: RawSymbol[][] }) =>
		context.stateGameDerived.boardRaw().map((_reel, reelIndex) => {
			const addingReel = addingBoard[reelIndex] ?? [];

			return addingReel.map((rawSymbol, symbolIndex) =>
				createTumbleSymbol({
					initY: getSymbolY(symbolIndex - 1 - addingReel.length),
					rawSymbol,
				}),
			);
		});

	/**
	 * Les symboles déjà en place, recopiés depuis le plateau normal.
	 *
	 * L'ÉTAT est repris aussi, pas seulement le `rawSymbol` : une case que le Wild
	 * vient de quitter est en `hidden`. Sans ça, elle réapparaîtrait le temps du
	 * tumble et on verrait le Wild exploser alors qu'il est déjà parti.
	 */
	/**
	 * Les symboles déjà en place, recopiés depuis le plateau normal.
	 *
	 * Seul le `rawSymbol` est repris, jamais l'état — comme chez Stake. Reprendre
	 * l'état paraissait utile pour le Wild, mais provoque un interblocage : les
	 * symboles déjà en `postWinStatic` n'émettent alors plus le `oncomplete`
	 * qu'attend `tumbleBoardExplode`, et la cascade se fige. Vérifié.
	 */
	const initTumbleBoardBase = () =>
		context.stateGameDerived
			.boardRaw()
			.map((rawSymbolReel) =>
				rawSymbolReel.map((rawSymbol, symbolIndex) =>
					createTumbleSymbol({ initY: getSymbolY(symbolIndex - 1), rawSymbol }),
				),
			);

	context.eventEmitter.subscribeOnMount({
		tumbleBoardShow: () => (show = true),
		tumbleBoardHide: () => (show = false),
		tumbleBoardInit: ({ addingBoard }) => {
			context.stateGame.tumbleBoardAdding = initTumbleBoardAdding({ addingBoard });
			context.stateGame.tumbleBoardBase = initTumbleBoardBase();
		},
		tumbleBoardReset: () => {
			context.stateGame.tumbleBoardAdding = [];
			context.stateGame.tumbleBoardBase = [];
		},
		tumbleBoardExplode: async ({ explodingPositions }) => {
			const getPromises = () =>
				explodingPositions.map(async (position) => {
					const tumbleSymbol = context.stateGame.tumbleBoardBase[position.reel]?.[position.row];
					if (!tumbleSymbol) return;
					tumbleSymbol.symbolState = 'explosion';
					await waitForResolve((resolve) => (tumbleSymbol.oncomplete = resolve));
				});

			await Promise.all(getPromises());
		},
		tumbleBoardRemoveExploded: () => {
			context.stateGame.tumbleBoardBase.forEach((tumbleReel, reelIndex) => {
				context.stateGame.tumbleBoardBase[reelIndex] = tumbleReel.filter(
					(tumbleSymbol) => tumbleSymbol.symbolState !== 'explosion',
				);
			});
		},
		tumbleBoardSlideDown: async () => {
			const getPromises = () =>
				_.flatten(
					context.stateGameDerived.tumbleBoardCombined().map((tumbleReel) =>
						tumbleReel.map(async (tumbleSymbol, symbolIndex) => {
							const targetY = getSymbolY(symbolIndex - 1); // même repère que initTumbleBoardBase
							if (targetY === tumbleSymbol.symbolY.current) return;

							await tumbleSymbol.symbolY.set(targetY, { duration: 200, easing: backOut });

							// Les lignes de padding ne jouent pas d'atterrissage.
							if (symbolIndex > 0 && symbolIndex < tumbleReel.length - 1) {
								tumbleSymbol.symbolState = 'land';
								await waitForResolve((resolve) => {
									tumbleSymbol.oncomplete = () => {
										tumbleSymbol.symbolState = 'static';
										resolve();
									};
								});
							}
						}),
					),
				);

			await Promise.all(getPromises());
		},
	});
</script>

{#if show}
	<BoardContext animate={false}>
		<BoardContainer>
			<BoardMask />
			<TumbleBoardBase />
		</BoardContainer>
	</BoardContext>

	<BoardContext animate={true}>
		<BoardContainer>
			<TumbleBoardBase />
		</BoardContainer>
	</BoardContext>
{/if}
