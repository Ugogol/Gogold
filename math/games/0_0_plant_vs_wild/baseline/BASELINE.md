# PLANT VS WILD - baseline mesuree

> Ce document **mesure** le jeu tel qu'il est. Il ne valide rien et ne fixe aucun
> objectif. La paytable est `TEST_ONLY` et les parametres de balancing ne sont pas
> decides : les chiffres ci-dessous decrivent un point de depart, pas une cible.

Genere par `analyse_baseline.py` - 50000 wagers base, 10000 wagers bonus.
Reproductible : simulation_seeds = range(n), random.seed(0) — reproductible

## Base Game

| | |
| --- | --- |
| OBSERVED_RTP | **34.79** (3479 %) |
| hit rate | 16.88 % - 1 spin sur 5.92 |
| spins sans gain | 83.12 % |
| gain moyen | 34.79x |
| gain median (P50) | 0.0x |
| gain max observe | 5000.0x (plafond, atteint 1 fois sur 190) |
| cascades / spin | moyenne 0.3504, max 19 |

### Cascades (Base Game)

| cascades | spins |
| --- | --- |
| 0 | 41560 |
| 1 | 5477 |
| 2 | 1121 |
| 3 | 579 |
| 4+ | 1263 |

## Wild

Present dans **75.97 %** des spins de base (37916 au reveal, 68 arrives par un refill).

| connexions dans le spin | Base | Free Spins |
| --- | --- | --- |
| 0 | 42522 | 86550 |
| 1 | 4793 | 14511 |
| 2 | 943 | 4080 |
| 3 | 544 | 1283 |
| 4+ | 1198 | 1606 |

## Multipliers

Nombre de fois qu'une case atteint chaque palier.

| palier | Base Game | Free Spins (mode bonus) |
| --- | --- | --- |
| x2 | 56658 | 91877 |
| x4 | 15033 | 47258 |
| x8 | 7506 | 25231 |
| x16 | 4668 | 13976 |
| x32 | 2898 | 8295 |
| x64 | 1506 | 5268 |
| x128 | 1063 | 3385 |
| x256 | 820 | 2302 |
| x512 | 615 | 1511 |
| x1024 | 485 | 1011 |
| x2048 | 307 | 661 |
| x4096 | 109 | 413 |

Part du payout venant des multiplicateurs de case : **99.11 %** en mode base, **98.90 %** en mode bonus.

## Bonus

| | mode base | mode bonus |
| --- | --- | --- |
| declenchement | 1 wager sur 41.7 (2.40 %) | achete |
| Free Spins moyens | 10.576 | 10.803 |
| gain moyen | 927.638x | 244.897x |
| gain median | 85.6x | 8.4x |
| gain max | 5000.0x | 5000.0x |
| retriggers / Bonus | 0.1152 | 0.1606 |

Retriggers (mode bonus) : 8558 Bonus sans, 1285 avec 1, 157 avec 2 ou plus.

## Features

Frequence observee en simulation normale : **0**. `DEAD_SPIN_FEATURE_WEIGHTS` vaut
`none` seul - aucune frequence n'est decidee, donc aucune feature ne part.

Les valeurs ci-dessous viennent d'une **sonde** (3000 wagers) qui force
une feature sur chaque dead spin eligible. Elles disent ce que rapporte une feature
*quand elle part*, pas a quelle frequence elle devrait partir.

Dead spins eligibles : **74.56 %** des Free Spins.

| feature | activations | gain moyen apres | median | max | sans gain |
| --- | --- | --- | --- | --- | --- |
| Rage | 8421 | 418.988x | 4.2x | 9653.2x | 42.68 % |
| Wild Snake | 8566 | 686.48x | 60.0x | 9349.6x | 0.00 % |
| Wild Split | 8608 | 625.009x | 32.5x | 9747.4x | 13.99 % |

Wild Snake - trajet moyen 3.98 cases (max 5), Low 49.40 % / High 50.60 %, dont H4 12.18 %.
Ces proportions refletent les poids uniformes actuels, pas un choix de design.

## Distribution des gains

| bucket | mode base | mode bonus |
| --- | --- | --- |
| 0x | 83.12 % | 7.49 % |
| >0x-1x | 10.08 % | 75.26 % |
| 1x-2x | 0.42 % | 5.13 % |
| 2x-5x | 1.50 % | 4.35 % |
| 5x-10x | 1.37 % | 2.03 % |
| 10x-25x | 0.82 % | 1.82 % |
| 25x-50x | 0.42 % | 3.92 % |
| 50x-100x | 0.52 % | 0.00 % |
| 100x-500x | 0.85 % | 0.00 % |
| 500x+ | 0.90 % | 0.00 % |

## Indicateurs de volatilite

Mesures du SDK (`utils.rgs_verification`), pas un score maison.

| | mode base | mode bonus |
| --- | --- | --- |
| ecart-type | 379.161 | 936.2296 |
| asymetrie | 12.4829 | 4463844.74 |
| kurtosis excedentaire | 157.7186 | 2200722495.2603 |
| P50 | 0.0x | 0.092x |
| P90 | 0.4x | 2.914x |
| P95 | 5.0x | 13.583x |
| P99 | 370.2x | 50.0x |
| P99.9 | 5000.0x | 50.0x |

## Contribution au payout

| mecanique | mode base | mode bonus |
| --- | --- | --- |
| Base Game | 46.51 % | 7.75 % |
| Free Spins | 53.49 % | 92.25 % |
| Multiplicateurs de case | 99.11 % | 98.90 % |
| Wild | NON_ISOLABLE | NON_ISOLABLE |
| Features | 0 (desactivees) | 0 (desactivees) |

> La part du Wild n'est pas isolable : il cree des connexions qui n'existeraient pas
> sans lui et en agrandit d'autres. La separer demanderait de rejouer chaque spin
> sans Wild - ce serait un autre jeu, pas une mesure.

