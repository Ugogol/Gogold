# Gogold Frontend Foundation

Registre de la fondation frontend Gogold, issue du **Stake Web SDK officiel**.

Ce document n'explique pas comment fonctionne le Web SDK — il enregistre **quelle
version nous avons intégrée, ce qu'elle fournit, et comment le vérifier**.

## Stake Web SDK baseline

```text
Upstream            : https://github.com/StakeEngine/web-sdk
Integrated commit   : 1843d60cedb94b390e641b563f32ad64353bec5e
Commit message      : remove dev tools error
Commit date         : 2025-11-28
Date d'intégration  : 2026-08-19 (étape A8)
```

L'intégration est une **copie de code**, pas un submodule ni un subtree. Le Web
SDK est notre base de code, que nous ferons évoluer volontairement.

Aucun mécanisme de synchronisation automatique n'existe : la stratégie de mise à
jour du SDK sera décidée ultérieurement. Le hash ci-dessus est la référence pour
tout futur diff avec une nouvelle version Stake.

## Packages importés

29 packages, copiés tels quels depuis `web-sdk/packages/`.

| Catégorie | Packages |
| --- | --- |
| **config** | `config-lingui`, `config-storybook`, `config-svelte`, `config-ts`, `config-vite`, `eslint-config-custom` |
| **state / constants** | `state-shared`, `constants-shared`, `envs` |
| **utils** | `utils-bet`, `utils-book`, `utils-event-emitter`, `utils-fetcher`, `utils-layout`, `utils-resize-observer`, `utils-shared`, `utils-slots`, `utils-sound`, `utils-xstate` |
| **components** | `components-layout`, `components-pixi`, `components-shared`, `components-storybook`, `components-ui-html`, `components-ui-pixi` |
| **pixi** | `pixi-svelte`, `pixi-svelte-storybook` |
| **rgs** | `rgs-fetcher`, `rgs-requests` |

Tous les packages officiels ont été conservés : préserver le fonctionnement
cohérent du SDK prime sur une réduction prématurée.

## Application de référence

```text
apps/lines
```

Sample officiel Stake, copié **sans aucune modification fonctionnelle**.

> **Ce n'est pas un jeu Gogold.** C'est un sample technique servant de smoke test
> pour vérifier que l'installation, le build et Storybook fonctionnent.

Il ne doit pas être renommé, rebrandé, ni transformé en jeu Gogold. `apps/grogg/`
reste un placeholder vide et distinct.

## Ce que Stake fournit déjà

À ne **jamais** réimplémenter côté Gogold.

| Domaine | Où |
| --- | --- |
| **Communication RGS** | `rgs-requests` (authenticate, play, end-round, balance…), `rgs-fetcher` (transport + schéma), `utils-fetcher` |
| **Reels / slots** | `utils-slots` — `createReelForSpinning`, `createReelForCascading`, `createEnhanceBoard*`, `stateSlots` |
| **Audio** | `utils-sound` (Howler) — `createPlayer`, `createPlayMusic`, `createPlayLoop`, `createPlayOnce` |
| **Chargement d'assets** | `stateApp` + `PIXI.Assets.load`, déclaré par jeu dans `src/game/assets.ts` |
| **Responsive / layout** | `utils-layout` (`createLayout`, contexte), `components-layout` |
| **State machine** | `utils-xstate` — `createGameActor`, machines bet / autoBet / resumeBet |
| **UI** | `components-ui-pixi` (boutons bet, balance, autospin, turbo, buy bonus, réglages, paytable, layouts desktop/tablet/portrait/landscape, `UIReplay`), `components-ui-html` (modales, menus, bonus cards) |
| **Book events** | `utils-book`, `utils-event-emitter` ; par jeu : `typesBookEvent.ts`, `bookEventHandlerMap.ts` |
| **Storybook** | `config-storybook`, `components-storybook`, `pixi-svelte-storybook` ; stories du sample dans `apps/lines/src/stories/` |
| **Rendu déclaratif** | `pixi-svelte` |
| **i18n** | `config-lingui`, `stateI18n` |

