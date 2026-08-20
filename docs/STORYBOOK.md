# Gogold Storybook Lab

Le laboratoire visuel de Gogold. Tester un symbole, un état, un book ou un
bookEvent en quelques secondes — sans lancer de partie, sans RGS.

Storybook n'est pas un outil que nous avons construit : **il vient du Stake Web
SDK** intégré en A8. Ce document explique comment nous l'utilisons et ce que
chaque jeu Gogold devra fournir.

---

## Purpose

```text
un asset intégré  → on le voit tout de suite
un état de symbole → on le compare aux autres
un bookEvent       → on le rejoue isolément, autant de fois qu'on veut
```

**Storybook est le premier outil de debug visuel.** Avant d'écrire un outil
Gogold pour observer une animation ou un événement :

1. vérifier si Storybook peut déjà le faire ;
2. ajouter une story si nécessaire ;
3. seulement ensuite envisager autre chose.

---

## Stake foundation

```text
Storybook              9.0.15 (sveltekit)
baseline Web SDK       1843d60c… (voir FRONTEND.md)
config partagée        packages/config-storybook       main.ts + preview.ts
composants de story    packages/components-storybook   StoryPixiApp, StoryGameTemplate,
                                                       StoryLocale, StoryEventEmitter
stories du sample      apps/lines/src/stories/
fixtures locales       apps/lines/src/stories/data/    base_books, base_events,
                                                       bonus_books, bonus_events
```

`config-storybook/main.ts` collecte `../src/**/*.stories.@(js|ts|svelte)` — les
stories vivent donc dans le `src/` de chaque app, jamais dans un dossier central.

---

## Launch Storybook

```powershell
pnpm run storybook --filter=lines
```

→ <http://localhost:6001>

Une seule commande, aucune variable d'environnement à poser à la main (voir
*Windows compatibility*).

> **Premier démarrage lent.** Stake documente que l'initialisation sous Windows
> peut prendre plusieurs minutes, parfois beaucoup plus. Une fois chargé, le
> passage d'une story à l'autre et le hot reload sont rapides. C'est un coût
> unique par session : garder Storybook ouvert.

---

## Story categories

Inventaire réel du sample `lines` — **23 stories**.

### Game

`COMPONENTS/<Game>` — le jeu complet dans son contexte.

| Story | Ce qu'elle montre |
| --- | --- |
| `component (loadingScreen)` | l'écran de chargement |
| `preSpin` | l'état juste avant le spin |
| `emitterEvent: boardHide` | un emitterEvent déclenché isolément |

### Symbol

`Components/<Symbol>` — le laboratoire des symboles.

| Story | Ce qu'elle montre |
| --- | --- |
| `component` | un symbole isolé, réglable via les *args* Storybook |
| `symbols` | **la galerie complète** : chaque symbole × chaque état |

La galerie boucle sur `SYMBOL_STATES` (`src/game/types.ts`) — dans `lines` :

```text
static   spin   land   win   postWinStatic   explosion
```

C'est la story que l'Art/Integration ouvre en premier. Ne pas construire une
deuxième galerie : celle-ci existe et suit automatiquement le jeu.

### Book

`MODE_BASE/book/random` et `MODE_BONUS/book/random`.

Rejouent un book complet tiré au hasard dans les fixtures locales. Aucune
connexion RGS.

### BookEvent

`MODE_BASE/bookEvent/*` et `MODE_BONUS/bookEvent/*` — 8 events chacun :

```text
reveal   setTotalWin   freeSpinTrigger   updateFreeSpin
winInfo  setWin        freeSpinEnd       finalWin
```

Chaque story rejoue **un seul** bookEvent via `playBookEvent`, le chemin de
production.

### UI

**Aucune story de bouton, compteur ou panneau UI n'existe** — ni dans
`apps/lines`, ni dans `components-ui-pixi`, ni dans `components-ui-html`.

C'est un manque constaté, pas un problème à régler tout de suite. Nous créerons
une story quand un composant Gogold réel demandera une validation isolée. Pas de
catalogue exhaustif construit à l'avance.

### Le second laboratoire — primitives PixiJS

`packages/pixi-svelte-storybook` contient **35 stories** couvrant les primitives :
`Sprite`, `SpriteSheet (AnimatedSprite)`, `Text`, `BitmapText`, `Container`,
`Graphics`, `Particle`, `ParticleEmitter`, `ReverseMask`, et **10 stories Spine**
(SpineProvider, Tracks, Events, Physics, BoneControl, MeshSequence…).

