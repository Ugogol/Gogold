import type { Bet, BookEvent, BookEventOfType } from '../../game/typesBookEvent';
import type { RawSymbol, SymbolName } from '../../game/types';
import { emptyGrid, withValues } from './base_book_multiplier';

/**
 * Books mockés DÉTERMINISTES des features Bonus — écrits à la main.
 *
 * Les trois features : **Rage**, **Wild Snake** et **Wild Split**.
 *
 * Rien n'est tiré au hasard : chaque position, chaque symbole et chaque plateau
 * est écrit en toutes lettres. Aucune fréquence de feature, aucune répartition
 * 65/35 n'existe ici — cela appartiendra au Math.
 *
 * ⚠️ INDEXATION — un `Position.row` est l'index dans le reel PADDÉ (0 = padding,
 * 1 à 5 visibles, 6 = padding) ; `gridMultipliers` ne couvre que les lignes
 * visibles. Voir `boardRowToGridRow` dans `game/utils.ts`.
 */

const MOCK_WIN = 320; // TEST_ONLY

const reel = (...names: SymbolName[]): RawSymbol[] => names.map((name) => ({ name }));

type Position = { reel: number; row: number };

/** Case centrale de la grille 5×5, en indexation paddée. */
const CENTER: Position = { reel: 2, row: 3 };

/** Grille de multiplicateurs déjà acquise avant la feature. */
const GRID_BEFORE = withValues(emptyGrid(), [
	{ positions: [{ reel: 0, row: 1 }], value: 2 },
	{ positions: [{ reel: 1, row: 3 }], value: 8 },
	{ positions: [{ reel: 3, row: 4 }], value: 64 },
]);

const winInfo = (
	index: number,
	symbol: SymbolName,
	positions: Position[],
): BookEventOfType<'winInfo'> => ({
	index,
	type: 'winInfo',
	totalWin: MOCK_WIN,
	wins: [
		{
			symbol,
			clusterSize: positions.length,
			win: MOCK_WIN,
			positions,
			meta: { globalMult: 1, clusterMult: 1, winWithoutMult: 3.2, overlay: positions[0] },
		},
	],
});

const bonusReveal = (index: number, board: RawSymbol[][]): BookEventOfType<'reveal'> => ({
	index,
	type: 'reveal',
	board,
	paddingPositions: [0, 0, 0, 0, 0],
	gameType: 'freegame',
	anticipation: [0, 0, 0, 0, 0],
});

// ─── RAGE ────────────────────────────────────────────────────────────────────

/** Position du Wild avant Rage — hors du centre, pour que le recentrage se voie. */
const RAGE_WILD_FROM: Position = { reel: 0, row: 1 };

/**
 * Plateau avant Rage. Aucune connexion : le spin est stabilisé, c'est ce qui
 * autorise la feature.
 *
 *     W  L2 L3 H4 L4        ← 1
 *     L3 H1 L1 H3 L2        ← 2
 *     H2 L4 L1 L4 H1        ← 3
 *     L4 H3 L2 H1 L3        ← 4
 *     H1 L2 H3 L4 L2        ← 5
 */
const rageBoardBefore: RawSymbol[][] = [
	[...reel('L3'), { name: 'W', charge: 2 }, ...reel('L3', 'H2', 'L4', 'H1', 'L2')],
	reel('L4', 'L2', 'H1', 'L4', 'H3', 'L2', 'L3'),
	reel('L2', 'L3', 'L1', 'L1', 'L2', 'H3', 'L4'),
	reel('H1', 'H4', 'H3', 'L4', 'H1', 'L4', 'L1'),
	reel('L3', 'L4', 'L2', 'H1', 'L3', 'L2', 'H2'),
];

/**
 * Plateau APRÈS Rage — fourni tel quel par le Book, Wild déjà au centre.
 *
 *     L4 L2 H4 L3 L1        ← 1
 *     H3 L1 L3 H1 L4        ← 2
 *     L1 L1 W  L2 H2        ← 3   ← le Wild, recentré
 *     H1 L1 L4 H3 L3        ← 4
 *     L3 H2 L2 L4 H1        ← 5
 *
 * Une connexion de 4 L1 y est présente : la résolution normale reprend donc
 * après la feature, exactement comme après un refill.
 */
const rageBoardAfter: RawSymbol[][] = [
	reel('L3', 'L4', 'H3', 'L1', 'H1', 'L3', 'L2'),
	reel('L4', 'L2', 'L1', 'L1', 'L1', 'H2', 'L3'),
	[...reel('L2', 'H4', 'L3'), { name: 'W', charge: 2 }, ...reel('L4', 'L2', 'H1')],
	reel('H1', 'L3', 'H1', 'L2', 'H3', 'L4', 'L1'),
	reel('L2', 'L1', 'L4', 'H2', 'L3', 'H1', 'L4'),
];

