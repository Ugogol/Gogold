/**
 * Assets runtime de PLANT VS WILD.
 *
 * Chemins et types suivent le pattern des sample games Stake
 * (`type` ∈ spine | sprite | sprites | spriteSheet | font | audio, cf.
 * `packages/pixi-svelte/src/lib/types.ts`).
 *
 * `symbols` est l'atlas TexturePacker livré par le graphiste. Ses frames sont
 * exposées dans la map globale des textures sous leur nom de frame exact :
 * `h1.png`, `l1.png`, `wild_01.png`… — voir SYMBOL_ASSET_MAP dans constants.ts.
 *
 * L'atlas porte les 16 frames : 8 symboles, les 4 états du Wild et les 4 du
 * Super Wild (ces derniers pas encore utilisés, le Bonus n'existe pas).
 *
 * Le nom de base `symbols` est celui du dossier ET celui que `meta.image`
 * référence. Ne pas le changer d'un côté sans l'autre : un `meta.image` qui ne
 * correspond pas au fichier fait échouer le chargement en silence.
 *
 * Deux fonds : `background` (1920×1080) pour les layouts couchés, `backgroundMobile`
 * (1080×1920) pour les layouts debout. Le choix se fait dans `Background.svelte`
 * via `isStacked()`.
 *
 * Quatre fonds : Base et Bonus, chacun en version couchée et debout. Le choix
 * se fait dans `Background.svelte` — `gameType` pour le mode, `isStacked()` pour
 * l'orientation.
 *
 * Rappel : `adapter-static` copie `static/` en bloc sans élaguer ce qu'`assets.ts`
 * ne déclare pas. Un fichier posé là mais non déclaré partirait dans le build
 * sans jamais être chargé.
 *
 * Aucun décor de plateau : le cadre autour de la grille a été abandonné
 * (étape 3). La grille est constituée des seules cases, dessinées en Graphics.
 * `board.psd` / `board.webp` sont conservés dans `source-assets/plant-vs-wild/`.
 *
 * Aucun son, aucune animation Spine à ce stade.
 */
export default {
	background: {
		type: 'sprite',
		src: new URL('../../assets/sprites/background/background.webp', import.meta.url).href,
		preload: true,
	},
	backgroundMobile: {
		type: 'sprite',
		src: new URL('../../assets/sprites/background/background-mobile.webp', import.meta.url).href,
		preload: true,
	},
	backgroundBonus: {
		type: 'sprite',
		src: new URL('../../assets/sprites/background/background-bonus.webp', import.meta.url).href,
		preload: true,
	},
	backgroundBonusMobile: {
		type: 'sprite',
		src: new URL('../../assets/sprites/background/background-bonus-mobile.webp', import.meta.url)
			.href,
		preload: true,
	},
	symbols: {
		type: 'sprites',
		src: new URL('../../assets/sprites/symbols/symbols.json', import.meta.url).href,
		preload: true,
	},
} as const;
