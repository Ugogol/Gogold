# Gogold

Monorepo des jeux de slots HTML5 Gogold, publiés sur **Stake Engine**.

Structure alignée sur le Web SDK Stake Engine
(https://github.com/StakeEngine/web-sdk) : pnpm workspaces + Turborepo.

## Structure

```text
apps/       un dossier = un jeu (spécifique à ce jeu uniquement)
packages/   code réellement partagé entre plusieurs jeux
tooling/    outils internes servant à fabriquer et vérifier les jeux
docs/       documentation et standards Gogold
```

## Principes

- Stake Engine est la référence technique : utiliser leurs SDK, packages et
  conventions plutôt que de les réimplémenter.
- Pas d'abstraction prématurée : un package n'est créé que lorsqu'un besoin
  réel de réutilisation apparaît.
- Le frontend rejoue un résultat déjà décidé par le RGS ; il ne calcule rien.

Détails : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) et
[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Statut

Structuration initiale du repository. Aucun jeu n'est implémenté.
Prochaine étape : intégration du Web SDK Stake Engine.

## Prérequis

- Node.js >= 22.16.0
- pnpm 10.5.0 (`corepack enable`)
