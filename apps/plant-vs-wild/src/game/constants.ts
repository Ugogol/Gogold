import type { RawSymbol, SymbolState } from './types';

/**
 * Espaces de design du jeu, un par `layoutType` de `utils-layout`.
 *
 * `createLayout` ne redimensionne jamais un élément individuellement : il calcule
 * un `scale` global (`Math.min(widthScale, heightScale)`) qui projette cet espace
 * logique sur le viewport réel. Toutes les proportions internes — cellule, gap,
 * symbole — sont donc conservées par construction.
 *
 * ⚠️ Le ratio de chaque espace reprend celui de l'espace STANDARD correspondant
 * de `packages/utils-layout/src/createLayout.svelte.ts` :
 *
 *   desktop    1920×1080  1,7778   ←  1422×800   1,7775
 *   tablet     1920×1920  1,0000   ←   800×800   1,0000
 *   landscape  1920×1080  1,7778   ←  1422×800   1,7775
 *   portrait   1080×1920  0,5625   ←   600×1067  0,5623
 *
 * C'est ce qui rend `LAYOUT_BANDS.gameBar` fiable : les deux espaces subissent
 * alors le même rapport de mise à l'échelle quel que soit le viewport, donc la
 * bande réservée à l'UI Stake ne dérive jamais. Ne pas casser cet alignement.
 */
export const MAIN_SIZES_MAP = {
	desktop: { width: 1422, height: 800 },
	tablet: { width: 800, height: 800 },
	landscape: { width: 1422, height: 800 },
	portrait: { width: 600, height: 1067 },
};

export type LayoutType = keyof typeof MAIN_SIZES_MAP;

/** Hauteurs des espaces standard Stake, relevées dans `createLayout.svelte.ts`. */
const STANDARD_HEIGHTS: Record<LayoutType, number> = {
	desktop: 1080,
	tablet: 1920,
	landscape: 1080,
	portrait: 1920,
};

/**
 * Hauteur réellement occupée par la game bar Stake, en unités de son espace
 * STANDARD. Ces valeurs sont MESURÉES dans `packages/components-ui-pixi`, pas
 * choisies : chaque layout y positionne son bloc par rapport au bas de l'espace
 * standard, et les libellés montent au-dessus du bloc.
 *
 *   desktop    bloc à H-145 (BASE 135 + 10), libellés à -160  → ~240
 *   tablet     bloc à H-165 (BASE 135 + 30), libellés à -220  → ~320
 *   landscape  bloc à H-205 (BASE 165 + 40), éléments à  -90  → ~215
 *   portrait   drawer déplié, élément le plus haut à H-670    → ~670
 *
 * À revérifier si l'UI Stake est mise à jour.
 */
const GAME_BAR_STANDARD: Record<LayoutType, number> = {
	desktop: 240,
	tablet: 320,
	landscape: 215,
	portrait: 670,
};

/** Bande haute réservée au logo. Aucun asset de logo n'existe encore. */
const LOGO_BAND: Record<LayoutType, number> = {
	desktop: 80,
	tablet: 100,
	landscape: 35,
	portrait: 200,
};

export const isMobileLayout = (layoutType: LayoutType) =>
	layoutType === 'portrait' || layoutType === 'landscape';

/**
 * Game bar MOBILE simplifiée.
 *
 * Divergence assumée vis-à-vis de `LayoutPortrait` / `LayoutLandscape` de Stake,
 * qui empilent en bas d'écran un drawer complet (menu, buy, bet, autospin,
 * turbo, balance) plus une rangée persistante — 670 unités standard en portrait,
 * soit 29 % de la hauteur d'un téléphone. Trop chargé pour l'usage réel au pouce.
 *
 * Composition retenue sur mobile :
 *
 *   ┌──────────────────────────────────┐
 *   │  (menu)            ( SPIN )      │   Spin centré et dominant,
 *   └──────────────────────────────────┘   Menu discret en bas à gauche
 *
 * Ni Buy, ni Bet, ni Balance comme contrôles principaux : ils passeront derrière
 * le Menu. Desktop et tablet conservent la réservation dérivée de l'UI Stake.
 *
 * `band` est la hauteur totale réservée ; `spin` et `menu` sont des diamètres ;
 * `bottomMargin` est la distance entre le bas de l'écran et le bas des boutons.
 * Tout est en unités de design du layout concerné.
 *
 * Les boutons sont ancrés par `bottomMargin`, PAS centrés dans la bande : la
 * bande est une réserve qui peut grandir (libellés de gain, compteur de free
 * spins) sans décoller le Spin du bas de l'écran, là où le pouce l'atteint.
 */
