# Gogold Continuous Integration

Une barrière automatique entre une modification et `main`.

```text
CODE / ASSET / MATH
        ↓
   PULL REQUEST
        ↓
        CI
  ┌─────┼─────┐
  ↓     ↓     ↓
QUALITY BUILD MATH
  └─────┼─────┘
        ↓
   MERGE AUTORISÉ
```

Nous sommes trois. La CI doit attraper les erreurs importantes avec le minimum
de maintenance — pas devenir une usine DevOps.

---

## Purpose

Empêcher qu'une erreur basique arrive silencieusement dans `main` :

```text
le build de production casse
un master (.psd, .aep, .wav…) est livré dans static/
du code de développement fuit dans le build (Debug Panel, fixtures, bypass RGS)
les tests du Math SDK cassent
```

La CI **valide**. Elle ne déploie rien, ne publie rien.

---

## When CI runs

```yaml
pull_request → main
push         → main
workflow_dispatch    # lancement manuel
```

Une seule CI par branche : un nouveau commit annule le run précédent
(`concurrency` + `cancel-in-progress`).

Permissions : `contents: read` uniquement. **Aucun secret n'est nécessaire.**

---

## Required checks

Trois jobs, tous verts aujourd'hui :

| Check (nom exact) | Ce qu'il garantit |
| --- | --- |
| **Frontend Quality** | installation reproductible + aucun fichier interdit dans les assets runtime |
| **Frontend Build** | le build de production passe + aucun code de dev dedans |
| **Math Tests** | le Math SDK **du repository** passe ses tests |

Ces trois noms sont stables et servent à la protection de branche.

---

## Informational checks

Ils s'exécutent, sont visibles dans les logs, mais **ne bloquent pas** — ils sont
en `continue-on-error` parce qu'ils échouent pour des raisons upstream connues.

| Check | Statut | Pourquoi non bloquant |
| --- | --- | --- |
| **Lint** | rouge | Défaut upstream : `eslint@9` + configuration legacy `.eslintrc.cjs` |
| **Typecheck** | rouge | 96 erreurs préexistantes, **toutes** dans du code Stake |
| **Build size** | rapporté | `lines` dépasse la cible interne ; c'est un sample de référence |

> Un check informatif ne doit jamais servir à masquer un vrai échec. Ces deux-là
> sont documentés, reproductibles dans l'upstream intact, et suivis.

---

## Frontend checks

### Frontend Quality

```text
pnpm install --frozen-lockfile          BLOQUANT
asset validation (toutes les apps)      BLOQUANT
lint                                    informatif
typecheck                               informatif
```

### Frontend Build

```text
pnpm install --frozen-lockfile          BLOQUANT
pnpm run build                          BLOQUANT
check-production-build                  BLOQUANT
```

Le build est **global** (`pnpm run build`, sans filtre) : Turborepo exécute la
tâche `build` de tout workspace qui en possède une. Aujourd'hui `lines` et
`pixi-svelte`. Une future slot est couverte sans toucher à la CI.

### Versions

```text
Node   22.16.0     épinglé dans ci.yml, aligné sur engines.node (>=22.16.0)
pnpm   10.5.0      lu automatiquement depuis packageManager par pnpm/action-setup
Python 3.13        math/setup.py exige >= 3.12
```

> `NODE_VERSION` dans `ci.yml` est un pin explicite. En cas de bump de
> `engines.node`, mettre les deux à jour.

---

## Math checks

```text
pip install -r requirements.txt         méthode officielle Stake
pip install -e .                        installe NOTRE math/ en editable
garde : PROJECT_PATH == math/           BLOQUANT
pytest tests/                           BLOQUANT
```

### Pourquoi le garde-fou

La première ligne de `math/requirements.txt` installe un editable **distant** :

```text
-e git+https://github.com/StakeEngine/math-sdk.git@0842bb2…#egg=stakeengine
```

épinglé sur un commit plus ancien que notre baseline. Le `pip install -e .` qui
suit le remplace par notre copie locale — mais rien ne le prouve à l'exécution.

La CI l'assure explicitement : elle importe `src.config.paths.PROJECT_PATH` et
vérifie qu'il pointe bien sur `math/` du repository. Sans ce garde, une CI verte
pourrait tester le code de Stake au lieu du nôtre.

### Ce que la CI Math ne fait pas

```text
aucune simulation lourde        run.py n'est jamais lancé
aucune optimisation             Rust/Cargo n'est pas installé
```

Les tests de `math/tests/` sont des tests de calcul de gains : ils tournent en
moins d'une seconde et n'ont besoin ni de Rust ni de simulations.

---

## Asset checks

```powershell
node tooling/assets/check-assets.mjs apps/<game>/static/assets
```

La CI boucle sur **toutes** les apps possédant `static/assets/`. Elle échoue si
un master (`.psd`, `.aep`, `.blend`, `.wav`…) ou un fichier temporaire
(`.tmp`, `.bak`, `Thumbs.db`…) est présent.

Outil créé en A10 — voir [`ASSET_PIPELINE.md`](ASSET_PIPELINE.md). Il n'existe
qu'un seul asset checker.

---

## Build size reporting

`tooling/ci/check-production-build.mjs` mesure et publie dans le Job Summary :

| App | Runtime assets | Build final |
| --- | ---: | ---: |
| `lines` | 51.9 MB | 55.6 MB |

**Mesuré, pas bloquant.** `lines` est un sample Stake de référence qui dépasse la
cible interne Gogold ; le bloquer n'aurait aucun sens. Les budgets stricts seront
définis pour les vraies slots, à partir de ces mesures.

