import type { Bet, BookEvent, BookEventOfType } from '../../game/typesBookEvent';
import type { RawSymbol, SymbolName } from '../../game/types';
import { boardRowToGridRow } from '../../game/utils';
import { bookWildCharge1, CONNECTION_POSITIONS } from './base_book_wild';

/**
 * Books mockés DÉTERMINISTES pour les multiplicateurs de case.
 *
 * Chaque grille est écrite en toutes lettres : le frontend n'en déduit aucune,
 * et surtout il ne calcule JAMAIS la progression x2 → x4 → x8. Cette règle
 * appartient au Math ; ici elle est simplement mise en scène.
 *
 * ⚠️ DEUX INDEXATIONS — ne pas les confondre :
 *
 *   Position du board / tumble    reel paddé de 7 entrées
 *                                 0 = padding, 1 à 5 visibles, 6 = padding
 *   gridMultipliers[reel][row]    lignes VISIBLES uniquement, 0 à 4
 *
 * La conversion passe par `boardRowToGridRow`, l'unique frontière du projet.
 * Les grilles ci-dessous sont donc construites à partir des positions gagnantes
 * plutôt que recopiées à la main : impossible de se tromper d'un cran.
 */

const MOCK_WIN = 210; // TEST_ONLY — 2,10×, valeur arbitraire

const reel = (...names: SymbolName[]): RawSymbol[] => names.map((name) => ({ name }));

type Position = { reel: number; row: number };

/** Grille 5×5 remplie de zéros : le x1 implicite partout. */
export const emptyGrid = (): number[][] => Array.from({ length: 5 }, () => Array.from({ length: 5 }, () => 0));

/**
 * Écrit des valeurs dans une grille, à partir de positions du BOARD.
 *
 * C'est un outil de fixture, pas du code de jeu : il pose les valeurs qu'on lui
 * donne, il n'en calcule aucune.
 */
export const withValues = (
	base: number[][],
	entries: { positions: Position[]; value: number }[],
): number[][] => {
	const grid = base.map((column) => [...column]);
	entries.forEach(({ positions, value }) => {
		positions.forEach(({ reel: reelIndex, row }) => {
			grid[reelIndex][boardRowToGridRow(row)] = value;
		});
	});
	return grid;
};

const updateGrid = (index: number, gridMultipliers: number[][]): BookEventOfType<'updateGrid'> => ({
	index,
	type: 'updateGrid',
	gridMultipliers,
});

// ─── Le plateau du scénario principal ────────────────────────────────────────

/**
 * Deux cascades qui se recouvrent volontairement.
 *
 *     L1 L2 L2 H2 L4        ← 1
 *     L3 L1 L1 H3 L2        ← 2   ┐ 1re connexion
 *     H2 L1 L1 L4 H1        ← 3   ┘
 *     L4 H3 L2 H1 L3        ← 4
 *     H1 L2 H3 L4 L2        ← 5
 */
const board: RawSymbol[][] = [
	reel('L3', 'L1', 'L3', 'H2', 'L4', 'H1', 'L2'),
	reel('L4', 'L2', 'L1', 'L1', 'H3', 'L2', 'L3'),
	reel('L2', 'L2', 'L1', 'L1', 'L2', 'H3', 'L4'),
	reel('H1', 'H2', 'H3', 'L4', 'H1', 'L4', 'L1'),
	reel('L3', 'L4', 'L2', 'H1', 'L3', 'L2', 'H2'),
];

/** 1re connexion : 4 L1. */
const CLUSTER_1: Position[] = [
	{ reel: 1, row: 2 },
	{ reel: 1, row: 3 },
	{ reel: 2, row: 2 },
	{ reel: 2, row: 3 },
];

/**
 * 2e connexion : 4 L2, dont TROIS cases déjà utilisées par la première.
 * C'est ce recouvrement qui fait passer ces cases de x2 à x4.
 */
const CLUSTER_2: Position[] = [
	{ reel: 1, row: 3 },
	{ reel: 2, row: 2 },
	{ reel: 2, row: 3 },
	{ reel: 2, row: 4 },
];

