import _ from 'lodash';
import type { Tween } from 'svelte/motion';

import { createEnhanceBoard, createReelForCascading } from 'utils-slots';

import type { GameType, RawSymbol, SymbolState } from './types';
import { stateLayoutDerived } from './stateLayout';
import {
	SYMBOL_SIZE,
	BOARD_SIZES,
	LAYOUT_BANDS,
	INITIAL_BOARD,
	BOARD_DIMENSIONS,
	SPIN_OPTIONS_DEFAULT,
	SPIN_OPTIONS_FAST,
	INITIAL_SYMBOL_STATE,
} from './constants';

/**
 * Plateau en cascade fourni par `utils-slots` — c'est la brique tumble de Stake.
 * Aucun moteur de board ni de cascade n'est écrit ici.
 */
const board = _.range(BOARD_DIMENSIONS.x).map((reelIndex) => {
	const reel = createReelForCascading({
		reelIndex,
		symbolHeight: SYMBOL_SIZE,
		initialSymbols: INITIAL_BOARD[reelIndex],
		initialSymbolState: INITIAL_SYMBOL_STATE,
		// Points d'accroche requis par `utils-slots`. Le son et les réactions
		// d'atterrissage seront branchés ici quand l'audio du jeu existera.
		onReelStopping: () => {},
		onSymbolLand: () => {},
	});

	reel.reelState.spinOptions = () =>
		reel.reelState.spinType === 'fast' ? SPIN_OPTIONS_FAST : SPIN_OPTIONS_DEFAULT;

	return reel;
});

export type Reel = (typeof board)[number];
export type ReelSymbol = Reel['reelState']['symbols'][number];

/**
 * Symbole du plateau de tumble — le plateau temporaire sur lequel se joue la
 * cascade, distinct du plateau normal. C'est le découpage de `apps/cluster` :
 * pendant la cascade le plateau normal est masqué, le plateau de tumble anime
 * l'explosion et la chute, puis le résultat est reversé au plateau normal.
 */
export type TumbleSymbol = {
	symbolY: Tween<number>;
	rawSymbol: RawSymbol;
	symbolState: SymbolState;
	oncomplete: () => void;
};

export const stateGame = $state({
	board,
	gameType: 'basegame' as GameType,
	/**
	 * Le plafond de gain a ete atteint pendant CE pari.
	 *
	 * Drapeau d'etat, pas un calcul : seul l'event `wincap` du Book le leve, et
	 * `finalWin` le rabaisse a la fin du pari. Le frontend ne detecte jamais le
	 * plafond lui-meme.
	 *
	 * Rien ne le LIT encore — l'animation Max Win viendra avec sa propre etape.
	 * Il existe pour que la celebration s'y accroche sans avoir a reinterpreter
	 * les montants, exactement comme `stateBet.winBookEventAmount`.
	 */
	wincapReached: false,
	/** Symboles qui arrivent par le haut pendant la cascade. */
	tumbleBoardAdding: [] as TumbleSymbol[][],
	/** Symboles déjà en place au moment où la cascade commence. */
	tumbleBoardBase: [] as TumbleSymbol[][],
});

/**
 * Centre de la grille dans l'espace de design du jeu.
 *
 * Horizontalement : centré. Verticalement : centré dans la bande qui reste une
 * fois le logo et la game bar réservés — pas au milieu de l'écran, sinon la
 * grille descend sous l'UI sur les layouts où celle-ci est haute (portrait).
 *
 *   y = logo + (hauteur − logo − gameBar) / 2
 */
const boardLayout = () => {
	const mainLayout = stateLayoutDerived.mainLayout();
	const bands = LAYOUT_BANDS[stateLayoutDerived.layoutType()];

	return {
		x: mainLayout.width * 0.5,
		y: (mainLayout.height + bands.logo - bands.gameBar) * 0.5,
		anchor: { x: 0.5, y: 0.5 },
		pivot: { x: BOARD_SIZES.width / 2, y: BOARD_SIZES.height / 2 },
		...BOARD_SIZES,
	};
};

const boardRaw = () =>
	board.map((reel) => reel.reelState.symbols.map((reelSymbol) => reelSymbol.rawSymbol));

/**
 * Plateau de tumble complet : les arrivants au-dessus, les rescapés en dessous.
 * L'index dans ce tableau est l'index de plateau — 0 est la ligne de padding
 * haute, hors champ.
 */
const tumbleBoardCombined = () =>
	stateGame.tumbleBoardAdding.map((tumbleReelAdding, reelIndex) => [
		...tumbleReelAdding,
		...(stateGame.tumbleBoardBase[reelIndex] ?? []),
	]);

const { enhanceBoard } = createEnhanceBoard();
const enhancedBoard = enhanceBoard({ board: stateGame.board });

export const stateGameDerived = {
	boardLayout,
	boardRaw,
	tumbleBoardCombined,
	enhancedBoard,
};