> ⚠️ **Ce Storybook ne démarre pas dans notre baseline** :
>
> ```text
> Error: Failed to load static files, no such directory: .\static
> ```
>
> `config-storybook` déclare `staticDirs: ['../static']`, or ce package n'a pas
> de dossier `static/`. **Le défaut est upstream** — vérifié, le dépôt Stake ne
> contient pas ce dossier non plus.
>
> Contournement vérifié (35 stories servies en HTTP 200) :
>
> ```powershell
> mkdir packages\pixi-svelte-storybook\static
> pnpm run storybook --filter=pixi-svelte-storybook   # → port 6006
> ```
>
> Non appliqué : cela modifierait un package Stake. Les fichiers de stories
> restent utilisables comme **référence de code** pour apprendre les primitives.

---

## Art / Integration workflow

Objectif : **une commande, puis uniquement de l'observation.** Aucun code à
modifier.

```text
pnpm run storybook --filter=<jeu>
        ↓
Components/<Symbol> → symbols
        ↓
tous les symboles × tous les états s'affichent côte à côte
        ↓
contrôle visuel (voir checklist)
```

Pour un événement animé :

```text
MODE_BASE/bookEvent → choisir l'event (ex. reveal)
        ↓
bouton « Action » en bas à droite du canvas
        ↓
l'animation se joue
        ↓
recliquer pour rejouer autant de fois que nécessaire
```

Le bouton **Action** est le déclencheur fourni par `StoryGameTemplate`. Même
principe pour `MODE_BASE/book/random`, qui joue un round complet.

### Enchaînement avec le pipeline d'assets

Storybook est l'étape de validation visuelle immédiate après l'intégration d'un
asset (voir [`ASSET_PIPELINE.md`](ASSET_PIPELINE.md)) :

```text
MASTER → EXPORT → OPTIMIZE → PACK → CHECK-ASSETS → INTEGRATE
                                                       ↓
                                                   STORYBOOK
                                                       ↓
                                              VALIDATION VISUELLE
                                                       ↓
                                                     BUILD
```

Un asset intégré qui n'a pas été regardé dans Storybook n'est pas validé.

---

## Adding a symbol state

Les états ne sont pas déclarés dans la story mais dans le jeu — la galerie suit
automatiquement.

1. Ajouter l'état à `SYMBOL_STATES` dans `src/game/types.ts`.
2. Déclarer le rendu de cet état dans `SYMBOL_INFO_MAP` (`src/game/constants.ts`)
   pour chaque symbole concerné : `type` (`sprite` ou `spine`), `assetKey`,
   `animationName`, `sizeRatios`.
3. Rouvrir `Components/<Symbol> → symbols` : la colonne apparaît.

Aucune modification de fichier `.stories.svelte` n'est nécessaire.

---

## Adding a BookEvent story

L'ordre est imposé par le contrat math ↔ frontend. **Ne jamais l'inverser.**

```text
1. Math produit le bookEvent          (math/ — Math SDK)
2. Frontend type le bookEvent          src/game/typesBookEvent.ts
3. Handler                             src/game/bookEventHandlerMap.ts
4. emitterEvent                        src/game/eventEmitter.ts
5. Composant qui réagit                src/components/
6. Story isolée                        src/stories/Mode<Mode>BookEvent.stories.svelte
```

Pour l'étape 6, suivre le pattern existant :

```svelte
<Story
    name="<nomDeLEvent>"
    args={templateArgs({
        skipLoadingScreen: true,
        data: events.<nomDeLEvent>,
        action: async (data) => await playBookEvent(data, { bookEvents: [] }),
    })}
    {template}
/>
```

avec la fixture correspondante dans `src/stories/data/<mode>_events.ts`.

> **La story doit passer par `playBookEvent`**, qui est construit sur
> `bookEventHandlerMap` (`createPlayBookUtils` de `utils-book`). C'est le chemin
> de production. Ne jamais créer une seconde API de test qui court-circuite le
> handler : on validerait alors du code que le jeu n'exécute pas.

---

## What belongs in Storybook

```text
symboles et leurs états
animations et transitions
assets (texture, atlas, Spine, font)
books complets rejoués depuis des fixtures locales
bookEvents isolés
composants visuels isolés
```

Tout doit fonctionner **sans** `sessionID`, token, ni RGS.

---

## What does NOT belong in Storybook

```text
recalcul d'un gain            ← le gain vient du book
RNG frontend                  ← aucun tirage côté client
simulation math               ← c'est le rôle de math/
probabilités                  ← jamais exposées au frontend
```

Les fixtures Storybook **représentent** le contrat math, elles ne le
reproduisent pas.

### Storybook ≠ Debug Panel (A12)

Deux outils, deux responsabilités. Le futur Debug Panel ne doit pas dupliquer
Storybook.

