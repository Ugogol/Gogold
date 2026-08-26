<script lang="ts" module>
	import type { RawSymbol, Position } from '../game/types';

	export type EmitterEventBoard =
		| { type: 'boardSettle'; board: RawSymbol[][] }
		| { type: 'boardShow' }
		| { type: 'boardHide' }
		| {
				type: 'boardWithAnimateSymbols';
				symbolPositions: Position[];
		  }
		/**
		 * Pose les Wild TEMPORAIRES de Wild Split aux cases fournies par le Book.
		 * Le frontend ne choisit aucune position : il transcrit.
		 */
		| { type: 'boardWildSplit'; positions: Position[] };
</script>

<script lang="ts">
	import { waitForResolve } from 'utils-shared/wait';
	import { BoardContext } from 'components-shared';

	import { getContext } from '../game/context';
	import { zIndexes } from '../game/constants';
	import BoardContainer from './BoardContainer.svelte';
	import BoardMask from './BoardMask.svelte';
	import BoardBase from './BoardBase.svelte';

	const context = getContext();

	let show = $state(true);

	context.eventEmitter.subscribeOnMount({
		stopButtonClick: () => context.stateGameDerived.enhancedBoard.stop(),
		boardSettle: ({ board }) => context.stateGameDerived.enhancedBoard.settle(board),
		boardShow: () => (show = true),
		boardHide: () => (show = false),
		boardWildSplit: async ({ positions }) => {
			const getPromises = () =>
				positions.map(async (position) => {
					const reelSymbol = context.stateGame.board[position.reel]?.reelState.symbols[position.row];
					if (!reelSymbol) {
						console.error('boardWildSplit : position hors plateau', position);
						return;
					}
					// `temporary` est ce qui les distingue du Wild permanent : pas de
					// charge, usage unique, et `wildMove` ne les suit jamais.
					reelSymbol.rawSymbol = { name: 'W', temporary: true };
					reelSymbol.symbolState = 'win';
					await waitForResolve((resolve) => (reelSymbol.oncomplete = resolve));
					reelSymbol.symbolState = 'static';
				});

			await Promise.all(getPromises());
		},
		boardWithAnimateSymbols: async ({ symbolPositions }) => {
			const getPromises = () =>
				symbolPositions.map(async (position) => {
					const reelSymbol = context.stateGame.board[position.reel].reelState.symbols[position.row];
					reelSymbol.symbolState = 'win';
					await waitForResolve((resolve) => (reelSymbol.oncomplete = resolve));
					reelSymbol.symbolState = 'postWinStatic';
				});

			await Promise.all(getPromises());
		},
	});

	context.stateGameDerived.enhancedBoard.readyToSpinEffect();
</script>

{#if show}
	<BoardContext animate={false}>
		<BoardContainer zIndex={zIndexes.board}>
			<BoardMask />
			<BoardBase />
		</BoardContainer>
	</BoardContext>

	<BoardContext animate={true}>
		<BoardContainer zIndex={zIndexes.board}>
			<BoardBase />
		</BoardContainer>
	</BoardContext>
{/if}
