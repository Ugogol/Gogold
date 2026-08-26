# Gogold — Architecture de configuration d'un jeu

Ce document répond à une seule question :

```text
QUELLE INFORMATION → EST DÉFINIE OÙ → QUI EN EST LA SOURCE DE VÉRITÉ
                                    → COMMENT L'AUTRE CÔTÉ LA CONSOMME
```

Il est destiné à un membre de l'équipe qui ne connaît pas encore bien Stake
Engine. **C'est un document d'analyse. Il ne crée aucune configuration.**

## 0. Comment lire ce document

Mêmes étiquettes que `docs/ASSETS.md`. Ne pas confondre les trois niveaux.

| Étiquette | Signification |
| --- | --- |
| **[CONTRAT STAKE]** | Imposé par le code ou le contrat Stake (Math SDK, Web SDK, RGS). Non négociable. |
| **[PATTERN SAMPLE]** | Observé dans les sample games officiels, **non documenté comme obligatoire**. |
| **[CONVENTION GOGOLD]** | Décision interne de notre équipe. Ne pas l'attribuer à Stake. |

**Sources officielles utilisées** (uniquement `github.com/StakeEngine`) :
`math-sdk` (`src/config/`, `src/write_data/`, `games/0_0_lines/`) et `web-sdk`
(`apps/lines/src/game/`). Les sites `stakeengine.github.io` et
`stake-engine.com/docs` sont restés inaccessibles (404 / SPA) lors de cette
analyse : tout ce qui est marqué [CONTRAT STAKE] vient donc du **code source
officiel**, pas d'une page de documentation.

## 1. Pourquoi ce document existe

Nous voulons éviter cette situation :

```text
frontend :  RTP = 0.97   symbols = [...]   paytable = A
math :      RTP = 0.96   symbols = [...]   paytable = B
```

Deux définitions indépendantes de la même information finissent toujours par
diverger. Le jour où elles divergent, le jeu affiche autre chose que ce qu'il
paie — et c'est un bug de certification, pas un bug d'affichage.

A6 fixe donc **qui possède quoi**, avant que la moindre ligne de configuration
de jeu soit écrite.

## 2. Principe : une seule source de vérité

**Définition — [CONVENTION GOGOLD]**

> La **source de vérité** est l'endroit officiel où une information est définie.
> Les autres parties du système peuvent la lire ou la représenter, mais ne
> doivent pas en maintenir une deuxième version indépendante.

**Règle fondamentale — [CONVENTION GOGOLD]**

> Toute donnée ayant un impact sur les probabilités, les gains, le résultat d'un
> spin, le coût d'un mode, le déclenchement d'une feature ou la logique
> mathématique a **le Math comme source de vérité**.

Le frontend ne doit jamais pouvoir modifier un résultat mathématique. C'est déjà
la conséquence directe du modèle précalculé de Stake : le RGS renvoie un `book`
déjà décidé, le frontend le rejoue.

**Exemple concret.** L'événement `freeSpinTrigger` transporte un champ
`totalFreeSpins` (vérifié dans `typesBookEvent.ts`).

```text
✓ Math décide 10 free spins → event freeSpinTrigger { totalFreeSpins: 10 }
                            → le frontend affiche 10

✗ const FREE_SPINS = 10 dans le frontend
```

Avec la seconde forme, le jour où le math passe à 12, le frontend affiche encore
10. Le joueur voit 10, en reçoit 12, et personne ne comprend pourquoi.

## 3. Math game configuration — **[CONTRAT STAKE]**

⚠️ **`GameConfig` existe déjà côté math.** Ne jamais en créer un second.

Vérifié dans `math-sdk/games/0_0_lines/game_config.py` :

```python
class GameConfig(Config):   # hérite de la classe de base du SDK
```

Un jeu math officiel contient :

```text
games/0_0_lines/
├── reels/                    BR0.csv, FR0.csv, FRWCAP.csv
├── game_config.py            ← le modèle de jeu
├── gamestate.py              ← état pendant la simulation
├── game_calculations.py
├── game_executables.py
├── game_optimization.py
├── game_override.py
├── run.py                    ← exécution des simulations
└── readme.txt
```

