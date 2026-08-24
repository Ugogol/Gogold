import type { BookEventHandlerMap } from 'utils-book';

import { stateGame, stateGameDerived } from './stateGame.svelte';
import type { BookEvent, BookEventOfType, BookEventContext } from './typesBookEvent';

/**
 * Un seul handler à ce stade. Il ne décide rien : il donne au plateau Stake
 * le contenu fourni par le book. Les handlers cluster/tumble arriveront avec
 * le contrat math (voir typesBookEvent.ts).
 */
export const bookEventHandlerMap: BookEventHandlerMap<BookEvent, BookEventContext> = {
	reveal: async (bookEvent: BookEventOfType<'reveal'>) => {
		stateGame.gameType = bookEvent.gameType;
		// Pas de reels de padding à ce stade : le plateau du book est affiché tel quel.
		await stateGameDerived.enhancedBoard.spin({ revealEvent: bookEvent });
	},
};
