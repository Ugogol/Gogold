# Conventions Assets & Nommage — Gogold

Comment nommer et organiser les assets des jeux Gogold. Destiné à toute
l'équipe, y compris aux profils non techniques (graphisme, animation, son).
Aucune connaissance de Stake Engine n'est requise pour le lire.

**Ce document définit des règles. Il ne construit rien.**

## 0. Comment lire ce document

Chaque règle est étiquetée selon son niveau d'autorité. Ne pas confondre les
trois : une pratique observée dans un jeu d'exemple n'est pas une obligation de
la plateforme.

| Étiquette | Signification |
| --- | --- |
| **[CONTRAT STAKE]** | Explicitement documenté par Stake (doc officielle du Web SDK) ou imposé par le contrat math ↔ frontend. Non négociable. |
| **[PATTERN SAMPLE]** | Observé de façon cohérente dans les sample games officiels, mais **non documenté comme obligatoire**. Gogold l'adopte par cohérence, pas par contrainte. |
| **[CONVENTION GOGOLD]** | Décision interne de notre équipe, pour garder le repository propre. Ne pas l'attribuer à Stake. |

**Sources officielles utilisées** (uniquement `github.com/StakeEngine`) :
`README.md` du Web SDK, et les sample games `apps/lines`, `apps/cluster`,
`apps/ways`.

Stake ne publie **aucun document officiel de conventions d'assets ou de
nommage**. Les pages `stakeengine.github.io` et `stake-engine.com/docs` n'ont pas
pu être consultées lors de cette revue. Tout ce qui n'est pas [CONTRAT STAKE]
ci-dessous est donc une observation ou une décision Gogold, jamais une exigence
Stake.

## 1. Principe fondamental

> Les conventions Stake Engine ont priorité sur les conventions personnalisées
> Gogold lorsqu'une solution officielle existe déjà. **[CONVENTION GOGOLD]**

> Avant de créer un nouveau dossier, format, système d'événements ou pipeline
> d'assets, vérifier si le Stake Web SDK fournit déjà une solution adaptée.
> **[CONVENTION GOGOLD]**

Toute divergence assumée vis-à-vis de Stake doit être consignée dans
`docs/decisions/` (ADR). **[CONVENTION GOGOLD]**

## 2. Structure des assets runtime — **[PATTERN SAMPLE]**

Structure identique dans les trois sample games vérifiés (`lines`, `cluster`,
`ways`). Aucune documentation Stake ne la déclare obligatoire.

> Structure de référence Gogold, reprise des sample games officiels Stake
> actuellement vérifiés.

```text
apps/<game>/
└── static/
    └── assets/
        ├── audio/
        ├── fonts/
        ├── spines/
        └── sprites/
```

Un **runtime asset** est un fichier réellement chargé par le jeu lorsque le
joueur lance la slot : `symbolsStatic.webp`, `background.webp`, `sounds.json`.

**[CONVENTION GOGOLD]** Ne pas créer de catégories principales concurrentes
tant que ces quatre dossiers suffisent :

```text
images/ graphics/ textures/  → utiliser sprites/
animations/                  → utiliser spines/ ou sprites/
sounds/                      → utiliser audio/
```

## 3. Convention générale : camelCase — **[PATTERN SAMPLE]** → **[CONVENTION GOGOLD]**

Les sample games utilisent majoritairement le **camelCase** pour les noms
fonctionnels d'assets et de dossiers. Gogold adopte cette convention pour ses
propres assets.

Le camelCase colle les mots sans espace, avec une majuscule au début de chaque
mot sauf le premier :

```text
board frame → boardFrame          free spins → freeSpins
scatter landing → scatterLand      barrel fill → barrelFill
free spins intro → freeSpinsIntro
```

Exemples réels observés : `freeSpins`, `payFrame`, `reelsFrame`,
`symbolsStatic`, `pressToContinueText`, `winSmall`, `progressBar`, `goldFont`.

**[CONVENTION GOGOLD]** Pas d'espace ; pas d'accent (`é`, `à`, `ç`…) ; pas de
caractères spéciaux inutiles ; nom court mais explicite ; le nom explique **ce
que l'asset est** ou **ce qu'il fait**.

