---
paths:
  - "packages/**"
  - "math/src/**"
  - "apps/lines/**"
---

# Code upstream Stake

Ces zones viennent du Stake Web SDK et du Stake Math SDK. Elles sont **copiées**,
pas forkées volontairement : nous voulons pouvoir diffuser contre l'upstream.

Baselines enregistrées dans `docs/FRONTEND.md` et `docs/MATH.md`.

## Avant de modifier

1. déterminer si le fichier est upstream — en cas de doute, il l'est
2. si oui : **préférer ne pas le modifier**
3. chercher une solution dans notre propre code (`apps/<game>/src/`, `tooling/`)
4. si la modification est réellement nécessaire :
   - expliquer pourquoi avant d'agir
   - limiter le diff au strict minimum
   - documenter la divergence dans la doc du domaine
   - ne pas en profiter pour reformater ou refactorer

Ne jamais appliquer des règles de style Gogold à du code upstream. Ne jamais
découper un fichier Stake pour satisfaire une métrique de longueur.

## `apps/lines` est un sample, pas un jeu

C'est le banc de test technique du repository. Ne pas le renommer, le rebrander
ni le transformer en jeu de production. Ne pas modifier sa paytable, ses reels,
ses symboles, ses animations ni le comportement de ses bookEvents.

## Divergences déjà décidées — ne pas les annuler

```text
apps/lines/package.json            cross-env devant le script storybook (Windows)
                                   svelte-check + script typecheck
apps/lines/src/routes/+layout.svelte   montage du Debug Panel, DEV uniquement
apps/lines/src/game/bookEventHandlerMap.ts   garde isLocalDebugMode() sur recordBookEvent
apps/lines/src/dev/, src/game/devDebugMode.ts   outillage DEV Gogold
```

Elles sont documentées dans `docs/STORYBOOK.md` et `docs/DEBUG_PANEL.md`.

## Défauts upstream connus — ne pas les corriger

```text
ESLint            eslint@9 + configuration legacy .eslintrc.cjs
svelte-check      erreurs préexistantes de la baseline
wincap            event Math non géré par le handler map du sample
pixi-svelte-storybook   dossier static/ absent, Storybook ne démarre pas
```

Tous reproduits à l'identique dans l'upstream intact. Les corriger nous
éloignerait de Stake sans bénéfice. Ne pas les « réparer » au détour d'une tâche
sans rapport — voir `docs/CI.md`.

## Mise à jour du SDK

Aucune synchronisation automatique n'existe. Ne jamais mettre à jour un SDK au
cours d'une tâche fonctionnelle : c'est une opération dédiée, tracée par son
propre commit.
