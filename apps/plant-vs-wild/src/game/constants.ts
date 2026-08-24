import type { RawSymbol, SymbolState } from './types';

/**
 * Grille 5×5. `SYMBOL_SIZE` est le PAS de la grille : la distance entre deux
 * centres de cases, pas la taille dessinée d'une case.
 *
 * 96 vient du cadrage retenu à l'étape 2 (grille de 480 px dans un canevas de
 * design haut de 800 px). Le décor `sprites/board` a été déposé depuis ; la
 * valeur peut être revue librement quand un nouveau décor arrivera.
 */
export const SYMBOL_SIZE = 96;

/**
 * Espace laissé entre deux cases. Le PAS de la grille reste `SYMBOL_SIZE` :
 * ajuster l'écartement ne déplace aucun centre de case.
 */
export const CELL_GAP = 10;

/** Côté de la case dessinée, gouttière déduite. */
export const CELL_SIZE = SYMBOL_SIZE - CELL_GAP;

export const REEL_PADDING = 0.53;

/** Une colonne = 5 cases visibles + 1 case de padding en haut et en bas. */
const PADDED_ROWS = 7;

const COLUMN_PATTERNS: RawSymbol['name'][][] = [
	['L1', 'H1', 'L2', 'L3', 'L1', 'H2', 'L4'],
	['L2', 'L3', 'H3', 'L1', 'L2', 'L4', 'H1'],
	['L3', 'L1', 'L4', 'H4', 'W', 'L2', 'L3'],
	['H2', 'L4', 'L2', 'L3', 'L1', 'H4', 'L2'],
	['L4', 'L2', 'H1', 'L1', 'L3', 'L4', 'H3'],
];

/** Plateau initial, statique et déterministe : aucun tirage aléatoire. */
export const INITIAL_BOARD: RawSymbol[][] = COLUMN_PATTERNS.map((column) =>
	column.slice(0, PADDED_ROWS).map((name) => ({ name })),
);

export const BOARD_DIMENSIONS = { x: INITIAL_BOARD.length, y: INITIAL_BOARD[0].length - 2 };

export const BOARD_SIZES = {
	width: SYMBOL_SIZE * BOARD_DIMENSIONS.x,
	height: SYMBOL_SIZE * BOARD_DIMENSIONS.y,
};

export const HIGH_SYMBOLS = ['H1', 'H2', 'H3', 'H4'];

export const INITIAL_SYMBOL_STATE: SymbolState = 'static';

const SPIN_OPTIONS_SHARED = {
	reelFallInDelay: 80,
	reelPaddingMultiplierNormal: 1.25,
	reelPaddingMultiplierAnticipated: 18,
	reelFallOutDelay: 145,
};

export const SPIN_OPTIONS_DEFAULT = {
	...SPIN_OPTIONS_SHARED,
	symbolFallInSpeed: 3.5,
	symbolFallInInterval: 30,
	symbolFallInBounceSpeed: 0.15,
	symbolFallInBounceSizeMulti: 0.5,
	symbolFallOutSpeed: 3.5,
	symbolFallOutInterval: 20,
};

export const SPIN_OPTIONS_FAST = {
	...SPIN_OPTIONS_SHARED,
	symbolFallInSpeed: 7,
	symbolFallInInterval: 0,
	symbolFallInBounceSpeed: 0.3,
	symbolFallInBounceSizeMulti: 0.25,
	symbolFallOutSpeed: 7,
	symbolFallOutInterval: 0,
};

export const zIndexes = {
	background: {
		backdrop: -3,
		normal: -2,
	},
};

/**
 * Correspondance symbole → frame de l'atlas `sprites/symbols`.
 *
 * Les frames de l'atlas gardent leur nom de fichier exact (`h1.png`, `wild_01.png`),
 * conformement au pattern Stake. Tout vient du meme atlas : aucun sprite isole.
 * `assets.ts` déclare l'atlas ; c'est cette table qui fait le lien avec les
 * identifiants math.
 *
 * H4 est intégré mais n'est pas utilisé par le Base Game à ce stade.
 * Aucun scatter : aucun asset n'a été fourni pour ce symbole.
 */
export const SYMBOL_ASSET_MAP = {
	H1: 'h1.png',
	H2: 'h2.png',
	H3: 'h3.png',
	H4: 'h4.png',
	L1: 'l1.png',
	L2: 'l2.png',
	L3: 'l3.png',
	L4: 'l4.png',
	W: 'wild_01.png',
} as const;

/**
 * Taille d'affichage d'un symbole, en proportion de `CELL_SIZE` — donc de la
 * case dessinée, pas du pas de la grille : le symbole tient dans sa case et
 * laisse voir le marquage.
 *
 * Les sources sont en 512×512 et sont réduites au rendu — elles ne sont pas
 * redimensionnées de façon destructive (docs/ASSET_PIPELINE.md).
 */
export const SYMBOL_DISPLAY_RATIO = 0.92;

/** Côté dessiné d'un symbole. */
export const SYMBOL_DISPLAY_SIZE = CELL_SIZE * SYMBOL_DISPLAY_RATIO;
