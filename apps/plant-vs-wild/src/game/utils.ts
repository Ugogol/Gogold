import { createPlayBookUtils } from 'utils-book';
import { createGetEmptyPaddedBoard } from 'utils-slots';

import { SYMBOL_SIZE, REEL_PADDING, BOARD_DIMENSIONS } from './constants';
import { bookEventHandlerMap } from './bookEventHandlerMap';

export const { getEmptyBoard } = createGetEmptyPaddedBoard({ reelsDimensions: BOARD_DIMENSIONS });
export const { playBookEvent, playBookEvents } = createPlayBookUtils({ bookEventHandlerMap });

export const getSymbolX = (reelIndex: number) => SYMBOL_SIZE * (reelIndex + REEL_PADDING);
export const getSymbolY = (symbolIndexOfBoard: number) => (symbolIndexOfBoard + 0.5) * SYMBOL_SIZE;

/**
 * FRONTIÈRE UNIQUE entre les deux indexations de lignes du jeu.
 *
 *   Position du board / tumble   reel paddé, 7 entrées
 *                                0 = padding haut, 1 à 5 visibles, 6 = padding bas
 *
 *   Ligne de gridMultipliers     lignes visibles uniquement, 0 à 4
 *
 * Les deux conventions viennent de Stake et ne sont pas alignées. Toute
 * conversion passe par ici — nulle part ailleurs on n'écrit `row - 1` ou
 * `row + 1` pour cette raison.
 *
 * `getSymbolY` prend déjà un index de LIGNE VISIBLE (`symbolIndexOfBoard`), donc
 * une ligne de grille s'y branche directement, sans conversion.
 */
export const boardRowToGridRow = (boardRow: number) => boardRow - 1;
export const gridRowToBoardRow = (gridRow: number) => gridRow + 1;
