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
 * Le fichier s'appelle `symboles.json` (orthographe du livrable) : ne pas le
 * renommer sans regénérer l'atlas, `meta.image` y fait référence.
 *
 * Le décor `sprites/board/board.webp` reste sur le disque mais n'est plus
 * déclaré : plus aucun composant ne l'affiche, le préchargement serait du poids
 * mort. Le redéclarer quand un nouveau cadre arrivera.
 *
 * Aucun son, aucune animation Spine à ce stade.
 */
export default {
	background: {
		type: 'sprite',
		src: new URL('../../assets/sprites/background/background.webp', import.meta.url).href,
		preload: true,
	},
	symbols: {
		type: 'sprites',
		src: new URL('../../assets/sprites/symbols/symboles.json', import.meta.url).href,
		preload: true,
	},
} as const;
