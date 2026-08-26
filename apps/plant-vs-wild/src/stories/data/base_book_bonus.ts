import type { Bet, BookEvent, BookEventOfType } from '../../game/typesBookEvent';
import type { RawSymbol, SymbolName } from '../../game/types';
import { bookWildBonusPending, WILD_TO } from './base_book_wild';
import { emptyGrid, withValues } from './base_book_multiplier';

/**
 * Book mocké DÉTERMINISTE du mode Bonus — écrit à la main, sans aucun tirage.
 *
 * Il enchaîne : spin de déclenchement, transition, Free Spins, retrigger, sortie
 * de Bonus. Rien n'est décidé par le frontend — ni le déclenchement, ni le
 * nombre de spins, ni le retrigger, ni la position du Wild, ni les
 * multiplicateurs conservés.
 *
 * ⚠️ INDEXATION — un `Position.row` est l'index dans le reel PADDÉ (0 = padding,
 * 1 à 5 visibles, 6 = padding), tandis que `gridMultipliers` ne couvre que les
 * lignes visibles. Voir `boardRowToGridRow` dans `game/utils.ts`.
 *
 * Les montants sont MOCK. Aucune paytable, aucun calcul.
 */

const MOCK_WIN = 240; // TEST_ONLY
const MOCK_BONUS_TOTAL = 1860; // TEST_ONLY

const reel = (...names: SymbolName[]): RawSymbol[] => names.map((name) => ({ name }));

type Position = { reel: number; row: number };

// ─── Base Game — le spin qui déclenche ───────────────────────────────────────

/**
 * Le spin déclencheur réutilise tel quel le book Wild « charge 3 → 4 » validé à
 * l'étape 6 : reveal, connexion, déplacement du Wild, refill, fin de résolution.
 * Rien n'y est modifié — on y insère seulement les grilles de multiplicateurs,
 * puis on ajoute le `freeSpinTrigger` À LA FIN.
 *
 * C'est ce placement qui garantit que la 4e connexion n'interrompt jamais la
 * cascade : le Bonus ne peut pas démarrer avant que le spin soit résolu.
 */
const TRIGGER_POSITIONS: Position[] = [
	{ reel: 1, row: 2 },
	{ reel: 1, row: 3 },
	{ reel: 2, row: 2 },
	{ reel: 2, row: 3 },
];

/** Grille héritée par le Bonus : trois cases marquées pendant le spin déclencheur. */
const INHERITED_GRID = withValues(emptyGrid(), [
	{ positions: [{ reel: 1, row: 2 }], value: 2 },
	{ positions: [{ reel: 1, row: 3 }], value: 8 },
	{ positions: [{ reel: 2, row: 2 }], value: 32 },
]);

const triggerSpin: BookEvent[] = [
	bookWildBonusPending.state[0], // reveal — Wild à charge 3
	{ index: 1, type: 'updateGrid', gridMultipliers: emptyGrid() }, // reset Base Game
	bookWildBonusPending.state[1], // winInfo — 3 L1 + le Wild
	{ index: 3, type: 'updateGrid', gridMultipliers: INHERITED_GRID },
	bookWildBonusPending.state[2], // wildMove — charge 4, bonus pending
	bookWildBonusPending.state[3], // tumbleBoard
	{ index: 6, type: 'setTotalWin', amount: MOCK_WIN },
	// Le Bonus n'est annoncé QU'ICI, une fois le spin entièrement résolu.
	{ index: 7, type: 'freeSpinTrigger', totalFs: 10, positions: [WILD_TO] },
];

// ─── Bonus — les plateaux des Free Spins ─────────────────────────────────────

/**
 * Plateau de Free Spin.
 *
 * Le Wild est TOUJOURS à `WILD_TO`, la case qu'il occupait à la fin du spin
 * déclencheur : sa position vient du Book, jamais d'un choix du frontend. Et
 * chaque plateau de Bonus contient un Wild — c'est une garantie du Math, pas une
 * règle que le frontend applique.
 *
 * H4 est présent : il n'existe aucune règle `if bonus then allow H4` côté
 * frontend, ce symbole se rend comme les autres.
 */
