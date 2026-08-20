---
paths:
  - ".github/workflows/**"
  - "tooling/ci/**"
  - "math/tests/**"
  - "apps/**/*.stories.svelte"
---

# Tests et CI

Référence détaillée : `docs/CI.md`, `docs/STORYBOOK.md`.

## Utiliser ce qui existe

Ne pas ajouter de framework de test sans besoin démontré. En particulier :
pas de Playwright, Cypress, Selenium, Chromatic payant ni Percy tant qu'aucun
besoin réel n'est établi.

```text
comportement visuel isolé   → Storybook
round complet / cas rare    → Debug Panel
calculs Math                → pytest (math/tests/)
```

## CI actuelle

Bloquants — noms exacts, utilisés par la protection de branche :

```text
Frontend Quality    install gelé + validation des assets
Frontend Build      build de production + absence de code de dev dans le build
Math Tests          Math SDK du repository + pytest
```

Informatifs aujourd'hui, à cause de défauts upstream documentés : **lint** et
**typecheck**. Ils ne doivent pas devenir bloquants tant que la baseline Stake
n'est pas propre.

## Règles

Toute commande ajoutée à la CI doit avoir été exécutée localement d'abord. Ne
jamais documenter une commande qui n'existe pas.

`continue-on-error` est réservé aux checks explicitement informatifs et
documentés. Ne jamais l'utiliser pour rendre un vrai échec invisible.

Aucun secret, aucun token, aucune session RGS n'est nécessaire à la CI. Ne pas en
introduire.

La CI valide : elle ne déploie rien et ne publie rien.

La CI ne couvre que l'automatisable. Avant de déclarer un travail terminé,
appliquer la checklist correspondante de `docs/DEFINITION_OF_DONE.md` — le rendu
visuel, les devices, l'audio et le Bet Replay restent manuels.

## Couverture d'un futur jeu

Une nouvelle `apps/<game>/` entre automatiquement dans la CI si son
`package.json` déclare un script `build` et si elle possède `static/assets/`.
Une app sans script `build` n'est testée par rien — le vérifier au moment de la
créer.

Les simulations Math d'un jeu ne tournent jamais en CI.
