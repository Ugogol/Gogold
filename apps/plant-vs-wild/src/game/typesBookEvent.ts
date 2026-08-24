import type { SymbolName, RawSymbol, GameType, Position } from './types';

/**
 * Contrat Math/RGS → Frontend de PLANT VS WILD.
 *
 * Le Math produit un book ; le frontend le rejoue. Le frontend ne déduit jamais
 * qu'un cluster existe, quelles cases gagnent, où le Wild va, s'il progresse,
 * si le Bonus se déclenche, ni quel multiplicateur porte une case.
 *
 * Les types marqués STAKE sont repris tels quels du sample `apps/cluster` du
 * Web SDK (commit 1843d60) : payloads relevés dans son code ET dans ses books
 * réels, pas supposés. Ne pas les renommer — la documentation Stake doit rester
 * applicable.
 *
 * Deux types seulement sont spécifiques à PLANT VS WILD. Chacun porte la
 * justification de son existence.
 *
 * ⚠️ Aucun handler n'existe encore pour la plupart de ces events : ils décrivent
 * le contrat, ils ne l'implémentent pas. `bookEventHandlerMap` est un
 * `Record<string, …>` non exhaustif ; un event sans handler produit seulement la
 * trace `Missing bookEventHandler`. Les handlers viendront avec les animations.
 */

// ─── STAKE ───────────────────────────────────────────────────────────────────

/** Plateau initial du spin. Porte le Wild s'il est présent dès le départ. */
type BookEventReveal = {
	index: number;
	type: 'reveal';
	board: RawSymbol[][];
	paddingPositions: number[];
	anticipation: number[];
	gameType: GameType;
};

/**
 * Identification du cluster : `positions` EST la liste des cases gagnantes.
 * C'est le Math qui l'établit — le frontend ne cherche aucune connexion.
 *
 * `clusterSize` est présent dans les books Stake réels mais absent de leur type
 * déclaré ; il est ajouté ici parce que nos books en produiront un.
 */
type BookEventWinInfo = {
	index: number;
	type: 'winInfo';
	totalWin: number;
	wins: {
		symbol: SymbolName;
		clusterSize: number;
		win: number;
		positions: Position[];
		meta: {
			globalMult: number;
			clusterMult: number;
			winWithoutMult: number;
			/** Case où afficher le montant du cluster. */
			overlay: Position;
		};
	}[];
};

/** Gain cumulé de la cascade en cours. */
type BookEventUpdateTumbleWin = {
	index: number;
	type: 'updateTumbleWin';
	amount: number;
};

/**
 * Grille COMPLÈTE des multiplicateurs de case, `0` valant le x1 implicite.
 *
 * Toute la grille étant renvoyée à chaque fois, la remise à zéro du Base Game et
 * la persistance en Bonus ne demandent aucun event supplémentaire : c'est le
 * Math qui envoie, ou n'envoie pas, une grille remise à zéro. L'héritage des
 * multiplicateurs par le premier Free Spin est automatique — tous les Free Spins
 * vivent dans le même book.
 */
type BookEventUpdateGrid = {
	index: number;
	type: 'updateGrid';
	gridMultipliers: number[][];
};

/**
 * Disparition puis refill, en un seul event côté Stake.
 *
 * `newSymbols` n'est pas un plateau : c'est, par reel, la liste des seuls
 * nouveaux symboles, de longueur variable.
 */
type BookEventTumbleBoard = {
	index: number;
	type: 'tumbleBoard';
	explodingSymbols: Position[];
	newSymbols: RawSymbol[][];
};

/** Présentation du gain du spin. */
type BookEventSetWin = {
	index: number;
	type: 'setWin';
	amount: number;
	winLevel: number;
};

/**
 * Fin de résolution du spin : plus aucun cluster, plus aucune cascade.
 *
 * C'est le marqueur de « dead spin » — aucun event dédié n'est nécessaire.
 * Vérifié sur les books Stake réels : exactement un `setTotalWin` par `reveal`
 * (124/124 en base, 621/621 en bonus).
 */
type BookEventSetTotalWin = {
	index: number;
	type: 'setTotalWin';
	amount: number;
};

/** Fin du pari complet, tous spins confondus. */
type BookEventFinalWin = {
	index: number;
	type: 'finalWin';
	amount: number;
};

/**
 * Déclenchement du Bonus. Chez nous il ne vient pas de scatters mais de la 4e
 * connexion du Wild ; `positions` porte alors la case du Wild, à animer avant
 * la transition.
 *
 * Le Math le place APRÈS le `setTotalWin` du spin déclencheur : les cascades ne
 * sont donc jamais interrompues, et aucun état « bonus pending » n'a besoin
 * d'être transmis.
 */
type BookEventFreeSpinTrigger = {
	index: number;
	type: 'freeSpinTrigger';
	totalFs: number;
	positions: Position[];
};

/** Retrigger. `totalFs` est le NOUVEAU total, pas l'incrément. */
type BookEventFreeSpinRetrigger = {
	index: number;
	type: 'freeSpinRetrigger';
	totalFs: number;
	positions: Position[];
};

