# PLANT VS WILD - baseline mesuree

> Ce document **mesure** le jeu tel qu'il est. Il ne valide rien et ne fixe aucun
> objectif. La paytable est `TEST_ONLY` et les parametres de balancing ne sont pas
> decides : les chiffres ci-dessous decrivent un point de depart, pas une cible.

Genere par `analyse_baseline.py` - 50000 wagers base, 10000 wagers bonus.
Reproductible : simulation_seeds = range(n), random.seed(0) — reproductible

## Base Game

| | |
| --- | --- |
| OBSERVED_RTP | **6.98** (698 %) |
| hit rate | 14.03 % - 1 spin sur 7.13 |
| spins sans gain | 85.97 % |
| gain moyen | 6.98x |
| gain median (P50) | 0.0x |
| gain max observe | 5000.0x (plafond, atteint 1 fois sur 1316) |
| cascades / spin | moyenne 0.2985, max 26 |

### Cascades (Base Game)

| cascades | spins |
| --- | --- |
| 0 | 42987 |
| 1 | 2293 |
| 2 | 3084 |
| 3 | 833 |
| 4+ | 803 |

## Wild

Present dans **55.58 %** des spins de base (27781 au reveal, 7 arrives par un refill).

| connexions dans le spin | Base | Free Spins |
| --- | --- | --- |
| 0 | 43764 | 86371 |
| 1 | 1886 | 12987 |
| 2 | 2898 | 6507 |
| 3 | 715 | 2415 |
| 4+ | 737 | 2070 |

## Multipliers

Nombre de fois qu'une case atteint chaque palier.

| palier | Base Game | Free Spins (mode bonus) |
| --- | --- | --- |
| x2 | 51297 | 98006 |
| x4 | 17568 | 54055 |
| x8 | 4059 | 30480 |
| x16 | 1427 | 16838 |
| x32 | 560 | 9578 |
| x64 | 281 | 5628 |
| x128 | 183 | 3308 |
| x256 | 135 | 1936 |
| x512 | 106 | 1175 |
| x1024 | 81 | 729 |
| x2048 | 61 | 440 |
| x4096 | 49 | 261 |

Part du payout venant des multiplicateurs de case : **98.83 %** en mode base, **98.78 %** en mode bonus.

## Bonus

| | mode base | mode bonus |
| --- | --- | --- |
| declenchement | 1 wager sur 67.8 (1.47 %) | achete |
| Free Spins moyens | 10.997 | 11.035 |
| gain moyen | 343.407x | 104.448x |
| gain median | 29.8x | 6.6x |
| gain max | 5000.0x | 5000.0x |
| retriggers / Bonus | 0.1995 | 0.207 |

Retriggers (mode bonus) : 8259 Bonus sans, 1449 avec 1, 292 avec 2 ou plus.

## Features

Frequence observee en simulation normale : **0**. `DEAD_SPIN_FEATURE_WEIGHTS` vaut
`none` seul - aucune frequence n'est decidee, donc aucune feature ne part.

Les valeurs ci-dessous viennent d'une **sonde** (2000 wagers) qui force
une feature sur chaque dead spin eligible. Elles disent ce que rapporte une feature
*quand elle part*, pas a quelle frequence elle devrait partir.

Dead spins eligibles : **74.34 %** des Free Spins.

| feature | activations | gain moyen apres | median | max | sans gain |
| --- | --- | --- | --- | --- | --- |
| Rage | 5880 | 292.326x | 2.4x | 8223.4x | 41.58 % |
| Wild Snake | 5887 | 429.916x | 26.6x | 7432.8x | 0.00 % |
| Wild Split | 5971 | 425.612x | 16.4x | 7603.8x | 13.48 % |

Wild Snake - trajet moyen 3.979 cases (max 5), Low 50.55 % / High 49.45 %, dont H4 12.66 %.
Ces proportions refletent les poids uniformes actuels, pas un choix de design.

## Distribution des gains

| bucket | mode base | mode bonus |
| --- | --- | --- |
| 0x | 85.97 % | 5.96 % |
| >0x-1x | 5.67 % | 83.97 % |
| 1x-2x | 3.90 % | 3.98 % |
| 2x-5x | 2.20 % | 2.63 % |
| 5x-10x | 0.77 % | 1.32 % |
| 10x-25x | 0.46 % | 0.84 % |
| 25x-50x | 0.28 % | 1.30 % |
| 50x-100x | 0.27 % | 0.00 % |
| 100x-500x | 0.27 % | 0.00 % |
| 500x+ | 0.21 % | 0.00 % |

## Indicateurs de volatilite

Mesures du SDK (`utils.rgs_verification`), pas un score maison.

| | mode base | mode bonus |
| --- | --- | --- |
| ecart-type | 152.7557 | 542.32 |
| asymetrie | 29.6504 | 7780069.6506 |
| kurtosis excedentaire | 926.1901 | 6633020594.1065 |
| P50 | 0.0x | 0.069x |
| P90 | 0.5x | 1.014x |
| P95 | 1.9x | 2.742x |
| P99 | 26.5x | 41.082x |
| P99.9 | 2225.0x | 50.0x |

## Contribution au payout

| mecanique | mode base | mode bonus |
| --- | --- | --- |
| Base Game | 36.53 % | 4.17 % |
| Free Spins | 63.47 % | 95.83 % |
| Multiplicateurs de case | 98.83 % | 98.78 % |
| Wild | NON_ISOLABLE | NON_ISOLABLE |
| Features | 0 (desactivees) | 0 (desactivees) |

> La part du Wild n'est pas isolable : il cree des connexions qui n'existeraient pas
> sans lui et en agrandit d'autres. La separer demanderait de rejouer chaque spin
> sans Wild - ce serait un autre jeu, pas une mesure.