| Storybook | Debug Panel (A12) |
| --- | --- |
| composants isolés | diagnostic d'une partie complète |
| assets, états | scénarios forcés |
| bookEvent unitaire | informations runtime |

---

## Visual QA checklist

Critères Gogold de validation visuelle d'un symbole. **[CONVENTION GOGOLD]** —
ce ne sont pas des exigences Stake.

- [ ] l'asset affiché est le bon
- [ ] aucune texture manquante (pas de carré blanc / magenta)
- [ ] taille relative cohérente avec les autres symboles
- [ ] centrage correct dans la cellule
- [ ] pivot correct (l'animation ne part pas de travers)
- [ ] aucun saut entre deux états
- [ ] pas de clipping / rognage en bord de cellule
- [ ] alpha propre, pas de frange sombre
- [ ] animation fluide, sans à-coup
- [ ] pas de halo d'atlas (bleeding d'un sprite voisin)
- [ ] lisible en petit (mobile)
- [ ] lisible en grand (desktop)

Pour une story de bookEvent :

- [ ] l'événement démarre
- [ ] l'animation attendue apparaît
- [ ] la story se termine (la promise se résout)
- [ ] aucun événement ne reste bloqué
- [ ] l'état visuel final est correct
- [ ] l'événement peut être rejoué via « Action »

---

## Windows compatibility

### Le problème

Le script upstream utilise la syntaxe POSIX d'affectation de variable, que
`cmd.exe` ne comprend pas :

```text
Stake baseline :
"storybook": "PUBLIC_CHROMATIC=true storybook dev -p 6001 public"

→ 'PUBLIC_CHROMATIC' n'est pas reconnu en tant que commande interne ou externe
```

### La solution — recommandée par Stake

Le README du Web SDK documente lui-même le correctif :

> *« For Windows users, you might need to add the script with "cross-env" to make
> it work »*

```text
Gogold Windows compatibility :
"storybook": "cross-env PUBLIC_CHROMATIC=true storybook dev -p 6001 public"
```

### Divergence assumée

```text
fichier   apps/lines/package.json
change    + cross-env devant le script storybook
          + "cross-env": "7.0.3" en devDependency
diff      3 insertions, 2 suppressions
```

C'est la **seule** modification apportée à `apps/lines`. Elle est volontaire,
minimale, et alignée sur la recommandation officielle Stake.

### Reste à faire si besoin

Cinq packages Stake gardent la syntaxe POSIX et échoueraient sous Windows :

```text
components-layout   components-pixi   components-shared
components-ui-html  components-ui-pixi
```

Non corrigés : seul `components-shared` possède des stories (2), et modifier un
package runtime Stake dépasse le périmètre. Le correctif est identique
(`cross-env` devant le script) si l'un d'eux devient nécessaire.

---

## Story coverage requirement for future games

Chaque jeu Gogold devra fournir, **lorsque les composants correspondants existent
réellement** :

| Catégorie | Exigence |
| --- | --- |
| **Game** | le jeu complet + les états importants |
| **Symbol** | un symbole isolé + la galerie complète (tous symboles × tous états implémentés) |
| **Book** | `book/random` du mode de base, + du mode bonus s'il existe |
| **BookEvent** | une story par bookEvent **ayant un effet visuel** |

### Ne pas créer de story artificielle

Storybook reflète le contrat réel du jeu, pas un catalogue théorique.

```text
jeu sans cascade      → pas de story cascade
jeu sans multiplicateur → pas de story multiplier
```

Exemple concret dans `lines` : **9 bookEvents déclarés, 8 stories.** Le neuvième,
`createBonusSnapshot`, restaure l'état lors de la reprise d'un round — il n'a
aucun rendu propre. Une story isolée n'aurait rien à montrer. Couverture correcte :
8/9.

### Definition of Done

> **Un bookEvent à effet visuel n'est pas terminé tant qu'il n'a pas :
> handler implémenté + rendu intégré + story isolée fonctionnelle.**

> **Un symbole n'est pas visuellement intégré tant qu'il n'est pas inspectable
> dans Storybook** avec son rendu `static` et ses états réellement implémentés.

Il ne doit jamais être nécessaire de lancer cinquante spins pour vérifier le
rendu d'un symbole.

---

## Ce que ce document ne fait PAS

Il n'installe aucun Storybook, ne crée aucun composant, ne définit aucun design
system Gogold, et ne configure aucune régression visuelle cloud (Chromatic,
Percy). Le laboratoire est local et sans compte externe.

Il ne couvre pas le pipeline de fabrication des assets
([`ASSET_PIPELINE.md`](ASSET_PIPELINE.md)) ni les conventions de nommage
([`ASSETS.md`](ASSETS.md)).
