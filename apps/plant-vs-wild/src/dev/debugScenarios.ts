import type { BookEvent } from '../game/typesBookEvent';
import type { RawSymbol, SymbolName } from '../game/types';
import { WILD_MAX_CHARGE } from '../game/config';
import { emptyGrid } from '../stories/data/base_book_multiplier';
import cascade from '../stories/data/base_book_cascade';
import wild from '../stories/data/base_book_wild';
import multiplier from '../stories/data/base_book_multiplier';
import bonus from '../stories/data/base_book_bonus';
import feature from '../stories/data/base_book_feature';

/**
 * Registre DEV des scénarios jouables — DÉVELOPPEMENT UNIQUEMENT.
 *
 * Il ne contient presque aucune donnée : il RÉFÉRENCE les Books déterministes
 * déjà écrits et validés aux étapes 5 à 9. Seuls trois plateaux perdants sont
 * ajoutés ici, faute d'équivalent existant.
 *
 * Aucun tirage, aucune probabilité, aucun `Math.random` : la « variété » des
 * spins génériques est une liste écrite à la main que l'on parcourt en boucle.
 */

const reel = (...names: SymbolName[]): RawSymbol[] => names.map((name) => ({ name }));

/** Plateau sans aucune connexion — vérifié à la main : aucun groupe de 4. */
const losingBoardA: RawSymbol[][] = [
	reel('L3', 'L1', 'L3', 'H2', 'L4', 'H1', 'L2'),
	reel('L4', 'H3', 'L2', 'L4', 'H1', 'L3', 'L1'),
	reel('L2', 'L4', 'H1', 'L3', 'L2', 'H3', 'L4'),
	reel('H1', 'L2', 'L4', 'H2', 'L1', 'L4', 'L3'),
	reel('L3', 'H2', 'L3', 'L1', 'H3', 'L2', 'H1'),
];

const losingBoardB: RawSymbol[][] = [
	reel('L1', 'H1', 'L4', 'L2', 'H3', 'L3', 'L4'),
	reel('L2', 'L3', 'H2', 'L1', 'L4', 'H1', 'L2'),
	reel('H3', 'L4', 'L1', 'H4', 'L3', 'L2', 'H1'),
	reel('L4', 'L2', 'L3', 'L4', 'H2', 'L1', 'L3'),
	reel('L3', 'H4', 'L2', 'H1', 'L1', 'L4', 'H2'),
];

const losingBoardC: RawSymbol[][] = [
	reel('L2', 'L4', 'H1', 'L3', 'L1', 'H2', 'L4'),
	reel('H1', 'L1', 'L3', 'H3', 'L4', 'L2', 'L3'),
	reel('L4', 'H2', 'L2', 'L1', 'H1', 'L3', 'L2'),
	reel('L3', 'L3', 'L4', 'H2', 'L2', 'H4', 'L1'),
	reel('H2', 'L2', 'H3', 'L4', 'L3', 'L1', 'H1'),
];

/**
 * Spin perdant : reveal, grille remise à zéro, fin de résolution.
 *
 * C'est la séquence minimale d'un spin. Rien d'autre n'est nécessaire pour que
 * le pipeline se déroule et se termine proprement.
 */
const losingSpin = (board: RawSymbol[][]): BookEvent[] => [
	{
		index: 0,
		type: 'reveal',
		board,
		paddingPositions: [0, 0, 0, 0, 0],
		gameType: 'basegame',
		anticipation: [0, 0, 0, 0, 0],
	},
	{ index: 1, type: 'updateGrid', gridMultipliers: emptyGrid() },
	{ index: 2, type: 'setTotalWin', amount: 0 },
];

/**
 * Book de remise à plat, joué par le bouton RESET.
 *
 * Il passe par le pipeline normal comme tous les autres : `reveal` en
 * `basegame` remet le mode, `updateGrid` vide la grille. Les éléments d'UI du
 * Bonus sont masqués par le panneau via leurs emitterEvents existants.
 */
export const resetBook: BookEvent[] = losingSpin(losingBoardA);

export type DebugScenario = {
	id: string;
	label: string;
	group: 'BASE' | 'BONUS' | 'GENERIC';
	events: BookEvent[];
};

