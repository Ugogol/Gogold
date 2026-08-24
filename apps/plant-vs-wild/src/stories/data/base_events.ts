import type { BookEvent } from '../../game/typesBookEvent';

/**
 * Fixtures de développement — DÉTERMINISTES et fabriquées à la main.
 *
 * Elles ne viennent PAS du Math SDK : `math/games/<game_id>/` n'existe pas
 * encore. Elles servent uniquement à vérifier que le pipeline
 * book → bookEvent → handler → plateau fonctionne.
 *
 * Elles seront remplacées par de vrais books produits par le math
 * (voir docs/DEBUG_PANEL.md pour le workflow d'export).
 */
const reveal: BookEvent = {
	index: 0,
	type: 'reveal',
	board: [
		[{ name: 'H1' }, { name: 'L2' }, { name: 'L3' }, { name: 'L1' }, { name: 'H2' }],
		[{ name: 'L4' }, { name: 'H3' }, { name: 'L1' }, { name: 'L2' }, { name: 'L3' }],
		[{ name: 'L2' }, { name: 'L1' }, { name: 'W' }, { name: 'H4' }, { name: 'L4' }],
		[{ name: 'H2' }, { name: 'L3' }, { name: 'L4' }, { name: 'S' }, { name: 'L1' }],
		[{ name: 'L1' }, { name: 'L4' }, { name: 'H1' }, { name: 'L3' }, { name: 'L2' }],
	],
	paddingPositions: [0, 0, 0, 0, 0],
	gameType: 'basegame',
	anticipation: [0, 0, 0, 0, 0],
};

export default { reveal };
