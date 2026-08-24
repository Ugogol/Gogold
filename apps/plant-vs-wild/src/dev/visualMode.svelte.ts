import type { RawSymbol } from '../game/types';

/**
 * État partagé du mode revue visuelle — DÉVELOPPEMENT UNIQUEMENT.
 *
 * La détection du mode vit dans `game/devVisualMode.ts` ; ce module ne contient
 * que ce dont l'outillage a besoin. Il n'est jamais importé statiquement par du
 * code de jeu : `Game.svelte` et `+layout.svelte` le chargent par import
 * dynamique gardé, donc il disparaît du bundle de production.
 */

/** Repères optionnels, pilotés par les cases à cocher du panneau. */
export const visualGuides = $state({
	gridBounds: false,
	cellBounds: false,
	centers: false,
	safeZones: false,
});

/**
 * Mesures publiées par `VisualOverlay`, qui vit dans l'arbre Pixi et connaît
 * donc le `scale` réellement appliqué. Le panneau ne recalcule rien : il affiche
 * ce que le rendu a utilisé.
 */
export const visualMetrics = $state({
	viewportWidth: 0,
	viewportHeight: 0,
	layoutType: '',
	designWidth: 0,
	designHeight: 0,
	scale: 1,
	gridWidth: 0,
	gridHeight: 0,
	cellSize: 0,
	symbolSize: 0,
	gap: 0,
	logoBand: 0,
	gameBarBand: 0,
	spinSize: 0,
});

/**
 * Plateau fixe de revue graphique (§16).
 *
 * Chaque High et le Wild apparaissent au moins deux fois, pour juger leur
 * lisibilité en contexte plutôt que sur un seul exemplaire. Aucun hasard, aucun
 * outcome, aucun calcul : c'est une planche de contact, pas un résultat.
 *
 * ⚠️ Sept lignes par colonne, pas cinq : `createReelForCascading` réassigne
 * TOUS les symboles du reel (5 visibles + 2 de padding hors champ). Une colonne
 * plus courte laisserait des symboles indéfinis et ferait planter le rendu.
 */
export const VISUAL_BOARD: RawSymbol[][] = (
	[
		['H1', 'L1', 'H3', 'L3', 'W', 'L2', 'H4'],
		['L2', 'H2', 'L4', 'H4', 'L1', 'H3', 'L3'],
		['H3', 'L3', 'W', 'L2', 'H1', 'L4', 'H2'],
		['L4', 'H4', 'L1', 'H2', 'L3', 'W', 'L1'],
		['W', 'L2', 'H1', 'L4', 'H3', 'L1', 'L2'],
	] as RawSymbol['name'][][]
).map((column) => column.map((name) => ({ name })));
