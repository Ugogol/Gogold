import { type CascadingReelSymbolState } from 'utils-slots';
import type config from './config';

export type SymbolName = keyof typeof config.symbols;
/**
 * `charge` n'a de sens que pour le Wild. Elle voyage avec le symbole, comme
 * `multiplier` et `scatter` chez Stake : c'est le Book qui la fournit partout où
 * il place un Wild, et le frontend ne l'incrémente jamais.
 */
export type RawSymbol = {
	name: SymbolName;
	multiplier?: number;
	scatter?: boolean;
	charge?: number;
};
export type BetMode = keyof typeof config.betModes;
export type GameType = keyof typeof config.paddingReels;

export const SYMBOL_STATES = [
	'static',
	'spin',
	'land',
	'win',
	'postWinStatic',
	'explosion',
	/** Le symbole occupe sa case mais n'est pas dessiné : le Wild en vol
	 *  est rendu par `WildFlight`, pas par le plateau. */
	'hidden',
] as const;

export type SymbolState = CascadingReelSymbolState | (typeof SYMBOL_STATES)[number];

export type Position = {
	reel: number;
	row: number;
};
