import type { RawSymbol, SymbolState } from './types';

/**
 * Grille 5×5. Le sample Stake `apps/cluster` est en 7×7 avec SYMBOL_SIZE 80
 * (560 px de large) ; on garde une largeur de plateau comparable en 5 colonnes.
 */
export const SYMBOL_SIZE = 110;

export const REEL_PADDING = 0.53;

/** Une colonne = 5 cases visibles + 1 case de padding en haut et en bas. */
const PADDED_ROWS = 7;

const COLUMN_PATTERNS: RawSymbol['name'][][] = [
	['L1', 'H1', 'L2', 'L3', 'L1', 'H2', 'L4'],
	['L2', 'L3', 'H3', 'L1', 'L2', 'L4', 'H1'],
	['L3', 'L1', 'L4', 'H4', 'W', 'L2', 'L3'],
	['H2', 'L4', 'L2', 'L3', 'L1', 'S', 'L2'],
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
 * Apparence PROVISOIRE des symboles.
 *
 * Aucun asset n'est intégré à ce stade : chaque symbole est dessiné avec les
 * primitives PixiJS (rectangle + texte) pour que la grille soit lisible sans
 * embarquer les assets du sample Stake — qui ne peuvent pas servir de contenu
 * final (voir docs/DEFINITION_OF_DONE.md).
 *
 * Remplacé par de vrais assets à l'étape dédiée, en suivant docs/ASSET_PIPELINE.md.
 */
export const SYMBOL_PLACEHOLDER_MAP = {
	H1: { fill: 0x2f6f3e, label: 'H1' },
	H2: { fill: 0x3d8b4f, label: 'H2' },
	H3: { fill: 0x4ea862, label: 'H3' },
	H4: { fill: 0x6cc177, label: 'H4' },
	L1: { fill: 0x8a6b3f, label: 'L1' },
	L2: { fill: 0xa4834f, label: 'L2' },
	L3: { fill: 0xbe9c60, label: 'L3' },
	L4: { fill: 0xd8b673, label: 'L4' },
	W: { fill: 0x8b2f3e, label: 'W' },
	S: { fill: 0xc9a227, label: 'S' },
} as const;

/** Teinte appliquée par-dessus le symbole selon son état d'affichage. */
export const SYMBOL_STATE_STYLE: Record<string, { alpha: number; borderColor: number }> = {
	static: { alpha: 1, borderColor: 0x1b1b1b },
	spin: { alpha: 0.9, borderColor: 0x1b1b1b },
	land: { alpha: 1, borderColor: 0xffffff },
	win: { alpha: 1, borderColor: 0xffd166 },
	postWinStatic: { alpha: 0.75, borderColor: 0x1b1b1b },
	explosion: { alpha: 0.35, borderColor: 0xffd166 },
};
