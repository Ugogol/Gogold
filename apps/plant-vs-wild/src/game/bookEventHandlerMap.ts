import _ from 'lodash';

import { stateBet } from 'state-shared';
import type { BookEventHandlerMap } from 'utils-book';

import { eventEmitter } from './eventEmitter';
import { stateGame, stateGameDerived } from './stateGame.svelte';
import type { BookEvent, BookEventOfType, BookEventContext } from './typesBookEvent';
import type { Position } from './types';

/**
 * Traduction bookEvent → emitterEvents.
 *
 * Aucun handler ne décide quoi que ce soit : les positions gagnantes, les
 * positions qui explosent et les symboles qui arrivent viennent tous du book.
 * Le frontend ne cherche aucun cluster.
 *
 * Les events du contrat encore sans handler (`wildFeature`, `freeSpin*`…)
 * arriveront avec leurs mécaniques. Le map Stake
 * n'est pas exhaustif : un event sans handler ne casse rien.
 */
/**
 * Contrôle de COHÉRENCE DE FIXTURE, développement uniquement.
 *
 * La destination du Wild doit faire partie des cases libérées par la connexion
 * qui vient d'être résolue. Ce n'est pas un moteur de règles : rien n'est
 * décidé, calculé ni corrigé ici — on signale une fixture ou un payload
 * incohérent, et le playback continue.
 *
 * Vite replie `import.meta.env.DEV` à `false` en production : la fonction y
 * devient un corps vide que Rollup élimine.
 */
const assertWildDestinationIsReleased = (
	bookEvent: BookEventOfType<'wildMove'>,
	bookEvents: BookEvent[],
) => {
	if (!import.meta.env.DEV) return;

	const previous = bookEvents.slice(0, bookEvents.indexOf(bookEvent));
	const lastWinInfo = _.findLast(previous, (event) => event.type === 'winInfo') as
		| BookEventOfType<'winInfo'>
		| undefined;

	if (!lastWinInfo) return;

	const released = _.flatten(lastWinInfo.wins.map((win) => win.positions));
	const isReleased = released.some(
		(position) => position.reel === bookEvent.to.reel && position.row === bookEvent.to.row,
	);

	if (!isReleased) {
		console.error(
			'wildMove : destination hors des cases libérées par la connexion.',
			{ to: bookEvent.to, released },
		);
	}
};

/**
 * Mise en évidence de cases, reprise de `apps/cluster`.
 *
 * Les cases sont DÉDOUBLONNÉES avant d'être animées. Un `winInfo` peut citer la
 * même case dans deux connexions : le Wild qui complète deux groupes à la fois
 * appartient légitimement aux deux, et les books Math en produisent. Sans ce
 * filtre, deux attentes viseraient le même symbole, la seconde écraserait le
 * `oncomplete` de la première, et le playback se figerait — constaté.
 *
 * Ce n'est pas une correction de Book : aucune connexion, aucun montant, aucune
 * position n'est modifié. Une case ne peut simplement pas s'allumer deux fois.
 */
const animateSymbols = async ({ positions }: { positions: Position[] }) => {
	eventEmitter.broadcast({ type: 'boardShow' });
	await eventEmitter.broadcastAsync({
		type: 'boardWithAnimateSymbols',
		symbolPositions: _.uniqWith(positions, _.isEqual),
	});
};