/** Les 4 L1 connectés du plateau renouvelé. */
const RAGE_CLUSTER: Position[] = [
	{ reel: 0, row: 3 },
	{ reel: 1, row: 2 },
	{ reel: 1, row: 3 },
	{ reel: 1, row: 4 },
];

export const bookRage: Bet = {
	id: 40,
	payoutMultiplier: MOCK_WIN,
	state: [
		{ index: 0, type: 'updateFreeSpin', amount: 5, total: 10 },
		bonusReveal(1, rageBoardBefore),
		{ index: 2, type: 'updateGrid', gridMultipliers: GRID_BEFORE },
		// Aucune connexion : le plateau est stabilisé. La feature arrive alors.
		// AUCUN `updateGrid` ne l'accompagne — les multiplicateurs sont conservés.
		{
			index: 3,
			type: 'wildFeature',
			feature: 'rage',
			wildFrom: RAGE_WILD_FROM,
			wildTo: CENTER,
			board: rageBoardAfter,
		},
		// La résolution normale reprend : le plateau renouvelé produit une connexion.
		winInfo(4, 'L1', RAGE_CLUSTER),
		{
			index: 5,
			type: 'updateGrid',
			// (1,3) valait déjà x8 et reparticipe : elle monte à x16. Les trois
			// autres partent du x1 implicite. C'est le Math qui décide ces valeurs.
			gridMultipliers: withValues(GRID_BEFORE, [
				{
					positions: [
						{ reel: 0, row: 3 },
						{ reel: 1, row: 2 },
						{ reel: 1, row: 4 },
					],
					value: 2,
				},
				{ positions: [{ reel: 1, row: 3 }], value: 16 },
			]),
		},
		{
			index: 6,
			type: 'tumbleBoard',
			explodingSymbols: RAGE_CLUSTER,
			newSymbols: [reel('H2'), reel('L3', 'H1', 'L4'), [], [], []],
		},
		{ index: 7, type: 'setTotalWin', amount: MOCK_WIN },
	],
};

// ─── WILD SPLIT ──────────────────────────────────────────────────────────────

/** Le Wild permanent, celui qui porte la charge et que `wildMove` suit. */
const SPLIT_STANDARD_WILD: Position = { reel: 2, row: 3 };

/** Les 3 temporaires, posés aux cases que le Book désigne. */
const SPLIT_POSITIONS: Position[] = [
	{ reel: 0, row: 2 },
	{ reel: 3, row: 2 },
	{ reel: 4, row: 4 },
];

/**
 * Plateau avant Wild Split. Le Wild permanent est au centre, chargé à 2.
 *
 *     L2 L3 H4 L4 H1        ← 1
 *     L1 H1 L3 L1 L2        ← 2   ← deux temporaires arriveront ici
 *     H2 L4 W  L4 H3        ← 3
 *     L4 H3 L2 H1 L1        ← 4   ← le troisième arrivera ici
 *     H1 L2 H3 L4 L2        ← 5
 */
const splitBoardBefore: RawSymbol[][] = [
	reel('L3', 'L2', 'L1', 'H2', 'L4', 'H1', 'L2'),
	reel('L4', 'L3', 'H1', 'L4', 'H3', 'L2', 'L3'),
	[...reel('L2', 'H4', 'L3'), { name: 'W', charge: 2 }, ...reel('L2', 'H3', 'L4')],
	reel('H1', 'L4', 'L1', 'L4', 'H1', 'L4', 'L1'),
	reel('L3', 'H1', 'L2', 'H3', 'L1', 'L2', 'H2'),
];

/**
 * Connexion utilisant UN temporaire : trois L1 plus le Wild temporaire de
 * (reel 0, ligne 2). Le Wild permanent n'y participe pas — sa charge ne bouge
 * donc pas, et aucun `wildMove` n'est émis.
 */
const SPLIT_CLUSTER: Position[] = [
	{ reel: 0, row: 2 },
	{ reel: 3, row: 2 },
	{ reel: 3, row: 4 },
	{ reel: 4, row: 4 },
];

