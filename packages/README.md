# Gogold Packages

Ce dossier contient exclusivement du code réutilisable entre plusieurs jeux Gogold.

**Statut : vide.** Aucun package n'existe encore, et c'est volontaire.

## Règle

Si un élément est spécifique à un seul jeu, il reste dans `apps/<game>`.

Si un élément peut réellement être utilisé par plusieurs jeux, il peut devenir
un package Gogold.

Ne pas extraire prématurément du code uniquement parce qu'il semble
potentiellement réutilisable.

> Une abstraction n'est pas créée parce qu'elle pourrait être réutilisable.
> Elle est créée lorsqu'un besoin réel de réutilisation apparaît.

## Avant de créer un package

> Avant de créer une technologie Gogold, vérifier si Stake Engine fournit déjà
> une solution adaptée.

Le Web SDK Stake fournit déjà de nombreuses briques (`utils-book`,
`utils-fetcher`, `utils-slots`, `utils-layout`, `utils-sound`, `utils-xstate`,
`pixi-svelte`, `components-ui-*`, `config-*`, `state-*`).

Nous voulons d'abord comprendre et utiliser leurs packages, pas les redoubler.

Convention de nommage Stake, à reprendre :
`<type>-<scope>` (ex. `utils-book`, `components-ui-pixi`).

## Ce que ce dossier ne fait PAS

Il n'accueille pas de packages créés « au cas où ». Tant qu'un seul jeu existe,
la frontière entre code de jeu et code de plateforme n'est pas connue : elle se
découvre en construisant le deuxième jeu.
