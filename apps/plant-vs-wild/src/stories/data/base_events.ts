import type { BookEvent } from '../../game/typesBookEvent';

/**
 * Fixtures de développement — DÉTERMINISTES et fabriquées à la main.
 *
 * Elles ne viennent PAS du Math SDK : `math/games/<game_id>/` n'existe pas
 * encore. Aucun tirage aléatoire, aucun calcul : chaque objet est écrit en
 * toutes lettres. Elles seront remplacées par de vrais books produits par le
 * math (voir docs/DEBUG_PANEL.md pour le workflow d'export).
 *
 * Elles sont typées `BookEvent` : c'est TypeScript qui vérifie que le contrat
 * de `typesBookEvent.ts` est réellement satisfaisable. Un champ manquant ou mal
 * nommé casse le typecheck.
 *
 * Toutes décrivent LE MÊME scénario, pour être lisibles ensemble :
 *
 *   plateau initial          le Wild est en (reel 1, row 1)
 *   cluster L1               (0,0) (0,1) (1,0) (2,0) + le Wild  → 5 cases
 *   le Wild rejoint (0,0)    charge 1
 *   les 4 autres cases       disparaissent puis sont recomplétées
 *
 * Les montants sont en centièmes de mise, comme dans les books Stake :
 * 130 se lit 1,30×.
 */

/** Case du Wild au départ. */
const WILD_FROM = { reel: 1, row: 1 };
/** Case du groupe gagnant que le Wild rejoint. */
const WILD_TO = { reel: 0, row: 0 };

/** Les 5 cases du cluster, Wild compris. */
const CLUSTER_POSITIONS = [
	{ reel: 0, row: 0 },
	{ reel: 0, row: 1 },
	{ reel: 1, row: 0 },
	{ reel: 2, row: 0 },
	WILD_FROM,
];

const reveal: BookEvent = {
	index: 0,
	type: 'reveal',
	board: [
		[{ name: 'L1' }, { name: 'L1' }, { name: 'L2' }, { name: 'H1' }, { name: 'L3' }],
		[{ name: 'L1' }, { name: 'W' }, { name: 'L4' }, { name: 'L2' }, { name: 'H2' }],
		[{ name: 'L1' }, { name: 'L3' }, { name: 'H3' }, { name: 'L4' }, { name: 'L1' }],
		[{ name: 'H2' }, { name: 'L4' }, { name: 'L2' }, { name: 'L3' }, { name: 'L1' }],
		[{ name: 'L4' }, { name: 'L2' }, { name: 'H1' }, { name: 'L1' }, { name: 'L3' }],
	],
	paddingPositions: [0, 0, 0, 0, 0],
	gameType: 'basegame',
	anticipation: [0, 0, 0, 0, 0],
};

/** Grille remise à zéro : `0` est le x1 implicite. Base Game, début de spin. */
const updateGridReset: BookEvent = {
	index: 1,
	type: 'updateGrid',
	gridMultipliers: [
		[0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0],
	],
};

/** Le Math désigne le cluster. Le frontend ne cherche aucune connexion. */
const winInfo: BookEvent = {
	index: 2,
	type: 'winInfo',
	totalWin: 130,
	wins: [
		{
			symbol: 'L1',
			clusterSize: 5,
			win: 130,
			positions: CLUSTER_POSITIONS,
			meta: {
				globalMult: 1,
				clusterMult: 1,
				winWithoutMult: 1.3,
				overlay: { reel: 1, row: 0 },
			},
		},
	],
};

const updateTumbleWin: BookEvent = {
	index: 3,
	type: 'updateTumbleWin',
	amount: 130,
};

/** Les 5 cases ayant participé passent du x1 implicite au x2. */
const updateGridAfterWin: BookEvent = {
	index: 4,
	type: 'updateGrid',
	gridMultipliers: [
		[2, 2, 0, 0, 0],
		[2, 2, 0, 0, 0],
		[2, 0, 0, 0, 0],
		[0, 0, 0, 0, 0],
		[0, 0, 0, 0, 0],
	],
};

/**
 * Le Wild rejoint une case du groupe et gagne sa 1re charge.
 * Il part AVANT que le groupe ne disparaisse : il n'est jamais détruit.
 */
const wildMove: BookEvent = {
	index: 5,
	type: 'wildMove',
	from: WILD_FROM,
	to: WILD_TO,
	charge: 1,
};

