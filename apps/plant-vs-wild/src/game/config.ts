/**
 * Configuration de jeu — PLANT VS WILD.
 *
 * ⚠️ `gameID` ci-dessous est un IDENTIFIANT DE DÉVELOPPEMENT PROVISOIRE.
 * Ce n'est PAS l'identifiant Stake officiel : celui-ci sera attribué par Stake
 * (format `{provider}_{n}_{nom}`, cf. `math/src/config/config.py`) et devra
 * remplacer cette valeur ici, puis dans `math/games/<game_id>/`.
 *
 * Il est volontairement déclaré à UN SEUL endroit du frontend pour que le
 * renommage soit trivial. Ne pas le recopier ailleurs.
 *
 * À terme cette configuration doit refléter `config_fe_{game_id}.json` produit
 * par le Math SDK (voir docs/CONFIGURATION.md §5.1). Le math n'existe pas encore :
 * les valeurs ci-dessous sont provisoires et n'engagent aucun payout.
 */
export const DEV_GAME_ID = 'dev_plant_vs_wild';

/**
 * Nombre de connexions du Wild menant au Bonus.
 *
 * Règle de jeu fixe, donc configuration — jamais un champ de bookEvent. Le
 * frontend ne compte pas : il reçoit la charge absolue dans `wildMove` et se
 * sert de cette valeur uniquement pour savoir quand afficher l'état d'attente.
 */
export const WILD_MAX_CHARGE = 4;

export default {
	providerName: 'gogold',
	gameName: 'plant_vs_wild',
	gameID: DEV_GAME_ID,
	rtp: 0,
	numReels: 5,
	numRows: [5, 5, 5, 5, 5],
	betModes: {
		base: {
			cost: 1.0,
			feature: false,
			buyBonus: false,
			rtp: 0,
			max_win: 0,
		},
	},
	symbols: {
		H1: { paytable: null },
		H2: { paytable: null },
		H3: { paytable: null },
		H4: { paytable: null },
		L1: { paytable: null },
		L2: { paytable: null },
		L3: { paytable: null },
		L4: { paytable: null },
		W: { paytable: null, special_properties: ['wild'] },
	},
	paddingReels: {
		basegame: '',
		freegame: '',
	},
};