export const MOBILE_BAR = {
	portrait: { band: 280, spin: 170, menu: 92, sideMargin: 44, bottomMargin: 40 },
	landscape: { band: 180, spin: 140, menu: 80, sideMargin: 56, bottomMargin: 22 },
} as const;

/**
 * Bandes réservées, exprimées dans l'espace de design DU JEU.
 *
 *   ┌───────────────┐  logo      ancrée en haut du VIEWPORT
 *   ├───────────────┤
 *   │   GRID 5×5    │  centrée dans ce qui reste
 *   ├───────────────┤
 *   └───────────────┘  gameBar   ancrée en bas du VIEWPORT
 *
 * Les deux bandes sont ancrées aux bords réels de l'écran, pas à ceux de
 * l'espace de design : sur un écran plus large ou plus haut que l'espace, ce
 * dernier ne le remplit pas, et une bande ancrée au design flotterait loin du
 * bord. Le centrage de la grille reste `(hauteur + logo − gameBar) / 2` — la
 * démonstration est dans `stateGame.svelte.ts`.
 */
export const LAYOUT_BANDS = Object.fromEntries(
	(Object.keys(MAIN_SIZES_MAP) as LayoutType[]).map((layoutType) => [
		layoutType,
		{
			logo: LOGO_BAND[layoutType],
			gameBar: isMobileLayout(layoutType)
				? MOBILE_BAR[layoutType as keyof typeof MOBILE_BAR].band
				: (GAME_BAR_STANDARD[layoutType] * MAIN_SIZES_MAP[layoutType].height) /
					STANDARD_HEIGHTS[layoutType],
		},
	]),
) as Record<LayoutType, { logo: number; gameBar: number }>;

/**
 * Géométrie de la grille, en unités logiques.
 *
 * `SYMBOL_SIZE` est le PAS de la grille — la distance entre deux centres de
 * cases — et non la taille dessinée d'une case. C'est la convention de
 * `utils-slots`, qui le reçoit comme `symbolHeight`.
 *
 *   pas          104          SYMBOL_SIZE
 *   gouttière     10          CELL_GAP
 *   case          94          CELL_SIZE   = pas − gouttière
 *   symbole     86,5          = case × SYMBOL_DISPLAY_RATIO
 *   grille    520×520         = pas × 5
 *
 * 520 est la plus grande grille carrée qui tienne dans la bande la plus étroite
 * des quatre layouts — desktop : 800 − 80 (logo) − 177,8 (game bar) = 542,2.
 * Le cadre décoratif ayant été abandonné, plus rien d'autre ne contraint cette
 * valeur : elle vient uniquement de la composition ci-dessus.
 */
export const SYMBOL_SIZE = 104;

/**
 * Gouttière entre deux cases, ~9,6 % du pas. Le pas ne bouge pas quand on
 * l'ajuste : aucun centre de case ne se déplace.
 */
export const CELL_GAP = 10;

/** Côté de la case dessinée. */
export const CELL_SIZE = SYMBOL_SIZE - CELL_GAP;

/**
 * Décalage horizontal des colonnes, en fraction du pas.
 *
 * Les samples Stake utilisent 0,53 : leurs plateaux sont posés dans un décor dont
 * l'ouverture n'est pas centrée. Sans cadre, 0,5 est la seule valeur qui centre
 * réellement la grille — 0,53 la décalait de 3 unités vers la droite.
 */
export const REEL_PADDING = 0.5;

/** Une colonne = 5 cases visibles + 2 cases de padding hors champ. */
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

/**
 * Ordre de dessin des calques.
 *
 * `pixi-svelte` trie les enfants par zIndex à chaque ajout : c'est ce qui fait
 * autorité, pas l'ordre de montage. Indispensable ici — le plateau se démonte et
 * se remonte à chaque tumble, et repasserait sinon devant les multiplicateurs.
 */
/**
 * Ratio des sprites de fond. Ce n'est pas une préférence de cadrage : c'est la
 * forme RÉELLE des assets, dont `createBackgroundLayout` se sert pour choisir
 * l'axe à étirer — c'est ce qui produit le comportement « cover ».
 *
 * Vit ici parce que deux endroits en ont besoin : `stateLayout.ts` pour cadrer
 * le fond, et `BackgroundGoo.svelte` pour retrouver la taille à l'écran du
 * sprite (le helper de layout ne renvoie qu'UNE dimension, l'autre se déduit
 * de ce ratio).
 *
 * À corriger si un fond est réexporté dans un autre format.
 */