/** Le spin déclencheur seul : les 8 premiers events du book Bonus. */
const bonusTriggerOnly = bonus.bookBonus.state.slice(0, 8);

export const debugScenarios: DebugScenario[] = [
	// ── Base Game ────────────────────────────────────────────────────────────
	{ id: 'base-no-win', label: 'Base — No Win', group: 'BASE', events: losingSpin(losingBoardA) },
	{
		id: 'base-simple-cluster',
		label: 'Base — Simple Cluster',
		group: 'BASE',
		events: cascade.bookEvents,
	},
	{
		id: 'base-multi-cascade',
		label: 'Base — Multi Cascade',
		group: 'BASE',
		events: multiplier.bookMultiplierCascade.state,
	},
	{
		id: 'base-wild-reveal',
		label: 'Base — Wild Reveal',
		group: 'BASE',
		events: wild.bookWildAtReveal.state,
	},
	{
		id: 'base-wild-connection',
		label: 'Base — Wild Connection',
		group: 'BASE',
		events: wild.bookWildCharge1.state,
	},
	{
		id: 'base-wild-charge',
		label: 'Base — Wild Charge (2 → 3)',
		group: 'BASE',
		events: wild.bookWildCharge3.state,
	},
	{
		id: 'base-multipliers',
		label: 'Base — Multipliers (x2 puis x4)',
		group: 'BASE',
		events: multiplier.bookMultiplierCascade.state,
	},
	{
		id: 'base-bonus-trigger',
		label: `Base — Bonus Trigger (charge ${WILD_MAX_CHARGE})`,
		group: 'BASE',
		events: bonusTriggerOnly,
	},

	// ── Bonus ────────────────────────────────────────────────────────────────
	{
		id: 'bonus-free-spins',
		label: 'Bonus — Free Spins',
		group: 'BONUS',
		events: bonus.bookBonus.state,
	},
	{
		id: 'bonus-no-win-spins',
		label: 'Bonus — Free Spins sans gain',
		group: 'BONUS',
		events: bonus.bookBonusNoWinSpins.state,
	},
	{ id: 'bonus-rage', label: 'Bonus — Rage', group: 'BONUS', events: feature.bookRage.state },
	{
		id: 'bonus-snake',
		label: 'Bonus — Wild Snake (court, Low)',
		group: 'BONUS',
		events: feature.bookWildSnake.state,
	},
	{
		id: 'bonus-snake-long',
		label: 'Bonus — Wild Snake (long, High)',
		group: 'BONUS',
		events: feature.bookWildSnakeLong.state,
	},
	{
		id: 'bonus-split',
		label: 'Bonus — Wild Split',
		group: 'BONUS',
		events: feature.bookWildSplit.state,
	},
	{
		id: 'bonus-full-demo',
		label: 'Bonus — Full Demo (trigger → retrigger → sortie)',
		group: 'BONUS',
		events: bonus.bookBonus.state,
	},
	{
		id: 'bonus-back-to-base',
		label: 'Bonus — Retour Base Game',
		group: 'BONUS',
		events: bonus.bookAfterBonus.state,
	},
];

/**
 * Série générique déterministe.
 *
 * Elle sert uniquement à cliquer plusieurs fois de suite et voir défiler des
 * spins variés — perdants, petits gains, cascades, Wild, multiplicateurs. Ce
 * n'est PAS du Math : l'ordre est écrit à la main et la liste boucle.
 */
export const genericSpins: { label: string; events: BookEvent[] }[] = [
	{ label: 'no win', events: losingSpin(losingBoardA) },
	{ label: 'petit cluster', events: cascade.bookEvents },
	{ label: 'no win', events: losingSpin(losingBoardB) },
	{ label: 'multi cascade', events: multiplier.bookMultiplierCascade.state },
	{ label: 'Wild au reveal', events: wild.bookWildAtReveal.state },
	{ label: 'cluster + multiplicateur', events: multiplier.bookMultiplierWithWild.state },
	{ label: 'connexion Wild', events: wild.bookWildCharge1.state },
	{ label: 'no win', events: losingSpin(losingBoardC) },
];