### 3.1 — Ce que définit `game_config.py`

Paramètres observés dans `0_0_lines`, hérités/étendus depuis la classe `Config`
de `src/config/config.py` :

| Paramètre | Exemple `0_0_lines` |
| --- | --- |
| `game_id`, `provider_name`, `game_name` | `"0_0_lines"`, `"sample_provider"` |
| `rtp` | `0.9670` |
| `wincap` (max win) | `5000.0` |
| `win_type` | `"lines"` |
| `num_reels`, `rows` | `5`, `[3, 3, 3, 3, 3]` |
| `paylines` | 20 lignes définies |
| `paytable` | 5×W = 50 … 3×L5 = 0.1 |
| `special_symbols` | `{wild: ["W"], scatter: ["S"], multiplier: ["W"]}` |
| `reels` / `padding_reels` | `BR0.csv`, `FR0.csv`, `FRWCAP.csv` |
| `freespin_triggers` | conditions de déclenchement |
| `bet_modes` | liste de `BetMode` |
| `opt_params` | paramètres d'optimisation |
| `min_denomination` | `0.1` |

**Tous ces paramètres influencent le résultat mathématique.** Ils sont donc, sans
exception, `MATH SOURCE OF TRUTH`.

### 3.2 — `BetMode` — **[CONTRAT STAKE]**

Classe fournie par le SDK (`src/config/betmode.py`). Champs vérifiés :

```text
name  ·  cost  ·  rtp  ·  max_win  ·  auto_close_disabled
is_feature  ·  is_buybonus  ·  distributions  ·  force_keys
```

Le **coût d'un mode est défini côté math**, jamais côté frontend.

### 3.3 — `run.py` n'est PAS le modèle de jeu

Distinction importante et souvent ratée. `run.py` ne contient que des paramètres
d'**exécution des simulations** :

```text
num_threads = 10        rust_threads = 20      batching_size = 5000
compression = True      profiling = False
num_sim_args = {"base": 1e4, "bonus": 1e4}
run_conditions = {...}
```

> Changer `run.py` change **la façon dont on simule**, pas **le jeu**. Changer
> `game_config.py` change **le jeu** — donc le RTP, donc la publication.
> **[CONVENTION GOGOLD]** Un changement dans `game_config.py` est un changement
> mathématique : jamais un PATCH (voir versioning dans `CLAUDE.md`).

## 4. Frontend game configuration — **[PATTERN SAMPLE]**

Vérifié dans `web-sdk/apps/lines/src/game/` :

| Fichier | Rôle |
| --- | --- |
| `config.ts` | modèle de jeu **recopié** du math (voir §5.1) |
| `assets.ts` | mapping symbole/élément → asset, et flags `preload` |
| `typesBookEvent.ts` | types des events reçus du math |
| `typesEmitterEvent.ts` | types des events internes au frontend |
| `bookEventHandlerMap.ts` | `bookEvent.type` → handler |
| `stateGame.svelte.ts` | état de jeu runtime (runes Svelte 5) |
| `stateApp.ts`, `stateLayout.ts`, `stateXstate.ts` | états app / layout / machine |
| `sound.ts`, `winLevelMap.ts`, `constants.ts`, `utils.ts` | présentation |

Ce qui appartient réellement au frontend : **la représentation**. Dimensions
visuelles du board, mapping asset → symbole, animation choisie, durée visuelle,
particules, son associé à un événement, layout mobile/desktop, fonts,
background, skin des boutons.

## 5. Shared contract Math ↔ Frontend

> **[CONVENTION GOGOLD]** `SHARED CONTRACT` ne signifie pas « recopier
> manuellement la même valeur dans deux fichiers ». Cela signifie : **une
> définition, une projection contrôlée**.

### 5.1 — Le point le plus important de A6 : `config_fe_{gameID}.json`

**Le Math SDK génère lui-même la configuration destinée au frontend.**

Vérifié dans `math-sdk/src/write_data/write_configs.py`, fonction
`make_fe_config()`, qui écrit `config_fe_{game_id}.json` avec ces clés :

```text
providerName · gameName · gameID · rtp · numReels · numRows
betModes { cost, feature, buyBonus, rtp, max_win }
paylines · symbols (paytable + special_properties) · paddingReels
```

