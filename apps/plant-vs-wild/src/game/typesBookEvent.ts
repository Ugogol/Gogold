import type { RawSymbol, GameType } from './types';

/**
 * Contrat bookEvent — VOLONTAIREMENT MINIMAL à ce stade.
 *
 * Le contrat définitif appartient au Math : il sera écrit quand
 * `math/games/<game_id>/` existera. Les events cluster/tumble du sample Stake
 * (`tumbleBoard`, `updateTumbleWin`, `updateGrid`, `updateGlobalMult`,
 * `freeSpinRetrigger`…) ne sont pas déclarés ici pour ne pas figer un contrat
 * que le math n'a pas encore produit.
 *
 * Seul `reveal` est présent : il ne calcule rien, il affiche un plateau donné.
 */
export type BookEventOfType<T extends BookEvent['type']> = Extract<BookEvent, { type: T }>;

export type BookEvent = {
	index: number;
	type: 'reveal';
	board: RawSymbol[][];
	paddingPositions: number[];
	gameType: GameType;
	anticipation: number[];
};

export type BookEventContext = {
	bookEvents: BookEvent[];
};

export type Bet = {
	id: number;
	payoutMultiplier: number;
	state: BookEvent[];
};