const REUSED: Position[] = [
	{ reel: 1, row: 3 },
	{ reel: 2, row: 2 },
	{ reel: 2, row: 3 },
];
const FIRST_ONLY: Position[] = [{ reel: 1, row: 2 }];
const SECOND_ONLY: Position[] = [{ reel: 2, row: 4 }];

const winInfo = (index: number, symbol: SymbolName, positions: Position[]): BookEventOfType<'winInfo'> => ({
	index,
	type: 'winInfo',
	totalWin: MOCK_WIN,
	wins: [
		{
			symbol,
			clusterSize: positions.length,
			win: MOCK_WIN,
			positions,
			meta: { globalMult: 1, clusterMult: 1, winWithoutMult: 2.1, overlay: positions[0] },
		},
	],
});

/** Grille après la 1re connexion : les 4 cases passent du x1 implicite à x2. */
const GRID_AFTER_1 = withValues(emptyGrid(), [{ positions: CLUSTER_1, value: 2 }]);

/**
 * Grille après la 2e : les 3 cases réutilisées montent à x4, la nouvelle prend
 * x2, et celle qui n'a pas reparticipé RESTE à x2.
 */
const GRID_AFTER_2 = withValues(emptyGrid(), [
	{ positions: FIRST_ONLY, value: 2 },
	{ positions: REUSED, value: 4 },
	{ positions: SECOND_ONLY, value: 2 },
]);

/**
 * Scénario principal — deux cascades, deux grilles.
 *
 * Pas de `finalWin` : il vide et masque la grille (comportement Stake), ce qui
 * empêcherait d'observer l'état final. La fin de pari est démontrée par le
 * scénario `bookMultiplierFinalWin`.
 */
export const bookMultiplierCascade: Bet = {
	id: 20,
	payoutMultiplier: MOCK_WIN,
	state: [
		{
			index: 0,
			type: 'reveal',
			board,
			paddingPositions: [0, 0, 0, 0, 0],
			gameType: 'basegame',
			anticipation: [0, 0, 0, 0, 0],
		},
		// Début de spin : la grille est remise à zéro PAR LE BOOK.
		updateGrid(1, emptyGrid()),
		winInfo(2, 'L1', CLUSTER_1),
		updateGrid(3, GRID_AFTER_1),
		{
			index: 4,
			type: 'tumbleBoard',
			explodingSymbols: CLUSTER_1,
			newSymbols: [[], [{ name: 'H2' }, { name: 'L4' }], [{ name: 'H3' }, { name: 'H1' }], [], []],
		},
		winInfo(5, 'L2', CLUSTER_2),
		updateGrid(6, GRID_AFTER_2),
		{
			index: 7,
			type: 'tumbleBoard',
			explodingSymbols: CLUSTER_2,
			newSymbols: [
				[],
				[{ name: 'L1' }],
				[{ name: 'L3' }, { name: 'L1' }, { name: 'L4' }],
				[],
				[],
			],
		},
		{ index: 8, type: 'setTotalWin', amount: MOCK_WIN * 2 },
	],
};

/**
 * Nouveau spin : la grille repart vide.
 *
 * Le frontend ne « sait » pas qu'un spin commence — c'est l'`updateGrid` rempli
 * de zéros, placé par le Book après le `reveal`, qui remet tout à plat.
 */
export const bookMultiplierResetSpin: Bet = {
	id: 21,
	payoutMultiplier: 0,
	state: [
		{
			index: 0,
			type: 'reveal',
			board,
			paddingPositions: [0, 0, 0, 0, 0],
			gameType: 'basegame',
			anticipation: [0, 0, 0, 0, 0],
		},
		updateGrid(1, emptyGrid()),
		{ index: 2, type: 'setTotalWin', amount: 0 },
	],
};