Or, `web-sdk/apps/lines/src/game/config.ts` exporte **exactement les mêmes
clés**, avec les mêmes valeurs :

```ts
export default {
	providerName: 'sample_provider',
	gameName: 'sample_lines',
	gameID: '0_0_lines',
	rtp: 0.97,
	numReels: 5,
	numRows: [3, 3, 3, 3, 3],
	betModes: {
		base:  { cost: 1.0,   feature: true,  buyBonus: false, rtp: 0.97, max_win: 5000.0 },
		bonus: { cost: 100.0, feature: false, buyBonus: true,  rtp: 0.97, max_win: 5000.0 },
	},
	// paylines, symbols, paddingReels
}
```

**Constat.** `config.ts` ne contient **aucun import de JSON**, aucun commentaire
de génération, aucun codegen. Le jeu de clés est identique à la sortie Python —
y compris `max_win` en snake_case au milieu d'un objet entièrement camelCase, ce
qui trahit une transcription depuis la sortie du Math SDK.

> **Autrement dit : dans les sample games officiels, la configuration frontend
> est une recopie manuelle de ce que le math a déjà généré.** Le mécanisme de
> synchronisation n'existe pas — c'est de la discipline humaine.

**Conséquence pour Gogold — [CONVENTION GOGOLD]** :

- la **source de vérité** de ces données est `game_config.py` (math), qui produit
  `config_fe_{gameID}.json` ;
- le `config.ts` frontend est une **projection**, jamais une définition
  concurrente ;
- personne ne modifie une valeur dans `config.ts` pour « corriger » un affichage.
  On corrige le math, on régénère, on reporte ;
- la façon exacte de fiabiliser ce report (import du JSON, génération, contrôle
  CI) est une **décision reportée** — voir §14.

### 5.2 — Identifiants de symboles — **[CONTRAT STAKE]**

Source de vérité : **le math**. Définis dans `game_config.py`
(`special_symbols`, `paytable`) et transportés dans les books/bookEvents.

Dans `0_0_lines` : `H1..H5`, `L1..L4`, `W`, `S`, `M`.

Rappel de la conclusion A5, qui reste valable :

```text
ID Math/RGS   ≠ nécessairement   nom du fichier graphique
```

Le frontend associe l'ID à un asset **explicitement**, dans `assets.ts` :

```text
H1 → spines/symbols/h1.json          W → spines/symbols3/W.json
S  → spines/symbols2/S.json          M → spines/symbols2/M.json
```

C'est ce mapping qui fait autorité, pas une règle de casse. **Le frontend est
source de vérité du mapping ID → asset ; il n'est jamais source de vérité de
l'ID lui-même.**

### 5.3 — Game modes / bet modes — **[CONTRAT STAKE]**

Vérifié : les modes sont définis côté math, dans `game_config.py`, via des objets
`BetMode`. Dans `0_0_lines` :

| Mode | cost | is_feature | is_buybonus | max_win |
| --- | --- | --- | --- | --- |
| `base` | 1.0 | true | false | 5000 |
| `bonus` | 100.0 | false | true | 5000 |

Le nom du mode et son coût circulent ensuite vers Stake par deux fichiers
générés (`src/config/output_filenames.py`) :

- `index.json` (manifest) — par mode : `name`, `cost`, fichier d'events, fichier
  de poids ;
- `config.json` (backend) — `BookShelfConfig` par mode : lookup table, books,
  force file, hashes, cost, RTP, écart-type, flags.

> **[CONVENTION GOGOLD]** Le frontend n'invente jamais un mode et n'en fixe
> jamais le coût. `CLAUDE.md` le dit déjà côté runtime : les valeurs de mise
> viennent de `/wallet/authenticate`, jamais d'une constante frontend.

### 5.4 — Book events — **[CONTRAT STAKE]**

Architecture vérifiée dans le README officiel du Web SDK et dans le code :

```text
Math génère les events
        ↓
book.events (renvoyé par le RGS)
        ↓
bookEventHandlerMap  →  bookEvent.type → bookEventHandler
        ↓
eventEmitter.broadcast()  →  emitterEvent
        ↓
composants Svelte (eventEmitter.subscribeOnMount)
```

