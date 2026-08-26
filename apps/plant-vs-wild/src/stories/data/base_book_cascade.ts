import type { Bet, BookEvent, BookEventOfType } from '../../game/typesBookEvent';

/**
 * Book mocké DÉTERMINISTE — une seule cascade, écrite à la main.
 *
 * Il n'y a ni Wild, ni multiplicateur, ni Bonus, ni feature : le but est
 * d'isoler le pipeline cluster/tumble et rien d'autre.
 *
 * ⚠️ INDEXATION DES LIGNES — convention Stake, vérifiée sur les books réels de
 * `apps/cluster` : un reel du book contient les lignes VISIBLES plus une ligne
 * de padding en haut ET en bas. `createReelForCascading` calcule
 * `symbolIndexOfBoard = index - 1`, donc :
 *
 *     index 0        padding, au-dessus du champ
 *     index 1 → 5    les 5 lignes visibles
 *     index 6        padding, sous le champ
 *
 * Un `Position.row` est cet index-là. Dans les books Stake réels, les rows de
 * `winInfo.positions` et de `explodingSymbols` ne valent jamais 0 ni 8 sur un
 * tableau de 9 : elles désignent bien les seules lignes visibles.
 *
 * Les montants sont MOCK, en centièmes de mise comme chez Stake. Ils n'ont
 * aucune signification mathématique : aucune paytable n'existe.
 */

const MOCK_WIN = 250; // TEST_ONLY — 2,50×, valeur arbitraire

/**
 * Plateau initial. Le cluster est le carré de 4 L1 au centre gauche :
 *
 *     .  L1 H1 H2 L4        ← index 1
 *     L3 L1 L1 H3 L2        ← index 2   ┐ les deux lignes
 *     H2 L1 L1 L4 H1        ← index 3   ┘ du cluster
 *     L4 H3 L2 H1 L3        ← index 4
 *     H1 L2 H3 L4 L2        ← index 5
 */
const reveal: BookEventOfType<'reveal'> = {
	index: 0,
	type: 'reveal',
	board: [
		[
			{ name: 'L3' },
			{ name: 'L1' },
			{ name: 'L3' },
			{ name: 'H2' },
			{ name: 'L4' },
			{ name: 'H1' },
			{ name: 'L2' },
		],
		[
			{ name: 'L4' },
			{ name: 'L2' },
			{ name: 'L1' },
			{ name: 'L1' },
			{ name: 'H3' },
			{ name: 'L2' },
			{ name: 'L3' },
		],
		[
			{ name: 'L2' },
			{ name: 'H1' },
			{ name: 'L1' },
			{ name: 'L1' },
			{ name: 'L2' },
			{ name: 'H3' },
			{ name: 'L4' },
		],
		[
			{ name: 'H1' },
			{ name: 'H2' },
			{ name: 'H3' },
			{ name: 'L4' },
			{ name: 'H1' },
			{ name: 'L4' },
			{ name: 'L1' },
		],
		[
			{ name: 'L3' },
			{ name: 'L4' },
			{ name: 'L2' },
			{ name: 'H1' },
			{ name: 'L3' },
			{ name: 'L2' },
			{ name: 'H2' },
		],
	],
	paddingPositions: [0, 0, 0, 0, 0],
	gameType: 'basegame',
	anticipation: [0, 0, 0, 0, 0],
};

/** Les 4 cases du cluster, désignées par le Math. Le frontend ne les cherche pas. */
const CLUSTER_POSITIONS = [
	{ reel: 1, row: 2 },
	{ reel: 1, row: 3 },
	{ reel: 2, row: 2 },
	{ reel: 2, row: 3 },
];

const winInfo: BookEventOfType<'winInfo'> = {
	index: 1,
	type: 'winInfo',
	totalWin: MOCK_WIN,
	wins: [
		{
			symbol: 'L1',
			clusterSize: 4,
			win: MOCK_WIN,
			positions: CLUSTER_POSITIONS,
			meta: {
				globalMult: 1,
				clusterMult: 1,
				winWithoutMult: 2.5,
				overlay: { reel: 1, row: 2 },
			},
		},
	],
};

/**
 * Disparition et refill. `newSymbols` liste, par reel, les SEULS nouveaux
 * symboles — pas un plateau. Les reels 0, 3 et 4 ne perdent rien, ils ne
 * reçoivent rien.
 *
 * Résultat attendu, calculé à la main et vérifié dans le rapport :
 *   reel1  [H2, L4, L4, L2, H3, L2, L3]
 *   reel2  [H3, L2, L2, H1, L2, H3, L4]
 * Aucun groupe de 4 symboles identiques ne subsiste : la cascade s'arrête là.
 */
const tumbleBoard: BookEventOfType<'tumbleBoard'> = {
	index: 2,
	type: 'tumbleBoard',
	explodingSymbols: CLUSTER_POSITIONS,
	newSymbols: [
		[],
		[{ name: 'H2' }, { name: 'L4' }],
		[{ name: 'H3' }, { name: 'L2' }],
		[],
		[],
	],
};

/** Fin de résolution : plus aucun cluster, plus aucune cascade. */
const setTotalWin: BookEventOfType<'setTotalWin'> = {
	index: 3,
	type: 'setTotalWin',
	amount: MOCK_WIN,
};

export const bookEvents: BookEvent[] = [reveal, winInfo, tumbleBoard, setTotalWin];

/** Book complet, au format que `playBet` attend. */
export const bookCascade: Bet = {
	id: 1,
	payoutMultiplier: MOCK_WIN,
	state: bookEvents,
};

export default { reveal, winInfo, tumbleBoard, setTotalWin, bookEvents, bookCascade };
