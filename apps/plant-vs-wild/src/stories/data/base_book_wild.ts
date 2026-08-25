import type { Bet, BookEvent, BookEventOfType } from '../../game/typesBookEvent';
import type { RawSymbol, SymbolName } from '../../game/types';

/**
 * Books mockés DÉTERMINISTES pour le Wild — écrits à la main, sans aucun tirage.
 *
 * Ni multiplicateur, ni Free Spins, ni feature : cette série sert uniquement à
 * prouver que le frontend sait jouer les états du Wild que le Book lui donne.
 *
 * ⚠️ INDEXATION DES LIGNES — convention Stake, voir `base_book_cascade.ts` :
 * un reel contient 7 entrées, l'index 0 est la ligne de padding haute, les
 * index 1 à 5 les lignes visibles, l'index 6 le padding bas. Un `Position.row`
 * est cet index-là.
 *
 * Les montants sont MOCK, en centièmes de mise. Aucune paytable n'existe.
 */

const MOCK_WIN = 180; // TEST_ONLY — 1,80×, valeur arbitraire

/** Raccourci de lecture : une colonne s'écrit comme une liste de noms. */
const reel = (...names: SymbolName[]): RawSymbol[] => names.map((name) => ({ name }));

// ─── Mode A — le Wild est déjà là au reveal ──────────────────────────────────

/**
 * Plateau de référence, réutilisé par la plupart des scénarios.
 *
 *     L2 H1 L3 H2 L4        ← index 1
 *     L3 L1 L1 H3 L2        ← index 2   ┐ les 3 L1 …
 *     H2 L1 W  L4 H1        ← index 3   ┘ … et le Wild forment la connexion
 *     L4 H3 L2 H1 L3        ← index 4
 *     H1 L2 H3 L4 L2        ← index 5
 */
const boardWithWild = (charge: number): RawSymbol[][] => [
	reel('L4', 'L2', 'L3', 'H2', 'L4', 'H1', 'L3'),
	reel('L3', 'H1', 'L1', 'L1', 'H3', 'L2', 'L4'),
	[
		...reel('H2', 'L3', 'L1'),
		{ name: 'W', charge },
		...reel('L2', 'H3', 'L1'),
	],
	reel('L1', 'H2', 'H3', 'L4', 'H1', 'L4', 'L2'),
	reel('L2', 'L4', 'L2', 'H1', 'L3', 'L2', 'H2'),
];

const revealWithWild = (charge: number): BookEventOfType<'reveal'> => ({
	index: 0,
	type: 'reveal',
	board: boardWithWild(charge),
	paddingPositions: [0, 0, 0, 0, 0],
	gameType: 'basegame',
	anticipation: [0, 0, 0, 0, 0],
});

/** Le Wild est fourni par le plateau : le frontend ne le « tire » pas. */
export const bookWildAtReveal: Bet = {
	id: 10,
	payoutMultiplier: 0,
	state: [revealWithWild(0), { index: 1, type: 'setTotalWin', amount: 0 }],
};

// ─── La connexion : 3 symboles identiques + le Wild ──────────────────────────

/** Position du Wild avant la connexion. */
export const WILD_FROM = { reel: 2, row: 3 };
/** Destination, choisie par le Math parmi les cases libérées. */
export const WILD_TO = { reel: 1, row: 3 };

/**
 * Les 4 cases de la connexion : trois L1 plus le Wild. C'est le Math qui
 * l'établit — jamais le frontend, qui ne sait pas qu'un Wild remplace un symbole.
 */
export const CONNECTION_POSITIONS = [
	{ reel: 1, row: 2 },
	{ reel: 1, row: 3 },
	{ reel: 2, row: 2 },
	WILD_FROM,
];