Types réellement déclarés dans `apps/lines/src/game/typesBookEvent.ts`
(union discriminée sur `type`) :

```text
reveal              board, paddingPositions, anticipation
setTotalWin         amount
finalWin            amount
setWin              amount, winLevel
freeSpinTrigger     totalFreeSpins, positions
updateFreeSpin      amount, total
freeSpinEnd         amount, winLevel
winInfo             symbols, multipliers, positions
createBonusSnapshot bookEvents imbriqués
```

**Le nom et la charge utile de chaque event sont le contrat.** Le math les
produit, le frontend les consomme. Aucun des deux ne peut les changer seul.

## 6. Configuration vs Runtime State

Distinction à ne jamais confondre.

**Configuration** — valeur relativement stable qui définit *comment le jeu
fonctionne* : paytable, reel strips, modes, mapping des assets, dimensions du
board.

**State** — valeur qui change *pendant* une partie.

Vérifié côté frontend (`stateGame.svelte.ts`, runes Svelte 5) :

```ts
export const stateGame = $state({
	board,
	gameType: 'basegame' as GameType,
	multiplierBoard: [],
	scatterCounter: 0,
});
```

Côté math, l'équivalent est `gamestate.py` (état pendant la simulation), distinct
de `game_config.py`.

> **[CONVENTION GOGOLD]** Ne jamais placer un état runtime dans un fichier de
> configuration parce qu'il « concerne le jeu ». Balance, gain courant,
> multiplicateur courant, free spins restants, board courant, mode courant sont
> des **états**, pas de la configuration.

## 7. Configuration vs Book Events

> **[CONVENTION GOGOLD]** Ne pas dupliquer côté frontend une information que le
> Math/RGS transmet déjà pendant le round.

```text
Math  →  bookEvent  →  Frontend
```

Si un event fournit `multiplier = 7`, le frontend **affiche 7**. Il ne le
recalcule pas, ne le déduit pas d'une table locale, ne le corrige pas.

Test simple, à appliquer avant d'ajouter la moindre constante frontend :

> Cette valeur est-elle déjà présente dans un `bookEvent` ou dans la
> configuration générée par le math ? Si oui, la constante frontend est un bug
> en attente.

## 8. Mapping des principales données

Chaque ligne a été vérifiée contre le code officiel.

| Donnée | Source de vérité | Consommateur | Pourquoi |
| --- | --- | --- | --- |
| RTP | **Math** (`game_config.py`) | Stake, analyse, affichage | Détermine la distribution des gains |
| Paytable | **Math** | Math (calcul), frontend (affichage) | Détermine les gains |
| Reel strips (`BR0.csv`…) | **Math** | Math | Déterminent les résultats |
| Probabilités / distributions | **Math** | Math, optimiseur | Cœur du modèle |
| `wincap` / max win | **Math** | Stake, frontend (affichage) | Contrainte mathématique |
| Coût d'un bet mode | **Math** (`BetMode.cost`) | Stake, RGS, frontend | Définit le prix du round |
| Déclenchement de bonus | **Math** (`freespin_triggers`) | Math | Le frontend ne décide jamais |
| Nombre de free spins attribué | **Math** → event `freeSpinTrigger` | Frontend (affichage) | Transporté par l'event |
| Résultat d'un spin | **Math / RGS** (book) | Frontend | Le frontend rejoue, ne calcule pas |
| Multiplicateur d'un round | **Math** → event | Frontend (affichage) | Vient de l'event |
| Identifiants de symboles | **Shared contract** (défini math) | Math + frontend | Permet le mapping |
| Noms et payloads des bookEvents | **Shared contract** | Math + frontend | Langage commun |
| Identifiants de bet modes | **Shared contract** (défini math) | Math + frontend + RGS | Sélection du mode |
| Dimensions du board (`numReels`, `numRows`) | **Math** → `config_fe` | Frontend | Contrainte du modèle, pas un choix visuel |
| Mapping ID → asset (`assets.ts`) | **Frontend** | Frontend | Pure représentation |
| Asset visuel, atlas, spine | **Frontend** | Frontend | Pure représentation |
| Animation et sa durée visuelle | **Frontend** | Frontend | Pure représentation |
| Son associé à un event | **Frontend** | Frontend | Pure représentation |
| Layout mobile / desktop | **Frontend** | Frontend | Pure représentation |
| Paramètres de simulation (`run.py`) | **Math (outillage)** | Math | N'affecte pas le modèle de jeu |
| `index.json`, `config.json`, books, lookup tables | **Généré par le Math** | Stake / RGS | Livrable de publication |

