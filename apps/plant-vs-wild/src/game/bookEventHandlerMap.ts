import _ from 'lodash';

import { stateBet } from 'state-shared';
import type { BookEventHandlerMap } from 'utils-book';

import { eventEmitter } from './eventEmitter';
import { stateGame, stateGameDerived } from './stateGame.svelte';
import type { BookEvent, BookEventOfType, BookEventContext } from './typesBookEvent';

/**
 * Traduction bookEvent → emitterEvents.
 *
 * Aucun handler ne décide quoi que ce soit : les positions gagnantes, les
 * positions qui explosent et les symboles qui arrivent viennent tous du book.
 * Le frontend ne cherche aucun cluster.
 *
 * Les events du contrat encore sans handler (`updateGrid`, `wildMove`,
 * `wildFeature`, `freeSpin*`…) arriveront avec leurs mécaniques. Le map Stake
 * n'est pas exhaustif : un event sans handler ne casse rien.
 */
export const bookEventHandlerMap: BookEventHandlerMap<BookEvent, BookEventContext> = {
	reveal: async (bookEvent: BookEventOfType<'reveal'>) => {
		stateGame.gameType = bookEvent.gameType;
		// Pas de reels de padding à ce stade : le plateau du book est affiché tel quel.
		await stateGameDerived.enhancedBoard.spin({ revealEvent: bookEvent });
	},

	/** Met en évidence les cases désignées par le Math. Il ne les cherche pas. */
	winInfo: async (bookEvent: BookEventOfType<'winInfo'>) => {
		eventEmitter.broadcast({ type: 'boardShow' });
		await eventEmitter.broadcastAsync({
			type: 'boardWithAnimateSymbols',
			symbolPositions: _.flatten(bookEvent.wins.map((win) => win.positions)),
		});
	},

	/**
	 * Décomposition en étapes séquentielles, reprise de `apps/cluster` :
	 * le plateau normal se cache, le plateau de tumble prend le relais, explose,
	 * retire, fait chuter, puis reverse le résultat au plateau normal.
	 */
	tumbleBoard: async (bookEvent: BookEventOfType<'tumbleBoard'>) => {
		eventEmitter.broadcast({ type: 'boardHide' });
		eventEmitter.broadcast({ type: 'tumbleBoardShow' });
		eventEmitter.broadcast({ type: 'tumbleBoardInit', addingBoard: bookEvent.newSymbols });
		await eventEmitter.broadcastAsync({
			type: 'tumbleBoardExplode',
			explodingPositions: bookEvent.explodingSymbols,
		});
		eventEmitter.broadcast({ type: 'tumbleBoardRemoveExploded' });
		await eventEmitter.broadcastAsync({ type: 'tumbleBoardSlideDown' });
		eventEmitter.broadcast({
			type: 'boardSettle',
			board: stateGameDerived
				.tumbleBoardCombined()
				.map((tumbleReel) => tumbleReel.map((tumbleSymbol) => tumbleSymbol.rawSymbol)),
		});
		eventEmitter.broadcast({ type: 'tumbleBoardReset' });
		eventEmitter.broadcast({ type: 'tumbleBoardHide' });
		eventEmitter.broadcast({ type: 'boardShow' });
	},

	/** Fin de résolution du spin. Le montant est une donnée du book, pas un calcul. */
	setTotalWin: async (bookEvent: BookEventOfType<'setTotalWin'>) => {
		stateBet.winBookEventAmount = bookEvent.amount;
	},
};