Détail des primitives math et de leur contrepartie frontend : `docs/MECHANICS.md`.
Sources de vérité des données : `docs/CONFIGURATION.md`.

## Règle Gogold

> **Stake first — aucune infrastructure dupliquée.**

Aucun client RGS, moteur de reels, moteur audio, chargeur d'assets, moteur
responsive, state machine ou bibliothèque UI Gogold n'a été créé. Ces briques
existent déjà ci-dessus.

Avant d'écrire quoi que ce soit, vérifier qu'aucun package de la liste ne le fait
déjà. Les critères justifiant une future abstraction Gogold sont dans
`docs/MECHANICS.md` §19.

## Modèle de build

`config-svelte` utilise `@sveltejs/adapter-static` avec
`output.bundleStrategy: 'inline'`. Le build produit un **site statique**,
conforme au modèle de publication Stake.

Sortie de `apps/lines` après build :

```text
apps/lines/build/
├── index.html
├── _app/            (env.js, immutable/, version.json)
├── assets/
├── favicon.svg
├── loader.gif
└── stake-engine-loader.gif
```

C'est ce dossier qui constitue le frontend statique à publier sur Stake. Aucun
serveur Node runtime, aucune API Gogold, aucun backend n'est requis.

## Commandes de vérification

```bash
pnpm install
pnpm run build --filter=lines        # → apps/lines/build/
pnpm run lint --filter=lines
pnpm run storybook --filter=lines    # serveur interactif, port 6001
pnpm run dev --filter=lines          # serveur de dev, port 3001
```

## Points de vigilance connus

### ⚠️ Le chemin du repository ne doit pas contenir de `#`

Le build échoue si le chemin absolu du repository contient un caractère `#` :

```text
Failed to resolve entry for package "config-vite"
```

Cause : Vite/esbuild résolvent les modules via des URLs `file://`, où `#`
introduit un fragment. Le chemin `C:\Users\ugooo\Documents\#GOGOLD\Gogold`
devient `file:///C:/Users/ugooo/Documents/%23GOGOLD/Gogold` et la résolution des
packages du workspace casse.

Vérifié : le **même contenu** placé dans un chemin sans `#` build correctement.
Ce n'est ni un défaut du SDK, ni un défaut de l'intégration.

**Correctif** : héberger le repository dans un chemin sans `#`.

### ⚠️ `lint` échoue en amont (défaut upstream)

```text
From ESLint v9.0.0, the default configuration file is now eslint.config.js.
```

Le SDK épingle `eslint@9.21.0` mais utilise encore le format legacy
`.eslintrc.cjs`. **Le même échec se produit dans le clone upstream intact.**

Non corrigé volontairement : rester aligné sur l'upstream prime à ce stade. À
traiter avec Stake ou lors d'une étape de personnalisation.

### ⚠️ Storybook démarre avec des warnings (défauts upstream)

Storybook 9.0.15 démarre correctement, mais signale :

```text
# à l'installation
@chromatic-com/storybook 3.2.5
└── unmet peer storybook@"^8.x": found 9.0.15

# au démarrage
@storybook/addon-svelte-csf@5.0.5 which depends on ^0.1.13   (incompatible)
CSF Parsing error: Expected 'ObjectExpression' but found 'undefined' …
```

**Vérifié : le clone upstream intact produit exactement les mêmes warnings**
(mêmes versions épinglées, mêmes fichiers de stories). Ce ne sont pas des effets
de l'intégration Gogold.

Sans effet sur l'installation (exit 0) ni sur le démarrage du serveur. À
réévaluer lors d'une future mise à jour du SDK.

### ⚠️ Police externe dans le sample

`apps/lines/src/app.html` charge `https://use.typekit.net/aba0ebl.css` — un CDN
externe. C'est du code upstream, laissé intact.

Un jeu Gogold ne devra pas reprendre cette dépendance externe : le build doit
rester autonome.

## Ce que cette fondation ne fait PAS

Elle ne contient aucun jeu Gogold, aucun branding, aucune optimisation de poids,
aucun pipeline de publication, aucun Math SDK, et aucune couche Gogold au-dessus
de Stake.

`apps/lines` est un outil de vérification, pas un produit.