⚠️ `numReels` / `numRows` sont un cas piège : ils **ressemblent** à de la mise en
page, mais ils décrivent la grille du modèle mathématique. Ils viennent du math.
Le frontend décide de la **taille à l'écran**, pas du **nombre de cases**.

## 9. MATH OWNS — **[CONTRAT STAKE]**

Domaines dont le math est source de vérité, d'après `Config`, `BetMode`,
`gamestate.py` et les sample games :

- RTP, `wincap` / max win, `min_denomination` ;
- paytable et valeurs de gains ;
- reel strips et padding reels ;
- symboles : identifiants et propriétés spéciales (wild, scatter, multiplier) ;
- lignes de paiement / type de win (`win_type`) ;
- dimensions de la grille (`num_reels`, `rows`) ;
- conditions de déclenchement des features (`freespin_triggers`) ;
- bet modes : nom, coût, flags `is_feature` / `is_buybonus`, max win ;
- distributions et quotas de simulation ;
- paramètres d'optimisation (`opt_params`) ;
- le résultat de chaque round (books) et les probabilités (lookup tables).

## 10. FRONTEND MAY DECIDE — **[CONVENTION GOGOLD]**

Décisions qui peuvent rester purement frontend, tant qu'elles n'influencent
aucun résultat mathématique :

- quel asset représente quel symbole (`assets.ts`) ;
- quelle animation joue, et sa durée visuelle ;
- position, échelle, layout, responsive, portrait/paysage ;
- particules et effets ;
- son associé à un événement, ducking, ambiance ;
- transitions graphiques, skin des boutons, fonts, background ;
- ordre de préchargement des assets (`preload`).

⚠️ **Vérifier avant de classer un timing ici.** Une durée purement décorative est
frontend. En revanche, tout ce qui touche au déroulement obligatoire du round —
ordre des events, appel de fin de round, reprise d'un round actif — relève du
protocole Stake, pas d'un choix esthétique. Le mode turbo raccourcit les
animations, il ne saute pas d'event.

## 11. NEVER DUPLICATE

Types de données qui ne doivent **jamais** exister en deux sources
indépendantes.

**Conséquences directes du contrat Stake — [CONTRAT STAKE]** :

- ne pas recalculer un résultat de spin côté frontend : il vient du book ;
- ne pas décider d'un déclenchement de bonus côté frontend : il est dans le book ;
- ne pas créer un second `GameConfig` math : la classe existe déjà dans le SDK ;
- ne pas maintenir deux définitions d'un même `bookEvent.type` ou de sa charge
  utile.

**Règles d'architecture Gogold — [CONVENTION GOGOLD]** :

- ne pas définir une paytable indépendante côté frontend ;
- ne pas donner au frontend une logique capable de modifier un payout ;
- ne pas recopier un paramètre math uniquement pour faciliter une animation si
  l'information est déjà dans les events ;
- ne pas écrire de constante frontend pour une valeur transportée par un event
  (`totalFreeSpins`, `multiplier`, `winLevel`, `amount`…) ;
- ne pas modifier une valeur dans `config.ts` pour corriger un affichage :
  corriger le math, régénérer, reporter ;
- ne pas hardcoder les valeurs de mise ni `rgs_url` (déjà dans `CLAUDE.md`).

## 12. Les deux livrables — **[CONTRAT STAKE]**

L'architecture doit produire **deux livrables indépendants** :

```text
FRONTEND BUILD              MATH PUBLISH FILES
(bundle web statique)       (books, lookup tables, configs)
```

Fichiers de publication réellement générés par le Math SDK (vérifié dans
`src/config/output_filenames.py`) :

