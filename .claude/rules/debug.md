---
paths:
  - "apps/*/src/dev/**"
  - "tooling/debug/**"
---

# Debug Panel et fixtures DEV

Référence détaillée : `docs/DEBUG_PANEL.md`, `tooling/debug/README.md`.

## Ce que le Debug Panel est

Une télécommande de développement : elle **sélectionne** un Book déjà produit par
le Math SDK et le donne au pipeline Stake normal via `playBet`.

```text
force records / books Math → fixtures DEV → panel → playBet → pipeline normal
```

> **Ne jamais fabriquer le résultat dans le Debug Panel.**

Interdits : calculer un gain, un RTP, des reel stops, décider d'un bonus ou d'un
multiplicateur, modifier directement la grille (`forceScatter()` et compagnie),
créer un `DebugEvent` / `DebugEventBus`, forcer un état de la machine XState.

## DEV uniquement

Activé par `?debug=true` sur un serveur de dev, gardé par `import.meta.env.DEV`
pour que Rollup élimine le panel et ses fixtures du bundle de production.

Le contrôle automatique `tooling/ci/check-production-build.mjs` échoue si un
marqueur de développement atteint un build. Ne pas contourner ce garde.

Le mode local ne doit exiger ni session RGS, ni token, ni credential. Il ne
simule pas de wallet et ne reproduit pas de solde : il fournit le minimum d'état
pour afficher des books locaux.

## Fixtures

Autorisé dans Git : de **petites** fixtures DEV/Storybook déterministes,
explicitement sélectionnées.

Interdit : bibliothèques de millions de books, publish outputs lourds, sorties de
simulation massives.

Une fixture versionnée doit être produite par un script reproductible (jamais
éditée à la main), se limiter à quelques books par scénario, déclarer sa
provenance, et rester hors du bundle de production.

## Générateur

`tooling/debug/export_debug_scenarios.py` est en **lecture seule** sur les
sorties Math. Il ne modifie jamais une simulation, un book ou une probabilité, et
n'écrit jamais dans `math/`.

Les scénarios sont data-driven : ils viennent des force records Stake ou de
champs déjà calculés du book. Ne pas coder en dur une liste universelle de
scénarios — chaque jeu a les siens.

## Aucun secret

Jamais de `sessionID`, token, credential ou URL privée dans une fixture ou dans
le panel.