export const bookEventHandlerMap: BookEventHandlerMap<BookEvent, BookEventContext> = {
	reveal: async (bookEvent: BookEventOfType<'reveal'>) => {
		stateGame.gameType = bookEvent.gameType;
		// Pas de reels de padding à ce stade : le plateau du book est affiché tel quel.
		await stateGameDerived.enhancedBoard.spin({ revealEvent: bookEvent });
	},

	/** Met en évidence les cases désignées par le Math. Il ne les cherche pas. */
	winInfo: async (bookEvent: BookEventOfType<'winInfo'>) => {
		await animateSymbols({ positions: _.flatten(bookEvent.wins.map((win) => win.positions)) });
	},

	/**
	 * Décomposition en étapes séquentielles, reprise de `apps/cluster` :
	 * le plateau normal se cache, le plateau de tumble prend le relais, explose,
	 * retire, fait chuter, puis reverse le résultat au plateau normal.
	 */
	tumbleBoard: async (bookEvent: BookEventOfType<'tumbleBoard'>) => {
		eventEmitter.broadcast({ type: 'boardHide' });
		eventEmitter.broadcast({ type: 'tumbleBoardShow' });
		eventEmitter.broadcast({ type: 'tumbleBoardInit', addingBoard: bookEvent.newSymbols });
		await eventEmitter.broadcastAsync({
			type: 'tumbleBoardExplode',
			explodingPositions: bookEvent.explodingSymbols,
		});
		eventEmitter.broadcast({ type: 'tumbleBoardRemoveExploded' });
		await eventEmitter.broadcastAsync({ type: 'tumbleBoardSlideDown' });
		eventEmitter.broadcast({
			type: 'boardSettle',
			board: stateGameDerived
				.tumbleBoardCombined()
				.map((tumbleReel) => tumbleReel.map((tumbleSymbol) => tumbleSymbol.rawSymbol)),
		});
		eventEmitter.broadcast({ type: 'tumbleBoardReset' });
		eventEmitter.broadcast({ type: 'tumbleBoardHide' });
		eventEmitter.broadcast({ type: 'boardShow' });
	},

	/**
	 * Déplacement du Wild vers la case que le Book lui désigne, et montée de sa
	 * charge. Le handler ne choisit ni la destination ni la charge : il les
	 * transmet.
	 *
	 * Placé entre la résolution de la connexion et le refill — la seule contrainte
	 * d'ordre certaine à ce stade (voir typesBookEvent.ts).
	 */
	wildMove: async (bookEvent: BookEventOfType<'wildMove'>, { bookEvents }: BookEventContext) => {
		assertWildDestinationIsReleased(bookEvent, bookEvents);

		await eventEmitter.broadcastAsync({
			type: 'boardWildMove',
			from: bookEvent.from,
			to: bookEvent.to,
			charge: bookEvent.charge,
		});
	},

	/**
	 * État COMPLET de la grille de multiplicateurs, fourni par le Book.
	 *
	 * Le frontend ne calcule aucune progression : il affiche ce qu'il reçoit. La
	 * remise à zéro du Base Game n'est pas une décision d'ici non plus — c'est un
	 * `updateGrid` rempli de zéros que le Math envoie après le `reveal`.
	 */
	updateGrid: async (bookEvent: BookEventOfType<'updateGrid'>) => {
		eventEmitter.broadcast({ type: 'multiplierGridShow' });
		eventEmitter.broadcast({ type: 'multiplierGridUpdate', grid: bookEvent.gridMultipliers });
	},

	/**
	 * Déclenchement du Bonus.
	 *
	 * Le Math le place APRÈS la résolution complète du spin : le frontend
	 * n'interrompt donc jamais une cascade, c'est structurel. `positions` est
	 * animé avant l'annonce — chez nous la case du Wild, chez Stake les scatters.
	 *
	 * `gameType` est l'unique source du mode. Aucun état Bonus parallèle.
	 *
	 * La grille de multiplicateurs n'est PAS touchée : elle est donc héritée du
	 * spin déclencheur, ce que la mécanique PLANT VS WILD demande.
	 */
	freeSpinTrigger: async (bookEvent: BookEventOfType<'freeSpinTrigger'>) => {
		await animateSymbols({ positions: bookEvent.positions });

		eventEmitter.broadcast({ type: 'freeSpinIntroShow' });
		await eventEmitter.broadcastAsync({
			type: 'freeSpinIntroUpdate',
			totalFreeSpins: bookEvent.totalFs,
		});
		stateGame.gameType = 'freegame';
		eventEmitter.broadcast({ type: 'freeSpinIntroHide' });

		eventEmitter.broadcast({ type: 'freeSpinCounterShow' });
		eventEmitter.broadcast({
			type: 'freeSpinCounterUpdate',
			current: 0,
			total: bookEvent.totalFs,
		});
	},

	/**
	 * Retrigger. `totalFs` est le NOUVEAU total, pas l'incrément : le frontend
	 * n'additionne rien. Comme le trigger, il arrive après la fin des cascades.
	 */
	freeSpinRetrigger: async (bookEvent: BookEventOfType<'freeSpinRetrigger'>) => {
		await animateSymbols({ positions: bookEvent.positions });

		eventEmitter.broadcast({ type: 'freeSpinIntroShow' });
		await eventEmitter.broadcastAsync({
			type: 'freeSpinIntroUpdate',
			totalFreeSpins: bookEvent.totalFs,
		});
		eventEmitter.broadcast({ type: 'freeSpinIntroHide' });

		eventEmitter.broadcast({ type: 'freeSpinCounterUpdate', total: bookEvent.totalFs });
	},

	/** Compteur. Les deux valeurs viennent du Book, rien n'est incrémenté ici. */
	updateFreeSpin: async (bookEvent: BookEventOfType<'updateFreeSpin'>) => {
		eventEmitter.broadcast({ type: 'freeSpinCounterShow' });
		eventEmitter.broadcast({
			type: 'freeSpinCounterUpdate',
			current: bookEvent.amount,
			total: bookEvent.total,
		});
	},

	/**
	 * Sortie du Bonus : retour au mode Base, compteur masqué. Le montant est une
	 * donnée MOCK du book, aucun calcul.
	 */
	freeSpinEnd: async (bookEvent: BookEventOfType<'freeSpinEnd'>) => {
		eventEmitter.broadcast({ type: 'freeSpinOutroShow' });
		await eventEmitter.broadcastAsync({
			type: 'freeSpinOutroCountUp',
			amount: bookEvent.amount,
		});
		stateGame.gameType = 'basegame';
		eventEmitter.broadcast({ type: 'freeSpinOutroHide' });
		eventEmitter.broadcast({ type: 'freeSpinCounterHide' });
	},

	/** Fin du pari : la grille est vidée et masquée, comme dans `apps/cluster`. */
	finalWin: async () => {
		eventEmitter.broadcast({ type: 'multiplierGridClear' });
		eventEmitter.broadcast({ type: 'multiplierGridHide' });
	},

	/**
	 * Features Bonus — Rage, Wild Snake et Wild Split.
	 *
	 * Le handler ne décide rien : ni quelle feature, ni quelles cases, ni le
	 * nouveau plateau. Il transcrit ce que le Book donne et laisse la résolution
	 * normale reprendre ensuite. Aucun mode de jeu n'est créé : `gameType` reste
	 * `freegame` pendant toute la séquence.
	 *
	 * Les trois features sont traitées : Rage, Wild Snake, Wild Split.
	 */
	wildFeature: async (bookEvent: BookEventOfType<'wildFeature'>) => {
		if (bookEvent.feature === 'rage') {
			await eventEmitter.broadcastAsync({
				type: 'featureAnnounce',
				title: 'RAGE',
				subtitle: 'LE WILD SE RECENTRE',
			});

			// La charge n'est PAS une donnée de Rage : le Wild se déplace sans
			// gagner de connexion. On rejoue donc celle qu'il porte déjà — la lire
			// n'est pas une décision, c'est de l'affichage.
			const wild =
				stateGame.board[bookEvent.wildFrom.reel]?.reelState.symbols[bookEvent.wildFrom.row];

			await eventEmitter.broadcastAsync({
				type: 'boardWildMove',
				from: bookEvent.wildFrom,
				to: bookEvent.wildTo,
				charge: wild?.rawSymbol.charge ?? 0,
			});
			// Renouvellement SUR PLACE, via l'event Stake `boardSettle` déjà utilisé
			// par la cascade. Pas de `tumbleBoard` : sa physique de chute
			// déplacerait le Wild qu'on vient de recentrer.
			eventEmitter.broadcast({ type: 'boardSettle', board: bookEvent.board });
			// La grille de multiplicateurs n'est pas touchée : Rage ne la modifie
			// jamais.
			return;
		}

		if (bookEvent.feature === 'wildSnake') {
			await eventEmitter.broadcastAsync({
				type: 'featureAnnounce',
				title: 'WILD SNAKE',
				subtitle: `LE WILD RAMPE VERS ${bookEvent.symbol}`,
			});
			await eventEmitter.broadcastAsync({
				type: 'boardWildSnake',
				from: bookEvent.from,
				path: bookEvent.path,
				to: bookEvent.to,
				symbol: bookEvent.symbol,
			});
			// Plateau final fourni par le Book : source de vérité. Le frontend ne
			// reconstruit rien depuis `path`. Les multiplicateurs ne sont pas
			// touchés — Snake n'émet aucun `updateGrid`.
			eventEmitter.broadcast({ type: 'boardSettle', board: bookEvent.board });
			return;
		}

		if (bookEvent.feature === 'wildSplit') {
			await eventEmitter.broadcastAsync({
				type: 'featureAnnounce',
				title: 'WILD SPLIT',
				subtitle: `${bookEvent.positions.length} WILD TEMPORAIRES`,
			});
			await eventEmitter.broadcastAsync({
				type: 'boardWildSplit',
				positions: bookEvent.positions,
			});
		}
	},

	/**
	 * Montant courant de la cascade en cours.
	 *
	 * Les trois events de gain écrivent le même état partagé, chacun à son
	 * échelle : la cascade, puis le spin, puis le pari. Aucun n'additionne quoi
	 * que ce soit — chaque montant vient du book.
	 *
	 * Rien ne LIT encore cet état : l'affichage du gain (bandeau, compteur,
	 * niveaux de win) viendra avec sa propre étape. Le handler existe pour que
	 * la séquence Stake complète soit consommée plutôt que signalée manquante.
	 */
	updateTumbleWin: async (bookEvent: BookEventOfType<'updateTumbleWin'>) => {
		stateBet.winBookEventAmount = bookEvent.amount;
	},

	/** Gain du spin, cascades comprises. Même remarque que ci-dessus. */
	setWin: async (bookEvent: BookEventOfType<'setWin'>) => {
		stateBet.winBookEventAmount = bookEvent.amount;
	},

	/** Fin de résolution du spin. Le montant est une donnée du book, pas un calcul. */
	setTotalWin: async (bookEvent: BookEventOfType<'setTotalWin'>) => {
		stateBet.winBookEventAmount = bookEvent.amount;
	},
};