**Le camelCase n'est pas universel chez Stake.** On trouve aussi `bigwin`,
`reelhouse`, `tumble_win`, `m1_2x.png`, `W.json`, `S.json`. Ce n'est donc pas
une règle Stake, mais un usage dominant. Gogold l'applique à **ses nouveaux
assets** et ne renomme **jamais** un asset ou un fichier venant de Stake
(voir section 12).

## 4. Symboles

⚠️ Il existe **deux couches distinctes**. Ne pas les confondre.

### 4.1 — Identifiant math — **[CONTRAT STAKE]**

L'identifiant vient du Math/RGS et apparaît dans les books, les bookEvents et
`config.ts`. Dans `apps/lines`, les identifiants observés sont :

```text
H1 H2 H3 H4 H5   high-paying      W   wild
L1 L2 L3 L4      low-paying       S   scatter        M   multiplicateur
```

> **Les IDs provenant du Math/RGS doivent être conservés exactement.**

Ils ne se renomment pas, ne se traduisent pas, ne se « rendent pas plus
lisibles ». C'est le contrat entre le math et le frontend.

Le **nombre** de symboles dépend entièrement du jeu. `H1..H5` / `L1..L4` est ce
qu'utilise `lines`, ce n'est pas un quota Gogold. Seule la forme (`H` + rang,
`L` + rang) est commune.

### 4.2 — Noms de fichiers et frames graphiques — **[PATTERN SAMPLE]**

⚠️ **Il n'existe aucune règle mécanique reliant l'ID math au nom du fichier.**

Preuve, dans le seul jeu `apps/lines` :

| ID math | Skeleton Spine | Frame(s) d'atlas |
| --- | --- | --- |
| `H1` | `spines/symbols/h1.json` | `h1.webp` |
| `L1` | `spines/symbols/l1.json` | `l1.webp` |
| `W` | `spines/symbols3/`**`W.json`** | `w.png`, `explodedW.png` |
| `S` | `spines/symbols2/`**`S.json`** | `s.png` |
| `M` | `spines/symbols2/`**`M.json`** | `m1_2x.png`, `m2_5x.png`, `m3_10x.png` |

Le même symbole `W` est donc écrit `W.json` côté Spine et `w.png` côté atlas.
Et `M` ne correspond à aucun fichier `m.png` : les frames décrivent des
multiplicateurs distincts (`m1_2x`, `m2_5x`…).

> Les noms de fichiers et frames graphiques suivent le mapping du frontend et
> les conventions du Web SDK ; ils **ne sont pas nécessairement** une simple
> version minuscule de l'ID math.

Le lien ID → asset est **déclaré explicitement** dans `src/game/assets.ts`.
C'est ce mapping qui fait autorité, pas une règle de casse.

### 4.3 — Ce que Gogold décide — **[CONVENTION GOGOLD]**

- conserver les IDs math exactement tels que fournis par le math ;
- pour les nouveaux assets graphiques, s'aligner sur les noms des sample games
  quand ils existent (`h1`, `l1`, `w`, `s`) — par cohérence, pas par obligation ;
- garder le mapping cohérent et lisible dans `assets.ts` ;
- éviter les noms ambigus ou porteurs d'historique :

```text
HighSymbol1   SymboleHigh1   H1_Final   scatterNEW   symbole1.webp
```

**Aucun nom n'est « interdit par Stake ».** `wild.webp` ou `scatter.webp`
fonctionneraient techniquement ; Gogold leur préfère `w` / `s` pour rester
aligné sur les sample games et sur les IDs math. C'est un choix d'équipe,
révisable, pas une contrainte de plateforme.

## 5. États d'un asset — **[CONVENTION GOGOLD]**

Quand un élément possède plusieurs états, suffixer le nom de base —
`<nom><Etat>` :

```text
boardFrame → boardFrameActive        scatter → scatterActive
background → backgroundFreeSpins     barrel  → barrelFull
```

L'élément de base reste au début du nom : tous ses états se regroupent
naturellement dans un tri alphabétique.

À éviter — noms de production :