export const BACKGROUND_RATIO = {
	normal: 1920 / 1080,
	portrait: 1080 / 1920,
};

/**
 * Glu orange qui goutte de la grande plante, à droite du décor.
 *
 * PUREMENT DÉCORATIF : n'écoute aucun bookEvent, ne lit aucun résultat, ne peut
 * donc rien révéler d'un round et n'interfère avec aucun gameplay.
 *
 * ── TOUT EST EN FRACTIONS DE L'IMAGE DE FOND, JAMAIS EN PIXELS ──────────────
 * La plante est peinte DANS le fond, lequel est mis à l'échelle en « cover » :
 * sa position à l'écran change avec le viewport. Exprimer l'effet en fractions
 * de l'image le colle donc à la plante sur tous les formats, sans un seul
 * réglage par appareil.
 *
 * Valeurs relevées sur les assets eux-mêmes, pas estimées à l'œil : la pointe
 * basse de la bave peinte est à (0.786, 0.500) sur `background.webp` et à
 * (0.761, 0.437) sur `background-mobile.webp`. Les fonds Bonus portent la
 * plante au même endroit (écart < 0.01), l'effet n'a donc pas à se masquer
 * pendant le Bonus.
 *
 * ── POUR AJUSTER ────────────────────────────────────────────────────────────
 *   `anchor`  déplace la glu suspendue      (x et y, fractions du fond)
 *   `ground`  hauteur d'impact de la goutte (fraction de la hauteur du fond)
 *   `hangWidth` / `dropWidth` / `splashWidth`  tailles, fractions de la largeur
 *   `delay`   intervalle entre deux gouttes, en millisecondes
 *   les autres durées sont en millisecondes
 */
export const BACKGROUND_GOO = {
	/** Réglages propres aux écrans couchés, où le fond est le 1920×1080. */
	landscape: {
		anchor: { x: 0.786, y: 0.5 },
		ground: 0.78,
		hangWidth: 0.052,
		dropWidth: 0.018,
		splashWidth: 0.05,
	},
	/** Écrans debout : autre asset, autre cadrage, donc autres fractions. */
	portrait: {
		anchor: { x: 0.761, y: 0.437 },
		ground: 0.63,
		hangWidth: 0.085,
		dropWidth: 0.03,
		splashWidth: 0.08,
	},

	/** Respiration de la glu suspendue : très discrète, jamais un mouvement. */
	breathe: { amplitude: 0.045, duration: 2400 },

	/** Attente entre deux gouttes, bornes en millisecondes. */
	delay: { min: 4000, max: 9000 },

	/** La goutte s'étire avant de se détacher, puis tombe en accélérant. */
	stretchDuration: 420,
	fallDuration: 780,

	/** L'éclaboussure : petit scale-up et fondu. */
	splashDuration: 300,
	splashScaleFrom: 0.45,

	/** Variation aléatoire d'une goutte à l'autre, pour éviter la répétition. */
	jitter: { x: 0.008, size: 0.2 },
};

