# Gogold — Audit des mécaniques réutilisables Stake Engine

Ce document répond à une seule question, mécanique par mécanique :

```text
QUELLE MÉCANIQUE → STAKE LA FOURNIT-IL DÉJÀ ? → À QUEL NIVEAU ?
                 → OÙ EST SON IMPLÉMENTATION ? → QUEL SAMPLE LA DÉMONTRE ?
                 → QUE RÉUTILISER ? → QUE CRÉER ÉVENTUELLEMENT ?
```

**C'est un audit. Aucune mécanique n'est développée ici.**

## 1. Objet du document

Un développeur Gogold doit pouvoir ouvrir ce document et conclure :

> « Pour faire un cascade, je pars de `Tumble` et de `Executables` côté math, et
> je ne réimplémente pas le système depuis zéro. »

L'objectif initial de A7 était de construire une bibliothèque de mécaniques
Gogold. Cet objectif est **suspendu** tant que l'audit ci-dessous n'a pas montré
qu'il reste quelque chose à construire.

## 2. Règle centrale : Stake d'abord — **[CONVENTION GOGOLD]**

> Avant de créer une mécanique réutilisable Gogold, vérifier si Stake Engine
> fournit déjà son implémentation, une primitive adaptée, un executable
> réutilisable ou un sample officiel dont nous devons partir.

**Règle de composition — [CONVENTION GOGOLD]**

> Préférer composer les primitives Stake existantes plutôt que créer une
> abstraction Gogold supplémentaire.

```text
✓  Tumble (Stake) + structure free game (Stake) + un bookEvent réellement
   nécessaire

✗  GogoldMegaCascadeFreeSpinEngine
```

## 3. Étiquettes d'autorité

Mêmes étiquettes que `ASSETS.md` et `CONFIGURATION.md`, plus une, propre à A7.

| Étiquette | Signification |
| --- | --- |
| **[CONTRAT STAKE]** | Imposé par le contrat Stake / RGS / SDK. Non négociable. |
| **[PRIMITIVE STAKE]** | Classe, fonction ou executable **générique** réellement fourni par le SDK et conçu pour être réutilisé. |
| **[PATTERN SAMPLE]** | Implémentation présente dans un sample officiel, **non exposée comme abstraction universelle**. |
| **[CONVENTION GOGOLD]** | Décision interne Gogold. |

⚠️ Ne jamais présenter un sample comme une API générique si le SDK ne l'a pas
conçu ainsi. C'est la distinction la plus importante de ce document.

**Sources** : `github.com/StakeEngine/math-sdk` et `web-sdk` (code source).
`stakeengine.github.io` et `stake-engine.com/docs` sont restés inaccessibles
(404 / SPA) pendant cet audit — limitation de session, pas conclusion générale.

## 4. Briques réutilisables du Math SDK — **[PRIMITIVE STAKE]**

Structure réelle de `math-sdk/src/` :

```text
src/
├── calculations/   board.py  symbol.py  lines.py  ways.py  cluster.py
│                   scatter.py  tumble.py  statistics.py
├── config/         config.py  betmode.py  distributions.py  constants.py
│                   optimization_paramaters.py  output_filenames.py  paths.py
├── events/         events.py  event_constants.py
├── executables/    executables.py
├── state/          state.py  books.py  run_sims.py  state_conditions.py
└── wins/           win_manager.py  multiplier_strategy.py
```

### 4.1 — `calculations/` : les types de win sont déjà implémentés

`lines.py`, `ways.py`, `cluster.py`, `scatter.py` existent comme **modules de
calcul génériques**. `board.py` et `symbol.py` fournissent la grille et les
symboles ; `tumble.py` la cascade.

### 4.2 — `Tumble` (`calculations/tumble.py`)

```python
class Tumble(Board):
    def tumble_board(self)          # retire les symboles marqués `explode`,
                                    # décale la reelstrip, insère les nouveaux
    def set_end_tumble_event(self)  # émet l'event de win après cascade
```

**Ce que `Tumble` fait** : retire les symboles marqués, recule la position de
reel, insère les nouveaux symboles depuis la reelstrip, suit
`new_symbols_from_tumble`, gère le padding, valide la taille du board.