Le même script assure aussi le contrôle bloquant de sécurité production.

---

## Known upstream limitations

### ESLint — défaut de la baseline Stake

Le Web SDK épingle `eslint@9.21.0` mais livre encore le format legacy
`.eslintrc.cjs` (12 fichiers). ESLint 9 attend `eslint.config.js`.

**Reproduit à l'identique dans un clone upstream intact.** Même en forçant le
mode legacy, `eslint-config-custom` référence le processeur `svelte3/svelte3`,
supprimé depuis longtemps.

Non corrigé volontairement : rester aligné sur l'upstream prime. Lint reste
informatif tant que ce défaut existe.

### Typecheck — 96 erreurs upstream

`svelte-check` fonctionne mais rapporte 96 erreurs préexistantes :

```text
63  static/**/index.ts    index d'assets, code mort important 'utils-pixi' (paquet inexistant)
19  src/stories/**        stories du sample upstream
 8  packages Stake        rgs-fetcher, envs
 6  src/ + tsconfig       config-ts non adaptée au typecheck de cette app
---
 0  code écrit par Gogold
```

Le typecheck **détecte bien** une vraie erreur : un `string` assigné à un
`number` dans `src/game/devDebugMode.ts` est signalé et fait passer le total de
96 à 97. L'outil est fiable ; c'est la baseline qui est sale.

Il deviendra bloquant quand une vraie slot Gogold aura son propre `src` propre.

### Storybook — pas de build non interactif

`apps/lines` n'a pas de script `build-storybook` ; seul le serveur interactif
existe. Aucun check Storybook n'est ajouté : monter un navigateur headless
uniquement pour la CI n'apporterait pas assez face au build jeu.

### Dérive de la fixture de debug — non vérifiable

`debugScenarios.generated.ts` est produit par
`tooling/debug/export_debug_scenarios.py` depuis
`math/games/<id>/library/`, qui est **volontairement non versionné**.

```text
fixture regeneration cannot be enforced in CI from committed sources yet
```

La régénération reste une opération locale, documentée dans
[`DEBUG_PANEL.md`](DEBUG_PANEL.md). Créer une CI qui simule des millions de
rounds pour vérifier une fixture de 100 KB serait absurde.

---

## Running CI checks locally

Exactement les commandes de la CI :

```powershell
pnpm install --frozen-lockfile

# Frontend Quality
node tooling/assets/check-assets.mjs apps/lines/static/assets
pnpm run lint          # informatif
pnpm run typecheck     # informatif — NODE_OPTIONS=--max-old-space-size=8192

# Frontend Build
pnpm run build
node tooling/ci/check-production-build.mjs

# Math Tests
cd math
.\env\Scripts\python.exe -m pytest tests/ -q
```

Sur Windows, le typecheck a besoin d'un tas Node élargi :

```powershell
$env:NODE_OPTIONS="--max-old-space-size=8192"
```

`svelte-check` charge `apps/lines/src/stories/data/base_books.ts` (20 MB) et
sature le tas par défaut sans cela.

---

## GitHub branch protection setup

⚠️ **Créer `ci.yml` ne bloque aucun merge à lui seul.** Tant que la règle
ci-dessous n'est pas activée dans GitHub, une PR rouge reste mergeable.

État actuel : **non vérifié et non configuré** — aucun paramètre GitHub n'a été
modifié depuis ce repository.

À faire par un administrateur, **après le premier push du workflow** (les checks
doivent avoir tourné au moins une fois pour apparaître dans la liste) :

1. `Settings ▸ Rules ▸ Rulesets ▸ New branch ruleset` (ou `Settings ▸ Branches`)
2. Cibler la branche `main`
3. Activer **Require a pull request before merging**
4. Activer **Require status checks to pass**
5. Ajouter exactement ces trois checks :

```text
Frontend Quality
Frontend Build
Math Tests
```

6. Ne **pas** ajouter les étapes informatives : elles vivent dans
   `Frontend Quality` et n'y font pas échouer le job.
7. Recommandé : **Require branches to be up to date before merging**

---

## Adding a future game to CI

**Frontend** — une nouvelle `apps/<game>/` entre automatiquement dans la CI si
elle possède :

| Script / dossier | Ce qu'il déclenche |
| --- | --- |
| `"build"` dans son `package.json` | Frontend Build + contrôle de sécurité production + mesure de taille |
| `static/assets/` | Asset validation |
| `"typecheck"` dans son `package.json` | Typecheck (informatif aujourd'hui) |

Aucune modification de `ci.yml` n'est nécessaire : le build est global, la
validation d'assets boucle sur `apps/*/static/assets`, et
`check-production-build.mjs` découvre les apps possédant un `build/`.

> ⚠️ Une app **sans script `build`** n'est testée par rien. Au moment de créer une
> nouvelle slot, vérifier que son `package.json` déclare bien `build` — sinon elle
> sera créée mais jamais testée.

**Math** — un nouveau `math/games/<game>/` est couvert par les tests génériques
de `math/tests/`, qui portent sur `math/src/`. Aucune action.

Les simulations d'un jeu ne sont **pas** lancées en CI : c'est une opération
locale coûteuse, pas un contrôle de PR.

---

## What CI does NOT do

```text
aucun déploiement
aucune publication Stake (frontend ou math)
aucune publication npm, aucune GitHub Release
aucune simulation Math massive
aucun test E2E (pas de Playwright/Cypress)
aucune régression visuelle cloud (pas de Chromatic payant, pas de Percy)
aucun secret, aucun token, aucune session RGS
aucune écriture dans le repository
```

Le CD viendra seulement si un besoin réel apparaît.