```text
boardFrameV2   boardFrameNew   boardFrameFinal   boardFrameOK
```

Ces noms décrivent l'historique de fabrication, pas l'état du jeu.

## 6. Animations — **[CONVENTION GOGOLD]**

Le nom décrit **l'action ou l'état**, jamais l'historique du fichier :

```text
scatterLand  scatterWin  scatterActivate      h1Land  h1Win
wildLand     wildWin                          barrelFill  barrelComplete
freeSpinsIntro  freeSpinsOutro
```

À éviter : `animation1`, `animation2`, `testAnimation`, `scatterNew`,
`scatterFinal`.

Si quelqu'un doit ouvrir le fichier pour savoir ce qu'il contient, le nom est
mauvais.

## 7. Spritesheets — **[PATTERN SAMPLE]**

Observé dans `apps/lines/static/assets/sprites/symbolsStatic/` :

```text
sprites/
└── symbolsStatic/
    ├── index.ts
    ├── symbolsStatic.json
    ├── symbolsStatic.webp
    └── symbolsStatic.png
```

> Dans les sample games, le dossier de spritesheet et ses fichiers partagent le
> même nom de base. Gogold reprend ce pattern.

`sprites/` contient un sous-dossier par spritesheet, en camelCase (observé :
`coin`, `freeSpins`, `payFrame`, `pressToContinueText`, `progressBar`,
`reelsFrame`, `symbolsStatic`, `winSmall`).

### WebP et PNG

⚠️ Ne pas décrire le `.png` comme un « fallback automatique » : **rien ne le
démontre**. Le fichier `index.ts` officiel de `symbolsStatic` importe
uniquement le WebP :

```ts
import img from './symbolsStatic.webp';
import atlas from './symbolsStatic.json';
```

> Les exemples Stake peuvent contenir plusieurs représentations d'un atlas,
> notamment WebP et PNG. **Le format réellement consommé est déterminé par le
> code d'import du jeu**, pas par la présence du fichier dans le dossier.

Le rôle exact du `.png` (source, export intermédiaire, ou repli manuel) sera
tranché à l'étape pipeline d'assets.

## 8. TexturePacker — **[PATTERN SAMPLE]**

Les atlas des sample games sont générés avec **TexturePacker** — visible dans le
champ `meta.app` de `symbolsStatic.json` :
`"app": "https://www.codeandweb.com/texturepacker"`.

**Stake n'exige pas TexturePacker** : aucune documentation officielle ne
l'impose. Ce qui compte est le **format d'atlas consommé par le frontend**.

> **[CONVENTION GOGOLD]** Gogold peut utiliser TexturePacker afin de produire
> des atlas compatibles avec le format attendu par le frontend Stake.

Le pipeline lui-même (presets, `.tps`, scripts, automatisation) sera traité dans
une étape ultérieure. Rien n'est configuré à ce stade.

## 9. Spine — **[PATTERN SAMPLE]**

Destination observée : `static/assets/spines/`. Pattern dans
`apps/lines/static/assets/spines/symbols/` :

```text
spines/
└── symbols/
    ├── index.ts
    ├── symbols.atlas
    ├── symbols.webp
    ├── symbols.png
    ├── h1.json … h5.json      (un skeleton par symbole)
    └── l1.json … l4.json
```

Le dossier et l'atlas partagent le même nom de base ; les skeletons `.json`
portent le nom de l'élément animé. Attention : la casse de ces skeletons **suit
l'ID math et non le camelCase** (`W.json`, `S.json`, `M.json` — voir 4.2).

Un sous-dossier par animation, en camelCase (observé : `anticipation`,
`bonusButton`, `clusterWin`, `fsIntro`, `globalMultiplier`, `loader`,
`transition`, `tumbleWin`, `winMeterExplosion`).

### Spine ou spritesheet — **[CONTRAT STAKE]** (documenté)

Le README officiel du Web SDK indique explicitement, à propos des animations :

> « Spritesheet animation is a good alternative. »

Les deux approches sont donc supportées. **Ni l'une ni l'autre n'est
obligatoire.**