const bonusBoard = (charge: number): RawSymbol[][] => [
	reel('L3', 'L1', 'L3', 'H4', 'L4', 'H1', 'L2'),
	[...reel('L4', 'L2', 'L1'), { name: 'W', charge }, ...reel('H3', 'L2', 'L3')],
	reel('L2', 'H1', 'L1', 'L1', 'L2', 'H3', 'L4'),
	reel('H1', 'L2', 'L2', 'L4', 'H1', 'L4', 'L1'),
	reel('L3', 'L2', 'L2', 'H1', 'L3', 'L2', 'H2'),
];

const bonusReveal = (index: number, charge: number): BookEventOfType<'reveal'> => ({
	index,
	type: 'reveal',
	board: bonusBoard(charge),
	paddingPositions: [0, 0, 0, 0, 0],
	gameType: 'freegame',
	anticipation: [0, 0, 0, 0, 0],
});

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
			meta: { globalMult: 1, clusterMult: 1, winWithoutMult: 2.4, overlay: positions[0] },
		},
	],
});

/** Connexion du Free Spin 1 : 4 L2 à droite, loin du Wild — il ne bouge pas. */
const FS1_CLUSTER: Position[] = [
	{ reel: 3, row: 1 },
	{ reel: 3, row: 2 },
	{ reel: 4, row: 1 },
	{ reel: 4, row: 2 },
];

/** Grille après le Free Spin 1 : l'héritée, plus les 4 cases qui viennent de gagner. */
const GRID_AFTER_FS1 = withValues(INHERITED_GRID, [{ positions: FS1_CLUSTER, value: 2 }]);

/** Connexion du Free Spin 3 : la même forme qu'en Base, le Wild y participe. */
const FS3_CLUSTER = TRIGGER_POSITIONS;

const GRID_AFTER_FS3 = withValues(GRID_AFTER_FS1, [
	{ positions: [{ reel: 1, row: 2 }], value: 4 },
	{ positions: [{ reel: 2, row: 2 }], value: 64 },
]);

// ─── Le book complet ─────────────────────────────────────────────────────────

export const bookBonus: Bet = {
	id: 30,
	payoutMultiplier: MOCK_BONUS_TOTAL,
	state: [
		...triggerSpin,

		// ── Free Spin 1 — une cascade, les multiplicateurs progressent ──────────
		// AUCUN updateGrid après le reveal : la grille du spin déclencheur est
		// donc conservée telle quelle. C'est ainsi que se fait l'héritage.
		{ index: 8, type: 'updateFreeSpin', amount: 1, total: 10 },
		bonusReveal(9, 4),
		winInfo(10, 'L2', FS1_CLUSTER),
		{ index: 11, type: 'updateGrid', gridMultipliers: GRID_AFTER_FS1 },
		{
			index: 12,
			type: 'tumbleBoard',
			explodingSymbols: FS1_CLUSTER,
			newSymbols: [
				[],
				[],
				[],
				[{ name: 'L1' }, { name: 'H2' }],
				[{ name: 'L4' }, { name: 'L1' }],
			],
		},
		{ index: 13, type: 'setTotalWin', amount: MOCK_WIN },

		// ── Free Spin 2 — spin sans gain : la grille reste celle du FS1 ─────────
		{ index: 14, type: 'updateFreeSpin', amount: 2, total: 10 },
		bonusReveal(15, 4),
		{ index: 16, type: 'setTotalWin', amount: MOCK_WIN },

		// ── Free Spin 3 — 4e connexion du Wild, puis retrigger ──────────────────
		{ index: 17, type: 'updateFreeSpin', amount: 3, total: 10 },
		bonusReveal(18, 3),
		winInfo(19, 'L1', FS3_CLUSTER),
		{ index: 20, type: 'updateGrid', gridMultipliers: GRID_AFTER_FS3 },
		{
			index: 21,
			type: 'wildMove',
			from: { reel: 1, row: 3 },
			to: { reel: 1, row: 3 },
			charge: 4,
		},
		{
			index: 22,
			type: 'tumbleBoard',
			explodingSymbols: [
				{ reel: 1, row: 2 },
				{ reel: 2, row: 2 },
				{ reel: 2, row: 3 },
			],
			newSymbols: [[], [{ name: 'H2' }], [{ name: 'L4' }, { name: 'L2' }], [], []],
		},
		{ index: 23, type: 'setTotalWin', amount: MOCK_WIN },
		// Le retrigger n'arrive qu'après la résolution complète, comme le trigger.
		// `totalFs` est le NOUVEAU total : 10 + 5.
		{ index: 24, type: 'freeSpinRetrigger', totalFs: 15, positions: [{ reel: 1, row: 3 }] },

		// ── Free Spin 4 — spin simple, compteur sur 15 ──────────────────────────
		{ index: 25, type: 'updateFreeSpin', amount: 4, total: 15 },
		bonusReveal(26, 4),
		{ index: 27, type: 'setTotalWin', amount: MOCK_WIN },

		// ── Sortie du Bonus ────────────────────────────────────────────────────
		{ index: 28, type: 'freeSpinEnd', amount: MOCK_BONUS_TOTAL, winLevel: 3 },
		// Fin de pari : la grille du Bonus est vidée et masquée.
		{ index: 29, type: 'finalWin', amount: MOCK_BONUS_TOTAL },
	],
};

