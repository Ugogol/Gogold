/**
 * Lecture d'un book mocké — DÉVELOPPEMENT UNIQUEMENT.
 *
 * Activé par `?book=true` sur un serveur de dev. Il ne sert qu'à déclencher la
 * lecture d'un book écrit à la main, par le pipeline normal : aucun RGS, aucun
 * wallet, aucune session, aucun résultat fabriqué.
 *
 * `import.meta.env.DEV` est replié à `false` en production : la fonction y
 * retourne constamment `false` et les branches appelantes disparaissent, avec
 * les modules `src/dev/` et les fixtures qu'elles importaient.
 *
 * Même découpage que `devVisualMode.ts` et que `apps/lines/src/game/devDebugMode.ts`.
 */
export const BOOK_QUERY_KEY = 'book';

export const isLocalBookMode = () =>
	import.meta.env.DEV &&
	typeof window !== 'undefined' &&
	new URLSearchParams(window.location.search).get(BOOK_QUERY_KEY) === 'true';