const connectionWinInfo = (index: number): BookEventOfType<'winInfo'> => ({
	index,
	type: 'winInfo',
	totalWin: MOCK_WIN,
	wins: [
		{
			symbol: 'L1',
			clusterSize: 4,
			win: MOCK_WIN,
			positions: CONNECTION_POSITIONS,
			meta: {
				globalMult: 1,
				clusterMult: 1,
				winWithoutMult: 1.8,
				overlay: { reel: 1, row: 2 },
			},
		},
	],
});

/**
 * Refill de la connexion.
 *
 * `explodingSymbols` EXCLUT la destination du Wild : c'est le Book qui est
 * cohérent, le frontend ne filtre rien. La case de départ du Wild, elle, y
 * figure — elle est bien libérée puis recomplétée.
 *
 * Résultat attendu, calculé à la main :
 *   reel1  [H2, L3, H1, W, H3, L2, L4]   le Wild reste sur la ligne 3
 *   reel2  [L4, L2, H2, L3, L2, H3, L1]
 */
const connectionTumble = (index: number): BookEventOfType<'tumbleBoard'> => ({
	index,
	type: 'tumbleBoard',
	explodingSymbols: [
		{ reel: 1, row: 2 },
		{ reel: 2, row: 2 },
		WILD_FROM,
	],
	newSymbols: [[], [{ name: 'H2' }], [{ name: 'L4' }, { name: 'L2' }], [], []],
});

/**
 * Une connexion impliquant le Wild, de `charge` à `charge + 1`.
 *
 * La charge d'arrivée est écrite dans le Book, pas déduite : le paramètre sert
 * uniquement à fabriquer les quatre fixtures sans les recopier.
 */
const wildConnectionBook = ({ from, to, id }: { from: number; to: number; id: number }): Bet => ({
	id,
	payoutMultiplier: MOCK_WIN,
	state: [
		revealWithWild(from),
		connectionWinInfo(1),
		{ index: 2, type: 'wildMove', from: WILD_FROM, to: WILD_TO, charge: to },
		connectionTumble(3),
		{ index: 4, type: 'setTotalWin', amount: MOCK_WIN },
	],
});

export const bookWildCharge1: Bet = wildConnectionBook({ from: 0, to: 1, id: 11 });
export const bookWildCharge2: Bet = wildConnectionBook({ from: 1, to: 2, id: 12 });
export const bookWildCharge3: Bet = wildConnectionBook({ from: 2, to: 3, id: 13 });

/**
 * 4e connexion : la charge atteint le maximum et le spin passe en attente de
 * Bonus. Le Bonus NE démarre PAS — aucun `freeSpinTrigger` n'est émis ici. La
 * cascade se termine normalement et l'état est conservé jusqu'au bout.
 */
export const bookWildBonusPending: Bet = wildConnectionBook({ from: 3, to: 4, id: 14 });

// ─── Modes B et C — le Wild arrive avec un refill ───────────────────────────

/**
 * ⚠️ Où atterrit un symbole neuf.
 *
 * Après un tumble, les rescapés glissent vers le bas et les nouveaux symboles
 * remplissent le HAUT de la colonne, dans l'ordre du Book. Avec deux cases
 * retirées, les arrivants occupent donc les index 0 et 1 — et l'index 0 est la
 * ligne de padding, hors champ.
 *
 * Le Wild doit donc être le DERNIER de sa liste pour tomber le plus bas et
 * rester visible. Rien n'est deviné côté frontend : c'est l'ordre du Book qui
 * décide, et ces deux fixtures le démontrent.
 */

/** Mode B — cluster sur les lignes 2 et 3 ; le Wild arrive ligne 1. */
const boardRefill: RawSymbol[][] = [
	reel('L4', 'L2', 'L3', 'H2', 'L4', 'H1', 'L3'),
	reel('L3', 'H1', 'L1', 'L1', 'H3', 'L2', 'L4'),
	reel('H2', 'L3', 'L1', 'L1', 'L2', 'H3', 'L1'),
	reel('L1', 'H2', 'H3', 'L4', 'H1', 'L4', 'L2'),
	reel('L2', 'L4', 'L2', 'H1', 'L3', 'L2', 'H2'),
];