export const bookWildSplit: Bet = {
	id: 41,
	payoutMultiplier: MOCK_WIN,
	state: [
		{ index: 0, type: 'updateFreeSpin', amount: 6, total: 10 },
		bonusReveal(1, splitBoardBefore),
		{ index: 2, type: 'updateGrid', gridMultipliers: GRID_BEFORE },
		// Plateau stabilisé, puis la feature.
		{ index: 3, type: 'wildFeature', feature: 'wildSplit', positions: SPLIT_POSITIONS },
		// À cet instant : 1 Wild permanent + 3 temporaires = 4 Wild à l'écran.
		winInfo(4, 'L1', SPLIT_CLUSTER),
		{
			index: 5,
			type: 'updateGrid',
			gridMultipliers: withValues(GRID_BEFORE, [{ positions: SPLIT_CLUSTER, value: 2 }]),
		},
		/**
		 * Consommation. Le Book retire les cases gagnantes — dont deux temporaires
		 * — ET le troisième temporaire resté inutilisé, dont la durée expire ici.
		 * Le frontend ne décide jamais qu'un temporaire « a servi » : il applique.
		 * Le Wild permanent, lui, n'est pas dans la liste : il survit.
		 */
		{
			index: 6,
			type: 'tumbleBoard',
			explodingSymbols: [...SPLIT_CLUSTER, { reel: 4, row: 4 }].filter(
				(position, index, all) =>
					all.findIndex((other) => other.reel === position.reel && other.row === position.row) ===
					index,
			),
			newSymbols: [reel('H2'), [], [], reel('L3', 'H1'), reel('L4')],
		},
		{ index: 7, type: 'setTotalWin', amount: MOCK_WIN },
	],
};

// ─── WILD SNAKE ──────────────────────────────────────────────────────────────

/**
 * Plateau avant Snake — le Wild est en haut à gauche, aucune connexion.
 *
 *     W  L3 L4 H2 L1        ← 1
 *     L2 H3 L2 L1 L4        ← 2
 *     H1 L1 H4 L4 L2        ← 3
 *     L3 L2 L3 H1 H2        ← 4
 *     L4 H1 L2 L3 L4        ← 5
 */
const SNAKE_FROM: Position = { reel: 0, row: 1 };

const snakeBoardBefore: RawSymbol[][] = [
	[...reel('L4'), { name: 'W', charge: 2 }, ...reel('L2', 'H1', 'L3', 'L4', 'H2')],
	reel('L2', 'L3', 'H3', 'L1', 'L2', 'H1', 'L4'),
	reel('H1', 'L4', 'L2', 'H4', 'L3', 'L2', 'L1'),
	reel('L3', 'H2', 'L1', 'L4', 'H1', 'L3', 'H3'),
	reel('L2', 'L1', 'L4', 'L2', 'H2', 'L4', 'L3'),
];

/** Trajet court : trois cases traversées, puis l'arrivée. */
const SNAKE_SHORT_PATH: Position[] = [
	{ reel: 0, row: 2 },
	{ reel: 0, row: 3 },
	{ reel: 1, row: 3 },
];
const SNAKE_SHORT_TO: Position = { reel: 2, row: 3 };

/**
 * Plateau après le Snake court, conversion vers L3.
 *
 * ⚠️ Ce plateau EST la règle : c'est lui qui décide ce que devient la case de
 * départ et ce que porte la case d'arrivée. Ici la fixture a retenu — case de
 * départ convertie, Wild déposé à l'arrivée — mais le game design n'a pas encore
 * tranché. Le frontend, lui, ne décide rien : il applique.
 */
const snakeBoardAfterShort: RawSymbol[][] = [
	reel('L4', 'L3', 'L3', 'L3', 'L3', 'L4', 'H2'),
	reel('L2', 'L3', 'H3', 'L3', 'L2', 'H1', 'L4'),
	[...reel('H1', 'L4', 'L2'), { name: 'W', charge: 2 }, ...reel('L3', 'L2', 'L1')],
	reel('L3', 'H2', 'L1', 'L4', 'H1', 'L3', 'H3'),
	reel('L2', 'L1', 'L4', 'L2', 'H2', 'L4', 'L3'),
];

/** Les 5 L3 connectés que le Snake vient de créer. */
const SNAKE_CLUSTER: Position[] = [
	{ reel: 0, row: 1 },
	{ reel: 0, row: 2 },
	{ reel: 0, row: 3 },
	{ reel: 0, row: 4 },
	{ reel: 1, row: 3 },
];

/** Trajet long : neuf cases traversées, conversion vers un High. */
const SNAKE_LONG_PATH: Position[] = [
	{ reel: 0, row: 2 },
	{ reel: 0, row: 3 },
	{ reel: 0, row: 4 },
	{ reel: 0, row: 5 },
	{ reel: 1, row: 5 },
	{ reel: 2, row: 5 },
	{ reel: 2, row: 4 },
	{ reel: 2, row: 3 },
	{ reel: 2, row: 2 },
];
const SNAKE_LONG_TO: Position = { reel: 3, row: 2 };

const snakeBoardAfterLong: RawSymbol[][] = [
	reel('L4', 'H2', 'H2', 'H2', 'H2', 'H2', 'H2'),
	reel('L2', 'L3', 'H3', 'L1', 'L2', 'H2', 'L4'),
	reel('H1', 'L4', 'H2', 'H2', 'H2', 'H2', 'L1'),
	[...reel('L3', 'H2'), { name: 'W', charge: 2 }, ...reel('L4', 'H1', 'L3', 'H3')],
	reel('L2', 'L1', 'L4', 'L2', 'H2', 'L4', 'L3'),
];

