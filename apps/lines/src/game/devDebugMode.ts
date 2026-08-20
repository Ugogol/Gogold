/**
 * Mode debug local — DÉVELOPPEMENT UNIQUEMENT.
 *
 * Activé par `?debug=true` sur un serveur de dev. Il ne sert qu'à une chose :
 * signaler qu'aucune session RGS n'existe, donc qu'aucun appel réseau vers le
 * RGS ne doit être tenté.
 *
 * `import.meta.env.DEV` est replié à `false` par Vite en production : la
 * fonction y retourne constamment `false` et la branche appelante disparaît.
 *
 * Voir docs/DEBUG_PANEL.md.
 */
export const DEBUG_QUERY_KEY = 'debug';

export const isLocalDebugMode = () =>
	import.meta.env.DEV &&
	typeof window !== 'undefined' &&
	new URLSearchParams(window.location.search).get(DEBUG_QUERY_KEY) === 'true';
