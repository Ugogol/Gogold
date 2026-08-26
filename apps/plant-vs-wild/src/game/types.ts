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
	/**
	 * Marque un Wild TEMPORAIRE, posé par Wild Split.
	 *
	 * Le Wild standard est unique et persistant ; les temporaires sont à usage
	 * unique et n'ont pas de charge. Sans ce champ, quatre Wild à l'écran seraient
	 * indistinguables et le frontend ne saurait plus lequel `wildMove` suit.
	 *
	 * Extension du contrat de l'étape 4, qui affirmait que « leur caractère
	 * éphémère ne demande aucun champ » — c'était faux dès qu'ils coexistent avec
	 * le Wild principal.
	 */
	temporary?: boolean;
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
