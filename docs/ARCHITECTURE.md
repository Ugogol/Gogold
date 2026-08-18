# Architecture Gogold

Gogold est un monorepo pnpm + Turborepo qui héberge des jeux de slots HTML5
publiés **exclusivement sur Stake Engine**.

Sa structure suit délibérément celle du Web SDK Stake Engine
(https://github.com/StakeEngine/web-sdk), qui repose sur `apps/*` et
`packages/*` orchestrés par pnpm workspaces et Turborepo.

---

## Règle fondamentale

```text
apps/<game>     = spécifique à un seul jeu
packages/*      = réellement partagé par plusieurs jeux
tooling/*       = outils servant à fabriquer et vérifier les jeux
docs/*          = documentation et standards Gogold
```

---

## `apps/`

Un dossier = un jeu.

```text
apps/
├── grogg/
├── game-002/
└── game-003/
```

Il n'y a **pas** de niveau intermédiaire `apps/games/`. C'est la convention du
Web SDK Stake, dont les jeux de référence (`lines`, `cluster`, `ways`,
`scatter`, `price`) sont placés directement sous `apps/`.

Tout ce qui concerne un seul jeu reste dans son app : configuration, math du
jeu, assets, symboles, écrans, sons, machine à états spécifique.

## `packages/`

Code réellement partagé entre plusieurs jeux.

Un package n'est créé que lorsqu'un besoin de réutilisation est **constaté**,
jamais anticipé.

## `tooling/`

Outils internes de fabrication et de vérification des jeux : validation
d'assets, compression, préparation TexturePacker, contrôles de poids du
frontend, contrôles avant publication Stake, création d'un nouveau jeu.

Ces outils servent à produire les jeux ; ils ne sont jamais embarqués dans le
bundle livré au joueur.

## `docs/`

Documentation d'architecture, standards, décisions.

---

## Séparation GAME / PLATFORM

Avant d'ajouter une fonctionnalité, poser la question :

> Cette fonctionnalité appartient-elle réellement à ce jeu, ou sert-elle à
> plusieurs jeux Gogold ?

**GAME** — spécifique, propre à l'univers, aux règles ou aux visuels d'un jeu.
→ `apps/<game>`

**PLATFORM** — générique, indépendante du thème, utilisable telle quelle par un
autre jeu.
→ `packages/*`

Dans le doute, le code reste dans le jeu. Il est toujours moins coûteux de
promouvoir plus tard du code éprouvé vers `packages/` que de démonter une
abstraction prématurée.

---

## Priorité aux briques Stake Engine

Stake Engine est la **référence technique principale** du projet.

Avant d'écrire une technologie Gogold, vérifier systématiquement si le Web SDK
Stake fournit déjà une solution adaptée : `utils-book`, `utils-fetcher`,
`utils-slots`, `utils-layout`, `utils-sound`, `utils-xstate`, `pixi-svelte`,
`components-ui-*`, `config-*`, `state-*`.

Interdictions :

- recréer une fonctionnalité déjà fournie par Stake Engine ;
- diverger de leurs conventions sans raison technique forte et documentée ;
- réécrire le rendu en PixiJS impératif : le SDK impose le modèle déclaratif
  `pixi-svelte`.

Toute divergence assumée vis-à-vis du Web SDK Stake doit être consignée dans
`docs/decisions/` au format ADR.

Divergence actuellement assumée : ajout de `tooling/*` au workspace pnpm. Le
Web SDK Stake ne déclare que `apps/*` et `packages/*` ; `tooling/` accueille
nos outils internes, qui ne sont pas du code de jeu et n'ont pas d'équivalent
amont.

---

## Interdiction d'abstraction prématurée

> Une abstraction n'est pas créée parce qu'elle pourrait être réutilisable.
> Elle est créée lorsqu'un besoin réel de réutilisation apparaît.

Concrètement : aucun package "moteur" n'est créé tant qu'un seul jeu existe.
La bonne frontière entre GAME et PLATFORM ne se devine pas — elle se découvre
en construisant le deuxième jeu.

---

## Rappel plateforme

Stake Engine fonctionne en modèle **précalculé** : le RGS renvoie un `book`
(séquence d'events) déjà décidé, et le frontend se contente de le rejouer.

Le frontend ne calcule jamais un gain, ne décide jamais d'un bonus, et ne
génère jamais d'aléa de jeu. Cette contrainte structure l'ensemble de
l'architecture.