```text
index.json                       manifest : mode, cost, events, weights
config.json                      backend : BookShelfConfig + hashes
config_fe_{game_id}.json         configuration destinée au frontend
math_config.json                 paramètres d'optimisation
books_{betmode}.jsonl.zst        séquences d'events
lookUpTable_{betmode}.csv        probabilités (+ _0, + Segmented)
force_record_{betmode}.json      cas forcés pour les tests
```

Répartis dans `library/`, `configs/`, `books/`, `forces/`, `lookup_tables/`,
`publish_files/`, `optimization_files/`.

> **[CONVENTION GOGOLD]** Le repository de développement peut être plus large
> que ces deux livrables, mais les deux côtés doivent rester configurables sans
> dépendance inutile l'un vers l'autre. Rappel `CLAUDE.md` : books, lookup
> tables et assets binaires ne sont jamais commités.

## 13. Ce que Stake fournit déjà

À ne pas réimplémenter :

**Math SDK** — classe de base `Config` (`src/config/config.py`), `BetMode`
(`src/config/betmode.py`), distributions, paramètres d'optimisation, `GameState`
(`src/state/`), génération des books et lookup tables, et **toute la génération
des fichiers de publication** (`src/write_data/`), y compris `config_fe_*.json`.

**Web SDK** — `config.ts` / `assets.ts` par jeu, système d'events complet
(`bookEvent`, `bookEventHandlerMap`, `emitterEvent`, `eventEmitter`), états
frontend (`stateApp`, `stateGame`, `stateLayout`, `stateXstate`), chargement des
assets via `PIXI.Assets.load`, et les packages `utils-*` / `components-*`.

## 14. Ce que nous déciderons plus tard

Diagnostiqué ici, **non décidé, non implémenté** :

1. **Synchronisation `config_fe_{gameID}.json` → `config.ts`.** C'est le risque
   de duplication n°1 identifié par A6. Options à évaluer : import direct du JSON
   généré, génération de types, ou contrôle automatisé de cohérence. Les samples
   Stake le font à la main.
2. **Contrôle de cohérence Python ↔ TypeScript** pour les `bookEvent` (noms et
   payloads). Aucun mécanisme n'est fourni par Stake.
3. ~~Emplacement du repo math~~ — **tranché** : le Math SDK vit dans `math/` de
   ce monorepo (voir `docs/MATH.md`). Il n'y a pas de repository séparé.
4. Un éventuel package partagé (`packages/…`) pour le contrat. **Rien n'est créé
   aujourd'hui** : ce serait une abstraction prématurée avant le premier jeu.

Aucun générateur de code, schéma JSON, protobuf ou OpenAPI n'est introduit : ce
serait prématuré.

## 15. Checklist pour un nouveau jeu

Avant d'ajouter une valeur de configuration, se poser ces questions dans l'ordre :

- [ ] Cette valeur influence-t-elle un gain, une probabilité, un coût ou un
      déclenchement ? → **Math**, sans discussion.
- [ ] Est-elle déjà générée par le math dans `config_fe_{gameID}.json` ? → ne pas
      la redéfinir côté frontend.
- [ ] Est-elle déjà transportée par un `bookEvent` ? → l'afficher, ne pas la
      stocker.
- [ ] Change-t-elle pendant une partie ? → c'est un **état**, pas de la
      configuration.
- [ ] Est-elle purement visuelle et sans effet sur le résultat ? → **Frontend**.
- [ ] Doit-elle être comprise identiquement des deux côtés ? → **Shared
      contract** : définie une fois côté math, projetée côté frontend.
- [ ] Stake fournit-il déjà ce mécanisme ? → l'utiliser plutôt que le recréer.

## Ce que ce document ne fait PAS

Il ne crée aucune configuration de jeu, aucun `game.config.ts` Gogold, aucun
package de configuration, aucun schéma cross-language, aucun générateur, aucun
event, aucun client RGS, aucun build et aucun fichier de publication.

Il n'invente aucune obligation Stake : tout ce qui n'est pas marqué
**[CONTRAT STAKE]** est une observation ou une décision Gogold, révisable.

Il établit qui possède quelle information — avant que nous écrivions quoi que ce
soit.
