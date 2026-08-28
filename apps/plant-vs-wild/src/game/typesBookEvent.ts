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
 *
 * ⚠️ Les `positions` de deux connexions PEUVENT se recouvrir : un Wild qui
 * complète deux groupes appartient aux deux, et compte dans les deux gains.
 * Le frontend dédoublonne avant d'animer — une case ne s'allume qu'une fois.
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

/**
 * Le plafond de gain est atteint.
 *
 * ⚠️ N'AJOUTE RIEN AU TOTAL. Relevé sur un vrai Book V4 (sim 93353), la
 * séquence est :
 *
 *     updateTumbleWin  amount 848880     le cumul avant écrêtage
 *     wincap           amount 1000000    le plafond, déjà écrêté
 *     updateGrid
 *     setTotalWin      amount 1000000    le total, même valeur
 *     …                                  le Bonus CONTINUE
 *     freeSpinEnd      amount 1000000
 *     finalWin         amount 1000000
 *
 * `setTotalWin` porte donc déjà le montant final : additionner `wincap`
 * doublerait le gain. `amount` est le total écrêté, pas un incrément.
 *
 * Le frontend ne décide JAMAIS que le plafond est atteint et n'écrête aucun
 * gain : le Math est seul juge, cet event est une annonce.
 *
 * Le Book ne s'arrête pas là — les Free Spins restants se jouent, tous leurs
 * `setTotalWin` valant le plafond.
 */
type BookEventWincap = {
	index: number;
	type: 'wincap';
	amount: number;
};

/**
 * Fin du PARI COMPLET, tous spins confondus — pas la fin d'un spin.
 *
 * ⚠️ CONTRAINTE POUR LE MATH — `finalWin` ne doit JAMAIS être émis entre deux
 * Free Spins. Son handler vide et masque la grille de multiplicateurs ; le
 * placer entre deux Free Spins détruirait la persistance que la mécanique
 * PLANT VS WILD exige.
 *
 * La fin d'un spin — Base comme Free Spin — se marque avec `setTotalWin`.
 * Ordre correct en Bonus :
 *
 *     … updateFreeSpin → reveal → … → setTotalWin      un Free Spin
 *     … updateFreeSpin → reveal → … → setTotalWin      le suivant
 *     freeSpinEnd                                      sortie du Bonus
 *     finalWin                                         fin du pari, une seule fois
 *
 * C'est la sémantique des books Stake réels, vérifiée sur le sample : 50
 * `finalWin` pour 124 `setTotalWin` en base, 50 pour 621 en bonus — soit un
 * `finalWin` par book et un `setTotalWin` par spin.
 */
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
 * incrément : le frontend ne compte rien.
 *
 * ⚠️ UNE SEULE CHARGE PAR CASCADE, donc au plus un `wildMove` entre deux
 * `tumbleBoard`. Un Wild qui complète deux groupes à la fois appartient aux
 * deux et rapporte dans les deux, mais ne progresse que d'un cran. `charge === 4` est l'état qui mènera
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
 * ⚠️ CONTRAINTE POUR LE MATH — AU PLUS UNE feature par spin. Décision validée :
 * pas d'enchaînement Snake → Split → Rage dans la même résolution. Plus lisible
 * pour le joueur, beaucoup plus simple à équilibrer, et cela évite l'explosion
 * combinatoire. Le frontend n'impose rien : c'est le Book qui doit s'y tenir.
 *
 * TODO_FUTURE_CONTRACT : Super Bonus, roue 0/BONUS/x10000, Max Win, Bonus Buy,
 * Spin Boosted, Wild préchargé, mise augmentée. Hors périmètre, aucun event.
 */
type BookEventWildFeature =
	| {
			index: number;
			type: 'wildFeature';
			feature: 'rage';
			/** Case actuelle du Wild. Fournie explicitement plutôt que cherchée sur
			 *  le plateau : le frontend ne localise rien, il transcrit. */
			wildFrom: Position;
			/** Case où le Wild est recentré. */
			wildTo: Position;
			/**
			 * Plateau complet après renouvellement, Wild compris et déjà à `wildTo`.
			 *
			 * ⚠️ Pourquoi un plateau et non un `tumbleBoard`, comme l'annonçait le
			 * contrat de l'étape 4 : le tumble fait TOMBER les rescapés. Renouveler
			 * toutes les cases sauf celle du Wild y ferait chuter le Wild jusqu'en
			 * bas de sa colonne — constaté à l'écran. Rage remplace SUR PLACE, ce
			 * que `tumbleBoard` ne sait pas exprimer.
			 *
			 * Les multiplicateurs ne sont pas touchés : Rage n'émet aucun
			 * `updateGrid`, donc la grille acquise reste intacte.
			 */
			board: RawSymbol[][];
	  }
	| {
			index: number;
			type: 'wildFeature';
			feature: 'wildSnake';
			/**
			 * Le Wild rampe orthogonalement de `from` vers `to` en suivant `path`,
			 * sans repasser sur une case déjà visitée. Le trajet, sa longueur et son
			 * symbole viennent tous du Math.
			 *
			 * ⚠️ Le Snake NE CHARGE PAS le Wild. Décision validée : c'est une feature
			 * de transformation, pas une connexion. Aucun `wildMove` n'accompagne
			 * donc cet event. Si le plateau qu'il produit forme ensuite un vrai
			 * cluster impliquant le Wild, CETTE connexion-là charge normalement, par
			 * le `wildMove` habituel.
			 */
			from: Position;
			/** Trajet ordonné, `from` et `to` exclus. */
			path: Position[];
			to: Position;
			/** Symbole appliqué aux cases du trajet. Le frontend le recopie sur les
			 *  cases fournies — il ne choisit ni le trajet, ni le symbole, ni la
			 *  longueur.
			 *
			 *  Les proportions 65 % Low / 35 % High et la rareté de H4 appartiennent
			 *  au Math : rien de tout cela n'existe côté frontend. */
			symbol: SymbolName;
			/**
			 * Plateau complet après le Snake — SOURCE DE VÉRITÉ FINALE.
			 *
			 * Le frontend anime la traversée puis applique ce plateau tel quel. Il
			 * ne reconstruit rien, ne déduit rien de `path` : le Math pourra donc
			 * changer la règle sans toucher au frontend.
			 *
			 * ⚠️ Ce que devient la case de départ, et si la case d'arrivée porte le
			 * Wild ou le symbole converti, dépend ENTIÈREMENT de ce plateau —
			 * décision validée : aucune règle n'est figée côté frontend, le Book
			 * tranche. Le game design pourra donc changer d'avis sans toucher au
			 * code, en fournissant simplement un autre plateau.
			 */
			board: RawSymbol[][];
	  }
	| {
			index: number;
			type: 'wildFeature';
			feature: 'wildSplit';
			/**
			 * Les 3 Wild temporaires, posés aux cases indiquées.
			 *
			 * Ils portent `temporary: true` sur le plateau : c'est ce qui les
			 * distingue du Wild permanent, seul à posséder une charge et seul que
			 * `wildMove` suit. La règle « un seul Wild standard » n'est donc pas
			 * touchée — quatre Wild peuvent coexister, un seul est le vrai.
			 *
			 * Leur consommation n'a pas de champ dédié : le Math les fait
			 * disparaître par le `explodingSymbols` d'un `tumbleBoard`, comme
			 * n'importe quel symbole. Le frontend ne détecte jamais qu'un
			 * temporaire « vient d'aider » une connexion.
			 */
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
	| BookEventWincap
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