/**
 * Le spin Base qui suit le Bonus.
 *
 * Il doit repartir propre : grille remise à zéro par le Book, plus aucun état de
 * Bonus. À jouer juste après `bookBonus` pour vérifier qu'aucun état ne survit.
 */
export const bookAfterBonus: Bet = {
	id: 31,
	payoutMultiplier: 0,
	state: [
		{
			index: 0,
			type: 'reveal',
			board: bonusBoard(0),
			paddingPositions: [0, 0, 0, 0, 0],
			gameType: 'basegame',
			anticipation: [0, 0, 0, 0, 0],
		},
		{ index: 1, type: 'updateGrid', gridMultipliers: emptyGrid() },
		{ index: 2, type: 'setTotalWin', amount: 0 },
	],
};

/**
 * Deux Free Spins consécutifs SANS aucune connexion.
 *
 * La séquence minimale d'un spin : `updateFreeSpin`, `reveal`, `setTotalWin`.
 * Ni `winInfo`, ni `updateGrid`, ni `tumbleBoard`, ni `wildMove` — et le spin
 * suivant s'enchaîne normalement.
 *
 * Le Wild reste présent parce que le PLATEAU du Book le contient, pas parce que
 * le frontend en ajouterait un. Aucune règle métier n'est introduite ici : c'est
 * exactement le même chemin de code qu'un spin gagnant, avec moins d'events.
 *
 * Le `reveal` déclare `gameType: 'freegame'`, ce qui suffit à placer le jeu en
 * mode Bonus même joué isolément — voir le handler `reveal`.
 */
export const bookBonusNoWinSpins: Bet = {
	id: 32,
	payoutMultiplier: 0,
	state: [
		{ index: 0, type: 'updateFreeSpin', amount: 5, total: 10 },
		bonusReveal(1, 2),
		{ index: 2, type: 'setTotalWin', amount: 0 },

		{ index: 3, type: 'updateFreeSpin', amount: 6, total: 10 },
		bonusReveal(4, 2),
		{ index: 5, type: 'setTotalWin', amount: 0 },
	],
};

// ─── Events isolés, pour les stories ─────────────────────────────────────────

export const bonusEvents = {
	freeSpinTrigger: triggerSpin[triggerSpin.length - 1],
	updateFreeSpin: { index: 0, type: 'updateFreeSpin', amount: 3, total: 10 } as BookEvent,
	freeSpinRetrigger: {
		index: 0,
		type: 'freeSpinRetrigger',
		totalFs: 15,
		positions: [{ reel: 1, row: 3 }],
	} as BookEvent,
	freeSpinEnd: {
		index: 0,
		type: 'freeSpinEnd',
		amount: MOCK_BONUS_TOTAL,
		winLevel: 3,
	} as BookEvent,
	/** Plateau de Bonus contenant H4 et le Wild. */
	bonusReveal: bonusReveal(0, 4),
	/** Grille héritée du spin déclencheur. */
	inheritedGrid: {
		index: 0,
		type: 'updateGrid',
		gridMultipliers: INHERITED_GRID,
	} as BookEvent,
};

export default { bookBonus, bookAfterBonus, bookBonusNoWinSpins, bonusEvents };