/**
 * Le Wild progresse sans changer de case : `to` est égal à `from`.
 * Sa propre case fait partie du groupe gagnant, c'est une destination valide.
 */
const wildMoveInPlace: BookEvent = {
	index: 5,
	type: 'wildMove',
	from: WILD_FROM,
	to: WILD_FROM,
	charge: 2,
};

/** 4e charge : ce spin mènera au Bonus, une fois toutes les cascades finies. */
const wildMoveFinalCharge: BookEvent = {
	index: 5,
	type: 'wildMove',
	from: WILD_FROM,
	to: WILD_TO,
	charge: 4,
};

/**
 * Disparition et refill, en un seul event côté Stake.
 * `explodingSymbols` exclut la case d'arrivée du Wild, qui n'est pas recomplétée.
 * `newSymbols` liste, par reel, les seuls nouveaux symboles.
 */
const tumbleBoard: BookEvent = {
	index: 6,
	type: 'tumbleBoard',
	explodingSymbols: [
		{ reel: 0, row: 1 },
		{ reel: 1, row: 0 },
		{ reel: 1, row: 1 },
		{ reel: 2, row: 0 },
	],
	newSymbols: [[{ name: 'H3' }], [{ name: 'L2' }, { name: 'L4' }], [{ name: 'H1' }], [], []],
};

const setWin: BookEvent = { index: 7, type: 'setWin', amount: 130, winLevel: 1 };

/** Fin de résolution du spin : plus aucun cluster, plus aucune cascade. */
const setTotalWin: BookEvent = { index: 8, type: 'setTotalWin', amount: 130 };

/** Fin du pari complet. */
const finalWin: BookEvent = { index: 9, type: 'finalWin', amount: 130 };

/** Déclenché par la 4e charge, après le setTotalWin du spin. */
const freeSpinTrigger: BookEvent = {
	index: 10,
	type: 'freeSpinTrigger',
	totalFs: 10,
	positions: [WILD_TO],
};

/** `totalFs` est le nouveau total, pas l'incrément : 10 + 5. */
const freeSpinRetrigger: BookEvent = {
	index: 11,
	type: 'freeSpinRetrigger',
	totalFs: 15,
	positions: [WILD_TO],
};

const updateFreeSpin: BookEvent = { index: 12, type: 'updateFreeSpin', amount: 1, total: 10 };

const freeSpinEnd: BookEvent = { index: 13, type: 'freeSpinEnd', amount: 4200, winLevel: 3 };

/** Wild recentré ; le renouvellement des autres cases suit en `tumbleBoard`. */
const wildFeatureRage: BookEvent = {
	index: 14,
	type: 'wildFeature',
	feature: 'rage',
	wildTo: { reel: 2, row: 2 },
};

/**
 * Trajet fourni par le Math, ordonné, `from` et `to` exclus. Chaque pas est
 * orthogonal et aucune case n'est revisitée — c'est le Math qui le garantit.
 */
const wildFeatureSnake: BookEvent = {
	index: 15,
	type: 'wildFeature',
	feature: 'wildSnake',
	from: { reel: 0, row: 0 },
	path: [
		{ reel: 0, row: 1 },
		{ reel: 0, row: 2 },
		{ reel: 1, row: 2 },
		{ reel: 2, row: 2 },
		{ reel: 2, row: 3 },
	],
	to: { reel: 2, row: 4 },
	symbol: 'L3',
};

/** 3 Wild temporaires. Ils ne font pas monter la charge du vrai Wild. */
const wildFeatureSplit: BookEvent = {
	index: 16,
	type: 'wildFeature',
	feature: 'wildSplit',
	positions: [
		{ reel: 0, row: 4 },
		{ reel: 2, row: 2 },
		{ reel: 4, row: 0 },
	],
};

export default {
	reveal,
	updateGridReset,
	winInfo,
	updateTumbleWin,
	updateGridAfterWin,
	wildMove,
	wildMoveInPlace,
	wildMoveFinalCharge,
	tumbleBoard,
	setWin,
	setTotalWin,
	finalWin,
	freeSpinTrigger,
	freeSpinRetrigger,
	updateFreeSpin,
	freeSpinEnd,
	wildFeatureRage,
	wildFeatureSnake,
	wildFeatureSplit,
};
