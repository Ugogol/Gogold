import { createPlayBookUtils } from 'utils-book';
import { createGetEmptyPaddedBoard } from 'utils-slots';

import { SYMBOL_SIZE, REEL_PADDING, BOARD_DIMENSIONS, SYMBOL_PLACEHOLDER_MAP } from './constants';
import { bookEventHandlerMap } from './bookEventHandlerMap';
import type { RawSymbol } from './types';

export const { getEmptyBoard } = createGetEmptyPaddedBoard({ reelsDimensions: BOARD_DIMENSIONS });
export const { playBookEvent, playBookEvents } = createPlayBookUtils({ bookEventHandlerMap });

export const getSymbolX = (reelIndex: number) => SYMBOL_SIZE * (reelIndex + REEL_PADDING);
export const getSymbolY = (symbolIndexOfBoard: number) => (symbolIndexOfBoard + 0.5) * SYMBOL_SIZE;

export const getSymbolPlaceholder = ({ rawSymbol }: { rawSymbol: RawSymbol }) =>
	SYMBOL_PLACEHOLDER_MAP[rawSymbol.name];