/** Fin de pari : `finalWin` vide et masque la grille, comme dans `apps/cluster`. */
export const bookMultiplierFinalWin: Bet = {
	id: 22,
	payoutMultiplier: MOCK_WIN,
	state: [
		...bookMultiplierCascade.state,
		{ index: 9, type: 'finalWin', amount: MOCK_WIN * 2 },
	],
};

/**
 * Wild ET multiplicateurs dans la même connexion.
 *
 * Les deux mécaniques sont indépendantes : la grille suit les POSITIONS de la
 * connexion, le Wild suit la destination que le Book lui donne. Aucune des deux
 * ne dépend de l'autre. L'`updateGrid` est simplement inséré après le `winInfo`
 * du book Wild déjà validé à l'étape 6, qui n'est pas modifié.
 */
export const bookMultiplierWithWild: Bet = {
	id: 23,
	payoutMultiplier: MOCK_WIN,
	state: [
		bookWildCharge1.state[0], // reveal, Wild à charge 0
		updateGrid(1, emptyGrid()),
		bookWildCharge1.state[1], // winInfo : 3 L1 + le Wild
		updateGrid(2, withValues(emptyGrid(), [{ positions: CONNECTION_POSITIONS, value: 2 }])),
		bookWildCharge1.state[2], // wildMove
		bookWildCharge1.state[3], // tumbleBoard
		{ index: 5, type: 'setTotalWin', amount: MOCK_WIN },
	],
};

// ─── Grilles isolées, pour les stories ───────────────────────────────────────

/** Toutes les valeurs de la progression, du plus petit au cap. */
const LADDER = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096];

const gridFromValues = (values: (number | null)[][]): number[][] =>
	Array.from({ length: 5 }, (_unused, reelIndex) =>
		Array.from({ length: 5 }, (_u, gridRow) => values[gridRow]?.[reelIndex] ?? 0),
	);

export const multiplierGrids = {
	/** Rien nulle part : aucun badge ne doit apparaître. */
	empty: emptyGrid(),

	/** Une seule case, première activation. */
	single: withValues(emptyGrid(), [{ positions: [{ reel: 2, row: 3 }], value: 2 }]),

	/** Plusieurs cases à la même valeur. */
	severalX2: withValues(emptyGrid(), [{ positions: CLUSTER_1, value: 2 }]),

	/** Trois paliers côte à côte. */
	stack: withValues(emptyGrid(), [
		{ positions: [{ reel: 1, row: 2 }], value: 2 },
		{ positions: [{ reel: 2, row: 3 }], value: 4 },
		{ positions: [{ reel: 3, row: 4 }], value: 8 },
	]),

	/** Valeurs très différentes : contrôle de lisibilité et de débordement. */
	mixed: withValues(emptyGrid(), [
		{ positions: [{ reel: 0, row: 1 }], value: 2 },
		{ positions: [{ reel: 1, row: 2 }], value: 8 },
		{ positions: [{ reel: 2, row: 3 }], value: 32 },
		{ positions: [{ reel: 3, row: 4 }], value: 256 },
		{ positions: [{ reel: 4, row: 5 }], value: 4096 },
	]),

	/** Le cap, seul dans sa case. */
	cap: withValues(emptyGrid(), [{ positions: [{ reel: 2, row: 3 }], value: 4096 }]),

	/** Le pire cas d'encombrement : les 25 cases occupées par la progression. */
	full: gridFromValues([
		LADDER.slice(0, 5),
		LADDER.slice(3, 8),
		LADDER.slice(5, 10),
		LADDER.slice(7, 12),
		[4096, 2048, 1024, 512, 256],
	]),
};

export const multiplierEvents = {
	reveal: bookMultiplierCascade.state[0] as BookEvent,
	...Object.fromEntries(
		Object.entries(multiplierGrids).map(([key, grid], index) => [key, updateGrid(index, grid)]),
	),
} as Record<string, BookEvent>;

export default {
	bookMultiplierWithWild,
	bookMultiplierCascade,
	bookMultiplierResetSpin,
	bookMultiplierFinalWin,
	multiplierGrids,
	multiplierEvents,
};
