// ⚠️ FICHIER GÉNÉRÉ — NE PAS ÉDITER À LA MAIN.
//
// Produit par `tooling/debug/sync-math-books.mjs` à partir de :
//   ../../math/games/0_0_plant_vs_wild/canonical_books
//
// Régénérer :
//   pnpm --filter=<app> run sync:math-books
//
// Les Books sont ceux du Math SDK, copiés SANS transformation. Le frontend ne
// recalcule rien : il les rejoue par le pipeline Stake normal.
import type { BookEvent } from '../../game/typesBookEvent';

import mathBaseNoWin from './math-base-no-win.json';
import mathSimpleCluster from './math-simple-cluster.json';
import mathMultiCascade from './math-multi-cascade.json';
import mathWildConnection from './math-wild-connection.json';
import mathMultipliers from './math-multipliers.json';
import mathBonusTrigger from './math-bonus-trigger.json';
import mathFreeSpins from './math-free-spins.json';
import mathRetrigger from './math-retrigger.json';
import mathRage from './math-rage.json';
import mathSnake from './math-snake.json';
import mathSplit from './math-split.json';
import v5Zero from './v5-zero.json';
import v5Basegame from './v5-basegame.json';
import v5FreegameLow from './v5-freegame-low.json';
import v5FreegameMedium from './v5-freegame-medium.json';
import v5FreegameMediumLong from './v5-freegame-medium-long.json';
import v5FreegameHigh from './v5-freegame-high.json';
import v5FreegameMega from './v5-freegame-mega.json';
import v5Wincap from './v5-wincap.json';

/**
 * Unique frontière de typage entre le JSON du Math et le contrat frontend.
 *
 * Un import JSON n'a pas de type littéral : TypeScript en déduit `string` là où
 * le contrat attend une union. La conformité réelle est vérifiée AVANT la copie
 * par le script de synchronisation, qui échoue si un Book s'en écarte.
 */
const eventsOf = (book: { events: unknown[] }): BookEvent[] => book.events as BookEvent[];

export type MathBook = {
	id: string;
	label: string;
	payoutMultiplier: number;
	events: BookEvent[];
};

export const mathBooks: MathBook[] = [
	{
		id: 'math-base-no-win',
		label: "No Win",
		payoutMultiplier: 0,
		events: eventsOf(mathBaseNoWin),
	},
	{
		id: 'math-simple-cluster',
		label: "Simple Cluster",
		payoutMultiplier: 80,
		events: eventsOf(mathSimpleCluster),
	},
	{
		id: 'math-multi-cascade',
		label: "Multi Cascade",
		payoutMultiplier: 320,
		events: eventsOf(mathMultiCascade),
	},
	{
		id: 'math-wild-connection',
		label: "Wild Connection",
		payoutMultiplier: 150,
		events: eventsOf(mathWildConnection),
	},
	{
		id: 'math-multipliers',
		label: "Multipliers",
		payoutMultiplier: 120,
		events: eventsOf(mathMultipliers),
	},
	{
		id: 'math-bonus-trigger',
		label: "Bonus Trigger",
		payoutMultiplier: 4400,
		events: eventsOf(mathBonusTrigger),
	},
	{
		id: 'math-free-spins',
		label: "Free Spins",
		payoutMultiplier: 280,
		events: eventsOf(mathFreeSpins),
	},
	{
		id: 'math-retrigger',
		label: "Retrigger",
		payoutMultiplier: 34340,
		events: eventsOf(mathRetrigger),
	},
	{
		id: 'math-rage',
		label: "Rage",
		payoutMultiplier: 470,
		events: eventsOf(mathRage),
	},
	{
		id: 'math-snake',
		label: "Wild Snake",
		payoutMultiplier: 380,
		events: eventsOf(mathSnake),
	},
	{
		id: 'math-split',
		label: "Wild Split",
		payoutMultiplier: 4640,
		events: eventsOf(mathSplit),
	},
	{
		id: 'v5-zero',
		label: "V5 / ZERO",
		payoutMultiplier: 0,
		events: eventsOf(v5Zero),
	},
	{
		id: 'v5-basegame',
		label: "V5 / BASEGAME",
		payoutMultiplier: 80,
		events: eventsOf(v5Basegame),
	},
	{
		id: 'v5-freegame-low',
		label: "V5 / FREEGAME LOW",
		payoutMultiplier: 80,
		events: eventsOf(v5FreegameLow),
	},
	{
		id: 'v5-freegame-medium',
		label: "V5 / FREEGAME MEDIUM",
		payoutMultiplier: 2040,
		events: eventsOf(v5FreegameMedium),
	},
	{
		id: 'v5-freegame-medium-long',
		label: "V5 / FREEGAME MEDIUM LONG",
		payoutMultiplier: 2060,
		events: eventsOf(v5FreegameMediumLong),
	},
	{
		id: 'v5-freegame-high',
		label: "V5 / FREEGAME HIGH",
		payoutMultiplier: 16170,
		events: eventsOf(v5FreegameHigh),
	},
	{
		id: 'v5-freegame-mega',
		label: "V5 / FREEGAME MEGA",
		payoutMultiplier: 56250,
		events: eventsOf(v5FreegameMega),
	},
	{
		id: 'v5-wincap',
		label: "V5 / WINCAP",
		payoutMultiplier: 1000000,
		events: eventsOf(v5Wincap),
	},
];

/** Série déterministe pour le bouton NEXT MATH. Aucun tirage. */
export const genericMathSpinIds: string[] = ['math-base-no-win', 'math-simple-cluster', 'math-multi-cascade', 'math-wild-connection', 'math-multipliers', 'math-base-no-win', 'math-rage', 'math-snake', 'math-split', 'math-free-spins'];
