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

/**
 * Rectangle réellement occupé à l'écran par le sprite de fond.
 *
 * `createBackgroundLayout` ne renvoie QU'UNE dimension — `width` ou `height`,
 * selon l'axe qu'il a choisi d'étirer — et laisse Pixi déduire l'autre du
 * ratio de la texture. Pour poser quelque chose sur le décor il faut les deux :
 * on complète donc la manquante avec le même ratio.
 *
 * `x` et `y` sont le CENTRE du sprite : il est ancré en (0.5, 0.5).
 */
export const backgroundRect = (
	layout: { x: number; y: number; width?: number; height?: number },
	ratio: number,
) => {
	const width = layout.width ?? (layout.height ?? 0) * ratio;
	const height = layout.height ?? (layout.width ?? 0) / ratio;
	return { x: layout.x, y: layout.y, width, height };
};
