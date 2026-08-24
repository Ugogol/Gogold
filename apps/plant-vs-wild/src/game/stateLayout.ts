import { createLayout } from 'utils-layout';

import { MAIN_SIZES_MAP } from './constants';

/**
 * `mainSizesMap` définit l'espace de design du jeu par `layoutType`.
 * Les valeurs et la contrainte de ratio qui les lie aux espaces standard Stake
 * sont documentées dans `constants.ts`.
 */
export const { stateLayout, stateLayoutDerived } = createLayout({
	/**
	 * Ratio du sprite de fond, pas une préférence de cadrage.
	 *
	 * `createBackgroundLayout` s'en sert pour choisir l'axe sur lequel étirer le
	 * sprite : c'est ce qui produit un comportement « cover ». Une valeur qui ne
	 * correspond PAS à l'asset choisit le mauvais axe et laisse des bandes vides
	 * — c'était le cas avec 2039/1000, hérité de `apps/lines` alors que notre
	 * `background.webp` fait 1920×1080.
	 *
	 * À corriger si l'asset est réexporté dans un autre format.
	 */
	backgroundRatio: {
		normal: 1920 / 1080,
		portrait: 1920 / 1080,
	},
	mainSizesMap: MAIN_SIZES_MAP,
});
