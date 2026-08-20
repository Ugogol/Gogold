---
paths:
  - "math/**/*.py"
  - "math/games/**"
---

# Math

Référence détaillée : `docs/MATH.md`, `docs/MECHANICS.md`, `docs/CONFIGURATION.md`.

## Stake Math SDK first

`math/src/` est le moteur générique Stake. Le traiter comme upstream.

Pour une nouvelle mécanique :

1. inspecter les primitives du Math SDK (`src/calculations/`, `src/executables/`,
   `src/config/`, `src/wins/`)
2. inspecter les sample games (`math/games/0_0_*`) et le `template`
3. réutiliser les primitives existantes
4. écrire du code spécifique au jeu dans `math/games/<game>/`
5. n'extraire une primitive commune qu'après un vrai besoin répété

## Ne pas modifier `math/src/`

Ne jamais y toucher pour personnaliser un jeu. Une modification upstream doit
être exceptionnelle, justifiée et documentée comme divergence.

Un jeu se configure par son `game_config.py` / `gamestate.py`, en héritant des
abstractions Stake (`Config`, `BetMode`, `Distribution`, `GameStateOverride`).
Ne pas créer une couche `GameConfig` Gogold parallèle.

## Fichiers générés

Ne jamais éditer à la main un artefact généré pour « corriger » un résultat :
corriger la source ou la configuration, puis régénérer.

Les publish files doivent respecter le format Stake actuel — `index.json`,
lookup table CSV, game logic `.jsonl.zst`, `payoutMultiplier` cohérent entre les
deux. Revalider contre la documentation officielle avant publication.

## Simulation

Le volume de simulation dépend des objectifs statistiques du jeu, pas d'un
nombre fixé dans une doc. Mesurer ce que le jeu exige réellement : RTP, hit rate,
volatilité, distribution des gains, fréquence des features, max win, comportement
par bet mode.

Les simulations lourdes sont une opération locale, jamais un contrôle de PR.

## Scénarios rares

Utiliser les **force mechanisms officiels** Stake (`library/forces/`,
`force_record_<mode>.json` : critère → bookIds). Ne pas créer un second système
de forces.

## Frontière

Aucune logique Math dans le frontend, aucun rendu dans le Math. Un event décrit
ce qui doit être affiché, jamais comment le calcul a été fait. Ne jamais exposer
une probabilité, un seed ou une information permettant de prédire un round.