> **[CONVENTION GOGOLD]** Choisir la technique selon le besoin réel : une
> spritesheet suffit souvent pour une animation simple ; Spine se justifie pour
> les animations complexes, déformables, ou réutilisant un même squelette avec
> plusieurs skins.

## 10. Fonts — **[PATTERN SAMPLE]**

Destination observée : `static/assets/fonts/`, avec un sous-dossier par police
en camelCase (`goldFont`, `goldBlur`, `silverFont`, `purpleFont`).

Les sample games utilisent des **polices bitmap** (définition + texture) plutôt
que des polices web classiques. Le format exact retenu par Gogold sera confirmé
à l'intégration du Web SDK.

## 11. Audio — **[PATTERN SAMPLE]**

Destination observée : `static/assets/audio/`.

Le dossier audio est **plat** dans les deux jeux vérifiés (`lines` et `ways`),
avec un contenu identique :

```text
sounds.json  sounds.mp3  sounds.ogg  sounds.m4a  sounds.ac3
```

C'est un **audio sprite** : tous les sons sont regroupés dans un seul fichier,
décliné en plusieurs formats pour la compatibilité navigateur ; `sounds.json`
décrit où commence et où finit chaque son. Le package `utils-sound` du Web SDK
repose sur **Howler**, qui gère nativement ce mécanisme.

Aucune documentation Stake ne déclare cette organisation obligatoire : c'est un
pattern cohérent, pas une exigence de plateforme.

> **[CONVENTION GOGOLD]** Gogold reprend `static/assets/audio/` et le principe
> d'audio sprite. Ne pas créer `audio/music/`, `audio/sfx/`, `audio/voice/`
> tant que l'audio sprite rend ces dossiers inutiles.

- la séparation BGM / SFX / ambiance / voix est **logique** (déclarée dans
  `sounds.json` et gérée par `utils-sound`), pas **physique** ;
- les noms des sons dans `sounds.json` suivent le camelCase.

### Formats audio

Aucune source officielle Stake n'interdit un format particulier. Les sample
games utilisent `mp3`, `ogg`, `m4a`, `ac3` — le WAV en est simplement absent.

> **[CONVENTION GOGOLD]** `CLAUDE.md` proscrit le WAV en runtime (poids). Cette
> règle est une décision Gogold, pas une contrainte Stake. Les formats runtime
> définitifs seront arrêtés pendant l'étape dédiée au pipeline d'assets, en
> suivant les formats réellement utilisés et supportés par le Web SDK.

Aucun système audio n'est développé à ce stade.

## 12. Technical naming — code et événements

### Architecture d'événements — **[CONTRAT STAKE]**

Documentée dans le README officiel du Web SDK :

```text
bookEvent  →  bookEventHandlerMap  →  emitterEvent  →  eventEmitter
```

- un **bookEvent** est un élément du tableau `book.events` renvoyé par le RGS ;
- **bookEventHandlerMap** associe un `bookEvent.type` à un `bookEventHandler` ;
- un handler diffuse un ou plusieurs **emitterEvents** via `eventEmitter` ;
- les composants s'y abonnent avec `eventEmitter.subscribeOnMount()`.

> **[CONVENTION GOGOLD]** Ne créer **aucun système d'événements parallèle**.
> Conserver les concepts et les noms Stake existants.

> **[CONVENTION GOGOLD]** Un événement Gogold personnalisé n'est créé que
> lorsqu'une vraie mécanique de jeu le nécessite et qu'aucun événement Stake
> existant ne répond au besoin. Il suivra le style de nommage Stake.

Aucun événement n'est créé à ce stade — ni `spinStart`, ni `cascade`, ni
`barrelFill`, ni quoi que ce soit « au cas où ».

### Fichiers de code — **[PATTERN SAMPLE]**

Observé dans `apps/lines/src/` :

```text
.ts       camelCase     typesBookEvent.ts  bookEventHandlerMap.ts
                        stateApp.ts  stateLayout.ts  assets.ts  config.ts
.svelte   PascalCase    Game.svelte  Board.svelte  BoardFrame.svelte
```

Ce sont des usages dominants, avec des exceptions dans le repo lui-même
(`stateGame.svelte.ts`, ou les skeletons `W.json` / `S.json`). Ne pas les
transformer en règle universelle.

