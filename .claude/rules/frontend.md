---
paths:
  - "apps/**/*.{ts,svelte}"
  - "apps/**/package.json"
---

# Frontend

Référence détaillée : `docs/FRONTEND.md`, `docs/CONFIGURATION.md`.

## Le frontend ne calcule rien

Le résultat vient du RGS sous forme de book. Le frontend l'anime.

Ne jamais calculer côté client : gain, RTP, reel stops, déclenchement de bonus,
multiplicateur, max win, probabilité. Ne jamais inventer une information Math.

Un effet purement décoratif peut varier localement s'il n'affecte jamais le
résultat ni la séquence.

## Préserver la chaîne Stake

```text
book → bookEvent → bookEventHandlerMap → emitterEvent → composant
```

Ne pas créer un second event bus ni une seconde architecture de replay. Un
handler asynchrone se termine quand son étape visuelle est terminée.

Un nouveau bookEvent part toujours du besoin Math, jamais du frontend :
Math produit l'event → type frontend → handler → emitterEvent si nécessaire →
rendu → story Storybook isolée.

## Réutiliser les primitives Stake

Inspecter avant d'écrire quoi que ce soit :

```text
utils-slots   utils-sound     utils-book      utils-event-emitter
utils-fetcher utils-layout    utils-xstate    utils-bet
components-layout  components-ui-pixi  components-ui-html  components-pixi
pixi-svelte   rgs-fetcher     rgs-requests    state-shared
```

Les noms peuvent changer dans une future baseline : vérifier le repository réel.

Interdits sans besoin démontré : client RGS parallèle, SlotEngine/ReelEngine,
AudioManager, ResponsiveEngine, machine d'état concurrente, chargeur d'assets
maison, bibliothèque UI Gogold.

## Réseau et configuration

`rgs_url`, `sessionID`, bet levels, jurisdiction viennent de la session Stake.
Ne jamais les hardcoder. Respecter les flags de jurisdiction reçus : turbo,
autoplay, fullscreen, buy feature, slam stop, spacebar ne sont pas disponibles
partout.

## État et timing

Utiliser la machine XState existante pour le cycle de jeu. Ne pas piloter le
gameplay avec des chaînes de `setTimeout`. Une animation locale simple peut
utiliser le mécanisme adapté du framework tant qu'elle ne remplace pas la
machine.

## Validation

Un comportement visuel isolable se vérifie dans Storybook (`docs/STORYBOOK.md`),
pas en lançant cinquante spins. Un round complet ou un cas rare se vérifie avec
le Debug Panel (`docs/DEBUG_PANEL.md`).

## Code

Types explicites, API petites, dépendances minimales. Éviter `any` ; le contenir
et le typer immédiatement à une frontière externe. Éviter les casts injustifiés.

Pas de limite absolue de longueur : découper un fichier quand il porte plusieurs
responsabilités, pas pour satisfaire une métrique.
