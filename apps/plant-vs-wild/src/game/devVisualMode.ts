/**
 * Mode revue visuelle — DÉVELOPPEMENT UNIQUEMENT.
 *
 * Activé par `?visual=true` sur un serveur de dev. Il n'existe que pour juger la
 * composition à l'écran : bandes réservées, repères de grille, mesures rendues.
 *
 * Il ne touche ni au RGS, ni au wallet, ni au math, ni à la machine XState.
 * Aucun résultat n'est fabriqué : le mode remplace seulement le plateau statique
 * par un autre plateau statique, plus représentatif pour l'œil.
 *
 * `import.meta.env.DEV` est replié à `false` par Vite en production : la fonction
 * y retourne constamment `false` et les branches appelantes disparaissent, avec
 * les modules `src/dev/` qu'elles importaient.
 *
 * Même découpage que `apps/lines/src/game/devDebugMode.ts` : la détection vit
 * dans `game/`, l'outillage dans `dev/`. Voir docs/DEBUG_PANEL.md.
 */
export const VISUAL_QUERY_KEY = 'visual';

export const isLocalVisualMode = () =>
	import.meta.env.DEV &&
	typeof window !== 'undefined' &&
	new URLSearchParams(window.location.search).get(VISUAL_QUERY_KEY) === 'true';