export const zIndexes = {
	/**
	 * Décor, sous tout le reste. Numéroté par dizaines : la glu doit s'insérer
	 * ENTRE les fonds et le jeu, et des entiers consécutifs ne laissaient pas
	 * de place. Seul l'ordre relatif compte.
	 */
	background: {
		backdrop: -40,
		normal: -30,
		/** Le fond Bonus se superpose au fond Base pendant le fondu croisé. */
		bonus: -20,
		/** La glu est devant les deux fonds, et derrière tout le jeu. */
		goo: -10,
	},
	boardCells: 0,
	board: 1,
	tumbleBoard: 2,
	multiplierGrid: 3,
	wildFlight: 4,
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
 * Texture du Wild selon sa charge.
 *
 * Table explicite plutôt qu'un calcul : la charge 4 — l'état d'attente du Bonus —
 * réutilise volontairement la texture de l'état 3. Il n'existe pas de cinquième
 * visuel, et le frontend ne fait donc aucun min/max pour en déduire un.
 *
 * Les quatre états viennent de l'atlas, comme tous les autres symboles.
 */
export const WILD_CHARGE_ASSET_MAP: Record<number, string> = {
	0: 'wild_01.png',
	1: 'wild_02.png',
	2: 'wild_03.png',
	3: 'wild_04.png',
	4: 'wild_04.png',
};

/**
 * Badge de multiplicateur de case.
 *
 * Tout est dérivé de `CELL_SIZE` : aucune des 25 positions n'est écrite en dur,
 * et le badge suit la cellule sur tous les layouts.
 *
 * Volontairement sobre : un texte sur une pastille sombre. Pas de police bitmap
 * — le projet n'en embarque aucune — pas de Spine, pas de filtre. À 25 cases,
 * un glow permanent coûterait plus qu'il n'apporte.
 */
export const MULTIPLIER_BADGE = {
	/** Position verticale dans la cellule, en fraction de sa hauteur. */
	offsetRatio: 0.34,
	height: 26,
	paddingX: 12,
	/** Largeur approximative d'un caractère, pour dimensionner la pastille. */
	charWidth: 11,
	fontFamily: 'system-ui, sans-serif',
	fontSize: 19,
	fill: 0xffe9a8,
	backgroundColor: 0x120c04,
	backgroundAlpha: 0.82,
	borderColor: 0xffc94d,
	borderAlpha: 0.55,
} as const;

/**
 * Compteur de Free Spins et bandeau d'annonce.
 *
 * Volontairement sobres : ni police bitmap ni Spine dans le projet, et le polish
 * final de l'UI n'est pas l'objet de cette étape.
 */
export const FREE_SPIN_PANEL = {
	width: 300,
	height: 46,
	fontFamily: 'system-ui, sans-serif',
	fontSize: 24,
	fill: 0xffe9a8,
	backgroundColor: 0x120c04,
	backgroundAlpha: 0.82,
	borderColor: 0xffc94d,
	borderAlpha: 0.55,
} as const;

/** Durées de transition, en millisecondes. */
export const TRANSITION_DURATION = {
	/** Fondu croisé entre le fond Base et le fond Bonus. */
	background: 600,
	/** Apparition et disparition du compteur. */
	counter: 300,
	/** Apparition et disparition du bandeau. */
	banner: 250,
} as const;

export const FREE_SPIN_BANNER = {
	width: 620,
	/** Part maximale de la largeur d'écran que le bandeau peut occuper. */
	maxWidthRatio: 0.92,
	height: 240,
	holdDuration: 1100,
	fontFamily: 'system-ui, sans-serif',
	titleSize: 64,
	subtitleSize: 28,
	titleFill: 0xffe9a8,
	subtitleFill: 0xffc94d,
	backgroundColor: 0x0b0704,
	backgroundAlpha: 0.9,
	borderColor: 0xffc94d,
	borderAlpha: 0.7,
	veilColor: 0x000000,
	veilAlpha: 0.55,
	zIndex: 50,
} as const;

/**
 * Rendu d'un Wild TEMPORAIRE (Wild Split).
 *
 * Il porte toujours la texture de l'état 0 — il n'a pas de charge — et une
 * opacité réduite pour se distinguer du Wild permanent. Distinction provisoire :
 * la vraie différenciation visuelle relève de la DA, aucun asset dédié n'a été
 * livré.
 */
export const WILD_TEMPORARY = {
	alpha: 0.72,
	sizeRatio: 0.88,
} as const;

/** Durée d'un PAS du Wild Snake, en millisecondes. Un trajet peut faire 24 cases. */
export const WILD_SNAKE_STEP_DURATION = 135;

/** Durée du vol du Wild vers sa destination, en millisecondes. */
export const WILD_MOVE_DURATION = 420;

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

/**
 * Opacité du fond de case.
 *
 * Trois valeurs candidates pour la revue visuelle — changer `CELL_OPACITY` pour
 * en essayer une autre, rien d'autre à toucher. Ce n'est volontairement pas un
 * système de thème : juste un point de réglage unique.
 */
export const CELL_OPACITY_PRESETS = {
	faible: 0.1,
	moyen: 0.18,
	appuye: 0.26,
} as const;

export const CELL_OPACITY: number = CELL_OPACITY_PRESETS.moyen;

/**
 * Style des cases : discret par construction.
 *
 * Fond sombre teinté vers le vert du décor, laissant l'arrière-plan perceptible.
 * Le liseré n'est là que pour détacher la case du fond quand celui-ci est clair ;
 * il reste sous le seuil de visibilité consciente. Aucun glow, aucune texture.
 */
export const CELL_STYLE = {
	backgroundColor: 0x0b1f18,
	backgroundAlpha: CELL_OPACITY,
	borderColor: 0xa8ffd8,
	borderAlpha: 0.1,
	borderWidth: 1,
	borderRadius: 8,
} as const;