**Ce que `Tumble` ne fait pas** : il ne calcule aucun gain, ne décide **pas**
quels symboles explosent (ils arrivent déjà marqués), ne gère ni animation ni
rendu. La règle « qu'est-ce qui explose » reste spécifique au jeu.

### 4.3 — `Executables` (`executables/executables.py`)

Groupe d'actions de jeu réutilisables, **surchargeables** par jeu. Méthodes
confirmées :

| Méthode | Rôle |
| --- | --- |
| `tumble_game_board()` | retire les symboles gagnants, remplace le board, émet l'event |
| `emit_tumble_win_events()` | transmet win/board après tumble, évalue le wincap |
| `evaluate_wincap()` | stoppe les spins au plafond de gain |
| `check_fs_condition()` | valide le compte de scatters pour le trigger |
| `check_freespin_entry()` | vérifie que le betmode autorise l'entrée en freespin |
| `run_freespin_from_base()` | lance le freespin, journalise les scatters |
| `update_freespin_amount()` | fixe le nombre initial de free spins, émet le trigger |
| `update_fs_retrigger_amt()` | incrémente le total sur retrigger |
| `update_freespin()` | prépare le reveal suivant, remet le compteur de win à zéro |
| `end_freespin()` | transmet les totaux du freegame |
| `evaluate_finalwin()` | combine base + freespin, applique le multiplicateur |
| `update_global_mult()` | incrémente le multiplicateur global, émet l'event |

> **Le framework de free spins existe déjà.** Il ne reste au jeu que ses règles
> propres (conditions, quantités, reelsets).

### 4.4 — `wins/`

**`WinManager`** (`win_manager.py`) — `running_bet_win`, `basegame_wins`,
`freegame_wins`, `cumulative_base_wins`, `cumulative_free_wins`, `spin_win`,
`tumble_win`, et l'application du plafond via
`min(max_allowed_win, basegame_wins)`.

**`multiplier_strategy.py`** — fonction `apply_mult(board, strategy, …)` avec
**trois stratégies distinctes** :

```text
"global"    → apply_global_mult()        win × multiplicateur global
"symbol"    → apply_added_symbol_mult()  somme des multiplicateurs des positions gagnantes
"combined"  → apply_combined_mult()      symbol puis global
```

⚠️ Stake distingue déjà ces trois cas. **Ne jamais les fusionner** dans un unique
`GGMultiplier` : ce serait une régression, pas une abstraction.

### 4.5 — `config/`

`Config`, `BetMode`, `distributions.py`, `optimization_paramaters.py`. Détaillés
dans `docs/CONFIGURATION.md` §3.

### 4.6 — `events/`

`events.py` et `event_constants.py` : le catalogue d'events génériques (§14).

## 5. Inventaire des sample games math

Jeux présents dans `math-sdk/games/` : `0_0_lines`, `0_0_ways`, `0_0_cluster`,
`0_0_scatter`, `0_0_expwilds`, `0_0_lines_feature_match`, `fifty_fifty`,
`template`.

Structure commune d'un jeu : `game_config.py`, `gamestate.py`,
`game_calculations.py`, `game_executables.py`, `game_override.py`,
`game_optimization.py`, `run.py`, `reels/`.

> Le découpage `game_*.py` montre le modèle voulu par Stake : **surcharger** les
> primitives par jeu, pas les remplacer.

### 5.1 — `0_0_lines`

- **Win type** : lines — 5 reels, `[3,3,3,3,3]`, 20 paylines, RTP 0.9670, wincap 5000
- **Mécaniques** : wild + multiplicateur de wild, scatter, free game sur reelset dédié
- **Trigger** : ≥ 3 scatters ; retrigger si ≥ 2 scatters sur reels 2/3/4
- **Free game** : multiplicateurs de wild ≥ 2x ; les multiplicateurs **s'additionnent**
- **BetModes** : `base` (cost 1.0), `bonus` (cost 100.0, buy)
- **Générique** : lines, free spins, wild, scatter, betmodes
- **Spécifique** : priorité de la combinaison gagnante sur une ligne, reelsets

### 5.2 — `0_0_ways`