/** Compteur de Free Spins. */
type BookEventUpdateFreeSpin = {
	index: number;
	type: 'updateFreeSpin';
	amount: number;
	total: number;
};

/** Sortie du Bonus. */
type BookEventFreeSpinEnd = {
	index: number;
	type: 'freeSpinEnd';
	amount: number;
	winLevel: number;
};

// ─── PLANT VS WILD ───────────────────────────────────────────────────────────

/**
 * SPÉCIFIQUE PLANT VS WILD.
 *
 * Aucun bookEvent Stake n'exprime la translation d'un symbole persistant d'une
 * case vers une autre, ni un compteur attaché à lui : `winInfo` dit quelles
 * cases gagnent, `tumbleBoard` dit ce qui disparaît et ce qui retombe, aucun des
 * deux ne peut dire « ce Wild est maintenant là, et il a progressé ».
 *
 * Le Wild rejoint toujours une case du groupe gagnant. Sa propre case en faisant
 * partie, `to` peut être égal à `from` : c'est ainsi qu'on représente « il
 * progresse mais ne bouge pas ». Aucun cas particulier n'est nécessaire.
 *
 * `charge` est la valeur ABSOLUE après la connexion (1 → 4), jamais un
 * incrément : le frontend ne compte rien. `charge === 4` est l'état qui mènera
 * au Bonus en fin de spin. Le maximum vit dans `config.ts`, c'est une règle
 * fixe et non une donnée de spin.
 *
 * Seul le vrai Wild progresse : les Wild temporaires de Wild Split ne font
 * jamais monter ce compteur.
 *
 * Contrainte d'ordre CERTAINE, et seule certitude à ce stade :
 *
 *     connexion résolue
 *       → le Wild rejoint la destination fournie par le Book
 *       → nouveaux symboles / refill
 *
 * Le Wild n'est jamais détruit : s'il doit disparaître, il ne se déplace pas.
 *
 * La place exacte de cet event vis-à-vis de `updateGrid` n'est PAS tranchée —
 * elle le sera pendant l'étape Wild, quand l'animation existera. Ne pas la
 * figer ici.
 */
type BookEventWildMove = {
	index: number;
	type: 'wildMove';
	from: Position;
	to: Position;
	charge: number;
};

/**
 * SPÉCIFIQUE PLANT VS WILD.
 *
 * Stake n'a aucune notion de feature nommée déclenchée après résolution, et
 * aucun de ses events ne peut transporter un trajet ordonné ni désigner des
 * symboles temporaires.
 *
 * Un seul type pour les trois features : elles sont mutuellement exclusives et
 * occupent la même place dans la séquence — à l'intérieur du spin, une fois les
 * cascades épuisées, avant son `setTotalWin`.
 *
 * TODO_FUTURE_CONTRACT : Super Bonus, roue 0/BONUS/x10000, Max Win, Bonus Buy,
 * Spin Boosted, Wild préchargé, mise augmentée. Hors périmètre, aucun event.
 */
type BookEventWildFeature =
	| {
			index: number;
			type: 'wildFeature';
			feature: 'rage';
			/** Case où le Wild est recentré. Le renouvellement des autres cases
			 *  arrive ensuite par un `tumbleBoard` normal ; les multiplicateurs
			 *  persistent par simple absence d'un `updateGrid` de remise à zéro. */
			wildTo: Position;
	  }
	| {
			index: number;
			type: 'wildFeature';
			feature: 'wildSnake';
			from: Position;
			/** Trajet ordonné, `from` et `to` exclus. */
			path: Position[];
			to: Position;
			/** Symbole appliqué aux cases du trajet. Le frontend le recopie sur les
			 *  cases fournies — il ne choisit ni le trajet, ni le symbole, ni la
			 *  longueur. Le plateau résultant n'est pas retransmis. */
			symbol: SymbolName;
	  }
	| {
			index: number;
			type: 'wildFeature';
			feature: 'wildSplit';
			/** Les 3 Wild temporaires. Ils disparaissent ensuite comme n'importe
			 *  quel symbole, via le `explodingSymbols` d'un `tumbleBoard` : leur
			 *  caractère éphémère ne demande aucun champ. La règle « un seul Wild »
			 *  n'est pas touchée — le Wild permanent reste celui que `wildMove`
			 *  suit. */
			positions: Position[];
	  };

// ─────────────────────────────────────────────────────────────────────────────

export type BookEvent =
	// Stake
	| BookEventReveal
	| BookEventWinInfo
	| BookEventUpdateTumbleWin
	| BookEventUpdateGrid
	| BookEventTumbleBoard
	| BookEventSetWin
	| BookEventSetTotalWin
	| BookEventFinalWin
	| BookEventFreeSpinTrigger
	| BookEventFreeSpinRetrigger
	| BookEventUpdateFreeSpin
	| BookEventFreeSpinEnd
	// PLANT VS WILD
	| BookEventWildMove
	| BookEventWildFeature;

export type BookEventOfType<T extends BookEvent['type']> = Extract<BookEvent, { type: T }>;

export type BookEventContext = {
	bookEvents: BookEvent[];
};

export type Bet = {
	id: number;
	payoutMultiplier: number;
	state: BookEvent[];
};