const snakeEvent = (
	index: number,
	{ path, to, symbol, board }: {
		path: Position[];
		to: Position;
		symbol: SymbolName;
		board: RawSymbol[][];
	},
): BookEvent => ({
	index,
	type: 'wildFeature',
	feature: 'wildSnake',
	from: SNAKE_FROM,
	path,
	to,
	symbol,
	board,
});

/** Conversion vers un LOW, trajet court, puis résolution normale. */
export const bookWildSnake: Bet = {
	id: 42,
	payoutMultiplier: MOCK_WIN,
	state: [
		{ index: 0, type: 'updateFreeSpin', amount: 7, total: 10 },
		bonusReveal(1, snakeBoardBefore),
		{ index: 2, type: 'updateGrid', gridMultipliers: GRID_BEFORE },
		// Plateau stabilisé. La feature arrive, SANS `updateGrid` : Snake ne
		// touche jamais aux multiplicateurs.
		snakeEvent(3, {
			path: SNAKE_SHORT_PATH,
			to: SNAKE_SHORT_TO,
			symbol: 'L3',
			board: snakeBoardAfterShort,
		}),
		// La résolution normale reprend sur le plateau que le Snake a produit.
		winInfo(4, 'L3', SNAKE_CLUSTER),
		{
			index: 5,
			type: 'updateGrid',
			gridMultipliers: withValues(GRID_BEFORE, [{ positions: SNAKE_CLUSTER, value: 2 }]),
		},
		{
			index: 6,
			type: 'tumbleBoard',
			explodingSymbols: SNAKE_CLUSTER,
			newSymbols: [reel('H1', 'L2', 'H3', 'L1'), reel('H2'), [], [], []],
		},
		{ index: 7, type: 'setTotalWin', amount: MOCK_WIN },
	],
};

/** Conversion vers un HIGH, trajet long. Pas de cascade : la feature seule. */
export const bookWildSnakeLong: Bet = {
	id: 43,
	payoutMultiplier: 0,
	state: [
		{ index: 0, type: 'updateFreeSpin', amount: 8, total: 10 },
		bonusReveal(1, snakeBoardBefore),
		{ index: 2, type: 'updateGrid', gridMultipliers: GRID_BEFORE },
		snakeEvent(3, {
			path: SNAKE_LONG_PATH,
			to: SNAKE_LONG_TO,
			symbol: 'H2',
			board: snakeBoardAfterLong,
		}),
		{ index: 4, type: 'setTotalWin', amount: 0 },
	],
};

// ─── Events isolés, pour les stories ─────────────────────────────────────────

export const featureEvents = {
	rageReveal: bonusReveal(0, rageBoardBefore),
	rageGrid: { index: 0, type: 'updateGrid', gridMultipliers: GRID_BEFORE } as BookEvent,
	rage: {
		index: 0,
		type: 'wildFeature',
		feature: 'rage',
		wildFrom: RAGE_WILD_FROM,
		wildTo: CENTER,
		board: rageBoardAfter,
	} as BookEvent,
	rageAfterCluster: bookRage.state[4],

	splitReveal: bonusReveal(0, splitBoardBefore),
	split: {
		index: 0,
		type: 'wildFeature',
		feature: 'wildSplit',
		positions: SPLIT_POSITIONS,
	} as BookEvent,
	splitWinInfo: winInfo(0, 'L1', SPLIT_CLUSTER),
	splitConsume: bookWildSplit.state[6],

	snakeReveal: bonusReveal(0, snakeBoardBefore),
	/** Trajet court, conversion vers un Low. */
	snakeShort: snakeEvent(0, {
		path: SNAKE_SHORT_PATH,
		to: SNAKE_SHORT_TO,
		symbol: 'L3',
		board: snakeBoardAfterShort,
	}),
	/** Trajet long, conversion vers un High. */
	snakeLong: snakeEvent(0, {
		path: SNAKE_LONG_PATH,
		to: SNAKE_LONG_TO,
		symbol: 'H2',
		board: snakeBoardAfterLong,
	}),
	snakeWinInfo: winInfo(0, 'L3', SNAKE_CLUSTER),
};

export const featurePositions = {
	center: CENTER,
	rageWildFrom: RAGE_WILD_FROM,
	standardWild: SPLIT_STANDARD_WILD,
	splitPositions: SPLIT_POSITIONS,
};

export default {
	bookRage,
	bookWildSplit,
	bookWildSnake,
	bookWildSnakeLong,
	featureEvents,
	featurePositions,
};