/**
 * Mode C — cluster sur les lignes 1 et 2 : le Wild atterrit dans une case que la
 * connexion vient de LIBÉRER.
 *
 * Les rescapés diffèrent volontairement de ceux du mode B, sinon les deux
 * scénarios donneraient le même plateau final et la démonstration ne se verrait
 * pas à l'écran.
 */
const boardReleased: RawSymbol[][] = [
	reel('L4', 'L2', 'L3', 'H2', 'L4', 'H1', 'L3'),
	reel('L3', 'L1', 'L1', 'L4', 'H1', 'L2', 'L4'),
	reel('H2', 'L1', 'L1', 'H3', 'L3', 'H3', 'L1'),
	reel('L1', 'H2', 'H3', 'L4', 'H1', 'L4', 'L2'),
	reel('L2', 'L4', 'L2', 'H1', 'L3', 'L2', 'H2'),
];

const clusterRows = (rowA: number, rowB: number) => [
	{ reel: 1, row: rowA },
	{ reel: 1, row: rowB },
	{ reel: 2, row: rowA },
	{ reel: 2, row: rowB },
];

const plainReveal = (board: RawSymbol[][]): BookEventOfType<'reveal'> => ({
	index: 0,
	type: 'reveal',
	board,
	paddingPositions: [0, 0, 0, 0, 0],
	gameType: 'basegame',
	anticipation: [0, 0, 0, 0, 0],
});

const plainWinInfo = (positions: { reel: number; row: number }[]): BookEventOfType<'winInfo'> => ({
	index: 1,
	type: 'winInfo',
	totalWin: MOCK_WIN,
	wins: [
		{
			symbol: 'L1',
			clusterSize: 4,
			win: MOCK_WIN,
			positions,
			meta: {
				globalMult: 1,
				clusterMult: 1,
				winWithoutMult: 1.8,
				overlay: positions[0],
			},
		},
	],
});

/** Aucun `wildMove` : le Wild n'était pas là, il arrive avec les nouveaux symboles. */
const refillBook = ({
	id,
	board,
	positions,
}: {
	id: number;
	board: RawSymbol[][];
	positions: { reel: number; row: number }[];
}): Bet => ({
	id,
	payoutMultiplier: MOCK_WIN,
	state: [
		plainReveal(board),
		plainWinInfo(positions),
		{
			index: 2,
			type: 'tumbleBoard',
			explodingSymbols: positions,
			newSymbols: [
				[],
				[{ name: 'H2' }, { name: 'W', charge: 0 }],
				[{ name: 'L4' }, { name: 'L2' }],
				[],
				[],
			],
		},
		{ index: 3, type: 'setTotalWin', amount: MOCK_WIN },
	],
});

export const bookWildFromRefill: Bet = refillBook({
	id: 15,
	board: boardRefill,
	positions: clusterRows(2, 3),
});

export const bookWildInReleasedCell: Bet = refillBook({
	id: 16,
	board: boardReleased,
	positions: clusterRows(1, 2),
});

// ─── Events isolés, pour les stories ─────────────────────────────────────────

export const wildEvents = {
	revealCharge0: revealWithWild(0),
	revealCharge1: revealWithWild(1),
	revealCharge2: revealWithWild(2),
	revealCharge3: revealWithWild(3),
	revealCharge4: revealWithWild(4),
	winInfo: connectionWinInfo(1),
	wildMove: { index: 2, type: 'wildMove', from: WILD_FROM, to: WILD_TO, charge: 1 } as BookEvent,
	tumbleBoard: connectionTumble(3),
};

export default {
	bookWildAtReveal,
	bookWildCharge1,
	bookWildCharge2,
	bookWildCharge3,
	bookWildBonusPending,
	bookWildFromRefill,
	bookWildInReleasedCell,
	wildEvents,
};