> **[CONVENTION GOGOLD]** Le code provenant de Stake, ou directement basé sur
> une structure Stake, **conserve sa convention existante**. Ne jamais renommer
> automatiquement du code Stake : la documentation officielle doit rester
> directement applicable à notre codebase.

## 13. Versioning des assets — **[CONVENTION GOGOLD]**

Le nom d'un fichier n'est **pas** un système de versioning. À proscrire dans les
assets runtime :

```text
final  final2  new  new2  latest  ok  test  v2  v3  v4

✗ boardFrameFinal2.webp        ✓ boardFrame.webp
```

**Git gère l'historique des versions.** Quand un asset est remplacé, on écrase
le fichier et on commit : l'ancienne version reste dans l'historique.

Un fichier nommé `Final2` finit toujours par être suivi d'un `Final3`.

## 14. Sources artistiques vs assets runtime — **[CONVENTION GOGOLD]**

> Les fichiers sources de production ne doivent pas être mélangés aveuglément
> avec les assets runtime chargés par la slot.

| Fichiers sources (production) | Assets runtime (chargés par le jeu) |
| --- | --- |
| `.psd`, `.aep` | images consommées par le code (WebP dans les samples) |
| fichiers de travail | `.json` (atlas, sounds) |
| images IA brutes | `.atlas` / skeletons Spine |
| masters très haute résolution | audio optimisé (mp3, ogg, m4a, ac3) |
| frames intermédiaires | atlas utilisé par le frontend |

Seuls les assets runtime vivent dans `apps/<game>/static/assets/`.

L'emplacement définitif des fichiers sources artistiques **n'est pas décidé
ici** : il sera traité avec le pipeline d'assets, dans une étape ultérieure.

Rappel : les assets binaires ne sont pas versionnés dans Git (voir `.gitignore`
et `CLAUDE.md`).

## 15. Dimensions d'export — **[CONVENTION GOGOLD]**

**Aucune dimension d'export n'est fixée à ce stade.** Cette décision dépendra du
frontend Stake réellement intégré, du sample utilisé, des spritesheets, de
TexturePacker, des performances, du poids final du frontend et du responsive.

Seule règle posée aujourd'hui :

> **MASTER ASSET ≠ RUNTIME ASSET**

Un master artistique peut avoir une résolution beaucoup plus élevée que la
version utilisée par le jeu. Produire en haute résolution est une bonne
pratique ; livrer la haute résolution au joueur ne l'est pas.

## 16. Checklist avant d'ajouter un asset

- [ ] Le nom est en camelCase, sans espace ni accent. *(Gogold)*
- [ ] Le nom décrit ce que l'asset est ou fait, pas son historique. *(Gogold)*
- [ ] Aucun `final`, `new`, `v2`, `test`, `ok` dans le nom. *(Gogold)*
- [ ] S'il s'agit d'un symbole : l'**ID math** est conservé exactement, et le
      mapping ID → fichier est déclaré dans `assets.ts`. *(Contrat)*
- [ ] L'asset est dans `audio/`, `fonts/`, `spines/` ou `sprites/`. *(Pattern)*
- [ ] Pour une spritesheet ou un spine : le dossier et les fichiers partagent le
      même nom de base. *(Pattern)*
- [ ] C'est un asset runtime, pas un fichier source de production. *(Gogold)*
- [ ] Le format est bien celui réellement importé par le code. *(Pattern)*
- [ ] Stake ne fournit pas déjà cet asset ou cette solution. *(Gogold)*

## Ce que ce document ne fait PAS

Il ne crée aucun asset, aucune arborescence de jeu, aucun pipeline, aucun preset
TexturePacker, aucun événement et aucun code. Il ne fixe pas les dimensions
d'export ni l'emplacement des sources artistiques.

Il n'invente aucune obligation Stake : tout ce qui n'est pas marqué
**[CONTRAT STAKE]** est une observation ou une décision Gogold, révisable.

Il définit les règles ; leur mise en œuvre viendra avec l'intégration du Web SDK
Stake Engine.