- **Win type** : ways — 5 reels, 3 rows, H1–H5 / L1–L4 + W + S
- **Trigger** : ≥ 3 scatters, **max 1 scatter par reel**
- **Free game** : multiplicateurs de wild 1x–5x qui **se multiplient** entre eux
  (contrairement à `lines` où ils s'additionnent)
- **Spécifique** : wilds absents du reel 1

⚠️ Deux samples officiels combinent donc les multiplicateurs différemment. C'est
une **règle de jeu**, pas un défaut à unifier.

### 5.3 — `0_0_cluster`

- **Win type** : cluster — clusters de 5+ symboles identiques retirés du board
- **Mécaniques** : **tumble**, multiplicateurs **positionnels** sur la grille en
  free game (désactivés au départ, +1 par cluster gagnant à cette position)
- **Trigger** : 4 scatters en base, 3 en retrigger
- **Spécifique** : distinction entre entrée forcée en freespin et scatters
  arrivés naturellement par tumble

### 5.4 — `0_0_scatter`

- **Win type** : scatter / pay-anywhere — 6 reels, 5 rows, paliers par taille de
  cluster (8-8, 9-10, 11-13, 14-36)
- **Mécaniques** : tumble, **multiplicateur global persistant +1 par tumble**
- **Trigger** : ≥ 3 scatters → 2 free spins **par scatter**, sans limite de
  retrigger (des scatters peuvent tomber dans le board pendant les tumbles)
- **Events cités** : `winInfo`, `tumbleBanner`, `setWin`, `setTotalWin`

### 5.5 — `0_0_expwilds`

Le sample le plus riche en mécaniques de wild et de prix.

- **Structure** : 5 reels, 5 rows, 15 paylines, 9 symboles payants
- **Expanding wild** : en free game, un wild peut apparaître sur chaque reel et
  **s'étend sur toutes les rows actives**
- **Sticky wild** : ces wilds étendus sont **persistants** pour tous les spins
  restants du free game
- **Multiplicateur aléatoire** : 2x–50x appliqué à chaque nouveau reveal
- **Superspin (mode d'achat autonome)** : accessible **uniquement par le buy
  menu**, coût 25x, sans entrée par scatter. 3 « vies », spins supplémentaires
  à chaque symbole prix qui tombe, **prix accumulés puis évalués à la fin**
  (mécanique de type hold'em)

### 5.6 — Non audités en détail

`0_0_lines_feature_match`, `fifty_fifty`, `template`. `template` est
vraisemblablement le point de départ d'un nouveau jeu — **à inspecter avant de
créer le math d'un nouveau jeu**.

## 6. Matrice des mécaniques

Statuts : `PRIMITIVE STAKE` · `PATTERN SAMPLE` · `NON IDENTIFIÉ`.

| Mécanique | Statut | Math (où) | Frontend (event) | Sample | Réutilisation Gogold | Test futur |
| --- | --- | --- | --- | --- | --- | --- |
| **Lines** | PRIMITIVE STAKE | `calculations/lines.py` | `winInfo`, `setWin` | `0_0_lines` | Réutiliser | Math force + Storybook book |
| **Ways** | PRIMITIVE STAKE | `calculations/ways.py` | `winInfo`, `setWin` | `0_0_ways` | Réutiliser | Math force + Storybook book |
| **Cluster** | PRIMITIVE STAKE | `calculations/cluster.py` | `winInfo`, `setWin` | `0_0_cluster` | Réutiliser | Math force + Storybook book |
| **Scatter / pay-anywhere** | PRIMITIVE STAKE | `calculations/scatter.py` | `winInfo` | `0_0_scatter` | Réutiliser | Math force + Storybook book |
| **Tumble / cascade** | PRIMITIVE STAKE | `calculations/tumble.py` + `Executables.tumble_game_board()` | `tumbleBoard` (`newSymbols`, `explodingSymbols`), `updateTumbleWin`, `setTumbleWin` | `0_0_cluster`, `0_0_scatter` | Réutiliser / étendre | Storybook bookEvent (séquence) |
| **Free spins / free game** | PRIMITIVE STAKE | `Executables` (`check_fs_condition`, `run_freespin_from_base`, `update_freespin_amount`, `update_fs_retrigger_amt`, `update_freespin`, `end_freespin`) | `freeSpinTrigger`, `updateFreeSpin`, `freeSpinEnd` | tous | Réutiliser | Math force + Storybook book |
| **Scatter trigger** | PRIMITIVE STAKE | `Executables.check_fs_condition()` | `freeSpinTrigger` (`totalFs`, `positions`) | tous | Réutiliser | Math force |
| **Retrigger** | PRIMITIVE STAKE | `Executables.update_fs_retrigger_amt()` | `freeSpinRetrigger` | `0_0_lines`, `0_0_cluster` | Réutiliser | Math force |
| **Bonus trigger générique** | PRIMITIVE STAKE | `events.enter_bonus_event()` | `enterBonus` (`reason`) | — | Réutiliser | Storybook bookEvent |
| **Global multiplier** | PRIMITIVE STAKE | `multiplier_strategy.apply_mult('global')` + `Executables.update_global_mult()` | `updateGlobalMult` (`globalMult`) | `0_0_scatter` | Réutiliser | Storybook bookEvent |
| **Symbol multiplier** | PRIMITIVE STAKE | `apply_mult('symbol')` | via `winInfo` | `0_0_lines`, `0_0_ways` | Réutiliser | Math force |
| **Combined multiplier** | PRIMITIVE STAKE | `apply_mult('combined')` | via `winInfo` | — | Réutiliser | Math force |
| **Multiplier positionnel (grille)** | PATTERN SAMPLE | logique de jeu `0_0_cluster` | via `winInfo` | `0_0_cluster` | Partir du sample | Math force |
| **Wild (standard)** | PRIMITIVE STAKE | `Config.special_symbols` | via `reveal` / `winInfo` | tous | Réutiliser | Math force |
| **Expanding wild** | PATTERN SAMPLE | logique de jeu `0_0_expwilds` | via `reveal` | `0_0_expwilds` | Partir du sample | Math force + Storybook |
| **Sticky / persistent wild** | PATTERN SAMPLE | logique de jeu `0_0_expwilds` | via `reveal` | `0_0_expwilds` | Partir du sample | Math force + Storybook |
| **Random wild** | NON IDENTIFIÉ | — | — | — | Réexaminer avant tout dév | — |
| **Transforming wild** | NON IDENTIFIÉ | — | — | — | Réexaminer avant tout dév | — |
| **Respins** | NON IDENTIFIÉ | le « superspin » de `0_0_expwilds` en est le plus proche | — | `0_0_expwilds` | Partir du sample | Math force |
| **Prize values / collection** | PATTERN SAMPLE | superspin de `0_0_expwilds` (accumulation puis évaluation finale) | via `reveal` / `winInfo` | `0_0_expwilds` | Partir du sample | Math force |
| **Bet modes** | PRIMITIVE STAKE | `config/betmode.py` | `config_fe_*.json` | tous | Réutiliser | — |
| **Bonus buy** | PRIMITIVE STAKE | `BetMode.is_buybonus` | `betModes.buyBonus` | `0_0_lines`, `0_0_expwilds` | Réutiliser | Math force |
| **Feature mode** | PRIMITIVE STAKE | `BetMode.is_feature` | `betModes.feature` | `0_0_lines` | Réutiliser | — |
| **Max win handling** | PRIMITIVE STAKE | `WinManager.max_allowed_win` + `Executables.evaluate_wincap()` | `wincap` (`amount`) | tous | Réutiliser | Math force (obligatoire) |
| **Gestion des totaux de win** | PRIMITIVE STAKE | `wins/win_manager.py` | `setWin`, `setTotalWin`, `finalWin` | tous | Réutiliser | — |

**Aucune ligne n'est marquée `À CRÉER`.** C'est le résultat attendu de A7 : à ce
stade, aucune mécanique auditée ne justifie une bibliothèque Gogold.

## 7. Types de win — conclusion

Les quatre types de win auditionnés sont **fournis comme modules de calcul
génériques** dans `src/calculations/`, chacun démontré par un sample officiel.

> **[CONVENTION GOGOLD]** Réutiliser ou étendre ces primitives. Ne pas écrire de
> moteur Lines/Ways/Cluster/Scatter maison.

## 8. Tumble / cascade — conclusion

`Tumble` est une **primitive réelle**, pas un pattern de sample.

Répartition des responsabilités confirmée :

```text
GÉNÉRIQUE (Stake)                    SPÉCIFIQUE AU JEU
Tumble.tumble_board()                quels symboles sont marqués `explode`
Executables.tumble_game_board()      condition d'arrêt de la cascade
Executables.emit_tumble_win_events() effet du tumble sur le multiplicateur
event tumbleBoard                    présentation (chute, timing, sons)
```

Deux samples l'utilisent avec des règles différentes (`0_0_cluster` :
multiplicateurs positionnels ; `0_0_scatter` : multiplicateur global +1 par
tumble). C'est exactement la variabilité que Stake laisse au jeu.

## 9. Free games — conclusion

Framework **fourni** (§4.3). Reste spécifique au jeu : le nombre de spins
accordés, les conditions de trigger et de retrigger, le reelset utilisé, et le
comportement des features pendant le free game.

Le nombre de free spins est transporté par l'event `freeSpinTrigger`
(`totalFs`) : le frontend l'affiche, il ne le connaît pas d'avance (voir
`CONFIGURATION.md` §2).

## 10. Bet modes / bonus buy — conclusion

`BetMode` fournit déjà `name`, `cost`, `rtp`, `max_win`, `auto_close_disabled`,
`is_feature`, `is_buybonus`, `distributions`.

> **[CONVENTION GOGOLD]** Ne créer aucun système `BonusBuy()` Gogold. Un bonus
> buy est un `BetMode` avec `is_buybonus=True` et un `cost` propre. Le superspin
> de `0_0_expwilds` (buy-only, 25x) montre qu'un mode d'achat autonome, sans
> entrée par scatter, se modélise déjà entièrement avec `BetMode`.

## 11. Mécaniques de wild — conclusion

- **Wild standard** : [PRIMITIVE STAKE] — déclaré dans `Config.special_symbols`.
- **Expanding wild**, **sticky wild** : [PATTERN SAMPLE] — implémentés dans la
  logique de `0_0_expwilds`, **pas exposés comme primitive générique**.
- **Random wild**, **transforming wild** : `PAS DE PRIMITIVE OFFICIELLE
  IDENTIFIÉE`.

> **[CONVENTION GOGOLD]** Pour un expanding ou sticky wild, partir du code de
> `0_0_expwilds` plutôt que d'inventer une abstraction. Ne rien créer tant qu'un
> jeu Gogold n'en a pas le besoin établi.

## 12. Multiplicateurs — conclusion

Stake distingue explicitement plusieurs concepts. Ne pas les regrouper.

| Type | Statut | Où | Event | Sample |
| --- | --- | --- | --- | --- |
| Global multiplier | PRIMITIVE | `apply_mult('global')`, `Executables.update_global_mult()` | `updateGlobalMult` | `0_0_scatter` |
| Symbol multiplier | PRIMITIVE | `apply_mult('symbol')` | via `winInfo` | `0_0_lines`, `0_0_ways` |
| Combined | PRIMITIVE | `apply_mult('combined')` | via `winInfo` | — |
| Positionnel (grille) | PATTERN SAMPLE | logique `0_0_cluster` | via `winInfo` | `0_0_cluster` |

⚠️ La **façon de combiner** varie par jeu : additive dans `0_0_lines`,
multiplicative dans `0_0_ways`, positionnelle dans `0_0_cluster`, +1 par tumble
dans `0_0_scatter`. Un `GGMultiplier` unique écraserait cette variabilité.

**Ownership** : le math décide de la valeur, le frontend l'affiche
(`CONFIGURATION.md` §7).

## 13. Prize values / collecteurs

`PATTERN SAMPLE` — démontré uniquement par le superspin de `0_0_expwilds` :
symboles porteurs de prix, accumulation pendant les spins, évaluation à la fin
du mode.

Aucune primitive générique de « prize collection » n'a été identifiée dans
`src/`. À partir du sample si le besoin apparaît.

## 14. Contrat d'events Math ↔ Frontend — **[CONTRAT STAKE]**

Chaîne officielle (voir `CONFIGURATION.md` §5.4) :

```text
Math → bookEvent → bookEventHandlerMap → emitterEvent → composant / animation
```

Events génériques émis par `src/events/events.py` :

| Event | Payload | Mécanique concernée |
| --- | --- | --- |
| `reveal` | `board`, `paddingPositions`, `gameType`, `anticipation` | toutes |
| `freeSpinTrigger` | `totalFs`, `positions` | free spins |
| `freeSpinRetrigger` | `totalFs`, `positions` | retrigger |
| `updateFreeSpin` | `amount`, `total` | compteur de free spins |
| `freeSpinEnd` | `amount`, `winLevel` | fin de free game |
| `setWin` | `amount`, `winLevel` | win de spin |
| `setTotalWin` | `amount` | total du round |
| `finalWin` | `amount` | résultat final |
| `winInfo` | `totalWin`, `wins` (positions, montants, métadonnées) | tous types de win |
| `tumbleBoard` | `newSymbols`, `explodingSymbols` | tumble |
| `setTumbleWin` / `updateTumbleWin` | `amount` | tumble |
| `updateGlobalMult` | `globalMult` | multiplicateur global |
| `wincap` | `amount` | max win |
| `enterBonus` | `reason` | entrée en bonus |

Côté frontend, `apps/lines/src/game/typesBookEvent.ts` déclare l'union
discriminée correspondante (`reveal`, `setTotalWin`, `finalWin`, `setWin`,
`freeSpinTrigger`, `updateFreeSpin`, `freeSpinEnd`, `winInfo`,
`createBonusSnapshot`). Chaque jeu ne type que les events qu'il utilise.

> **[CONVENTION GOGOLD]** Un event Gogold personnalisé n'est créé que si aucun
> event de cette liste ne couvre le besoin. Aucun n'est créé aujourd'hui.

## 15. Stratégie de test — **[PRIMITIVE STAKE]**

Trois mécanismes existent déjà. Les utiliser **avant** toute infrastructure de
test maison.

### 15.1 — Force files (math)

`src/write_data/force.py` fournit `Option`, `Search` et `IdentityCondition`. Une
condition sélectionne les simulations à conserver, soit par critères
(paires nom/valeur), soit par montant ou plage de gain, avec un drapeau
`opposite` pour inverser. Les deux types de condition ne peuvent pas être
combinés.

Sortie : `force_record_{betmode}.json`. C'est le moyen officiel d'atteindre les
cas rares — bonus, max win, retrigger.

### 15.2 — Storybook (frontend)

`web-sdk/apps/lines/src/stories/` contient :

```text
ComponentsGame.stories.svelte      un jeu complet
ComponentsSymbol.stories.svelte    un symbole isolé
ModeBaseBook.stories.svelte        un book complet, mode base
ModeBaseBookEvent.stories.svelte   un bookEvent isolé, mode base
ModeBonusBook.stories.svelte       un book complet, mode bonus
ModeBonusBookEvent.stories.svelte  un bookEvent isolé, mode bonus
data/                              fixtures
```

On peut donc tester **un book entier** ou **un event isolé**, par mode. C'est
exactement ce qu'il faut pour valider une mécanique côté frontend.

> **[CONVENTION GOGOLD]** Quand une mécanique sera implémentée, son comportement
> frontend devra être isolable selon ces patterns. Rappel `CLAUDE.md` : un event
> sans story est un event non testé. **Aucune story n'est créée ici.**

### 15.3 — Bet Replay

Bet Replay est une exigence d'approbation pour les nouveaux jeux Stake.

> **[CONVENTION GOGOLD]** Conséquence directe pour les mécaniques : une
> mécanique doit être **déterministe à partir des seules données du round**. Si
> son rendu dépend d'un `Math.random()` non décoratif, d'une horloge ou d'un
> état accumulé hors du round, elle ne sera pas rejouable correctement.

Aucun Bet Replay n'est développé ici.

## 16. Futurs jeux — mécaniques non définies

```text
No game mechanics formally defined in repository yet.
```

Vérifié : aucun document du repository ne décrit les mécaniques d'un jeu Gogold,
et aucune roadmap produit n'existe. `<game>`, `game-002` et `game-003`
n'apparaissent que comme illustrations d'arborescence dans `ARCHITECTURE.md`.
**Aucun jeu n'est inventé ici.**

⚠️ `barrelFill` / `barrelFull` apparaissent dans `ASSETS.md`, mais **uniquement
comme exemples de nommage** — `ASSETS.md` précise lui-même qu'aucun event de ce
type n'est créé. Ce ne sont **pas** des mécaniques déclarées et elles ne doivent
pas être interprétées ainsi.

## 17. Ce que Gogold doit réutiliser

- les quatre modules de win : `lines`, `ways`, `cluster`, `scatter` ;
- `Tumble` pour toute cascade ;
- `Executables` pour les free spins, le wincap et le multiplicateur global ;
- `WinManager` pour les totaux et le plafond de gain ;
- `apply_mult()` et ses trois stratégies ;
- `Config` / `BetMode` pour les modes et le bonus buy ;
- le catalogue d'events de `src/events/events.py` ;
- le mécanisme de force files et les patterns Storybook pour les tests ;
- le modèle de surcharge par jeu (`game_*.py`) plutôt que le remplacement.

## 18. Ce que Gogold ne doit PAS construire maintenant

```text
packages/mechanics/   packages/features/   packages/slot-mechanics/

GGWays   GGLines   GGCascade   GGFreeSpins
GGMultiplier   GGStickyWild   GGBonusBuy

interface Mechanic {}      interface Feature {}      class GogoldMechanic
```

Aucun schéma de mécanique universel, aucune configuration générique de features.

**Raison** : chacun de ces éléments existe déjà chez Stake sous une forme plus
précise, ou n'a encore aucun usage réel dans Gogold.

### Modification des primitives Stake — **[CONVENTION GOGOLD]**

> Ne jamais modifier directement une primitive générique Stake pour satisfaire
> un seul jeu, sans analyser l'impact sur les autres jeux.

Ordre de préférence :

```text
configuration  →  composition  →  extension / surcharge (game_*.py)
               →  code spécifique au jeu
               →  (en dernier recours) modification de la primitive commune
```

Cohérent avec `CLAUDE.md` : ce qui est spécifique à Gogold va dans `gogold/`,
jamais dans `src/` du SDK forké.

## 19. Critères d'extraction future — **[CONVENTION GOGOLD]**

Une mécanique ne devient un package ou une abstraction Gogold que si **au moins
une** de ces situations est vérifiée :

1. Stake ne fournit pas la fonctionnalité nécessaire.
2. La même adaptation au-dessus de Stake est réellement requise par plusieurs
   jeux Gogold.
3. Copier cette adaptation provoquerait une duplication significative.
4. L'abstraction peut être créée **sans masquer ni casser** le contrat Stake.

> De préférence, attendre **au moins deux usages réels** avant d'extraire une
> abstraction générique, sauf besoin évident et stable.

Cohérent avec `ARCHITECTURE.md` : la frontière GAME / PLATFORM se découvre en
construisant le deuxième jeu.

## 20. Checklist pour une nouvelle mécanique

- [ ] Ai-je cherché une primitive dans `src/calculations/`, `src/executables/`,
      `src/wins/` ?
- [ ] Un sample officiel démontre-t-il déjà cette mécanique ?
- [ ] Puis-je l'obtenir en **composant** des primitives existantes ?
- [ ] La partie math et la partie présentation sont-elles bien séparées ?
- [ ] Un event existant du catalogue couvre-t-il le besoin ?
- [ ] La mécanique est-elle rejouable à partir des seules données du round ?
- [ ] Ai-je prévu un scénario de force (math) et une story (frontend) ?
- [ ] Si je veux l'extraire en package : les critères du §19 sont-ils remplis ?

## 21. Publication

Rappel (`CONFIGURATION.md` §12) : toute mécanique converge vers deux livrables.

```text
Math      →  fichiers de publication statiques (books, lookup tables, configs)
Frontend  →  build statique
```

Aucune mécanique n'introduit de couche runtime serveur Gogold.

## Ce que ce document ne fait PAS

Il ne crée aucune mécanique, aucun package, aucune interface, aucun event,
aucune story, aucun force file, aucun code math ni frontend.

Il n'invente aucune roadmap produit et aucune mécanique de jeu.

Il n'affirme comme générique que ce que le SDK expose réellement comme tel : tout
le reste est marqué [PATTERN SAMPLE] ou `NON IDENTIFIÉ`.
