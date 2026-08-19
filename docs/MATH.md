# Gogold Math Foundation

Fondation mathématique de Gogold : le **Stake Engine Math SDK officiel**, intégré tel quel.

Gogold n'écrit pas de moteur math. Nous configurons des jeux au-dessus du moteur Stake.

---

## Stake Math SDK baseline

```text
Upstream            : https://github.com/StakeEngine/math-sdk
Integrated commit   : e2f0db9cf04cb3b0202fa3747ce173a46ac0aa7f
Commit date         : 2026-08-01
Integration date    : 2026-08-19
```

Même logique de provenance que [`FRONTEND.md`](FRONTEND.md) pour le Web SDK.

Aucun submodule, aucun subtree, aucun script de synchronisation : la stratégie de mise à
jour upstream sera décidée séparément.

---

## Location

```text
math/
```

Le SDK est **indépendant de son emplacement** : `src/config/paths.py` dérive `PROJECT_PATH`
de `__file__`, jamais du répertoire courant. Il fonctionne donc sous `math/` sans aucune
modification de ses imports.

Deux toolchains cohabitent dans le repository, strictement séparées :

```text
apps/ + packages/   → Node / pnpm / Turbo / Stake Web SDK
math/               → Python / Stake Math SDK
```

`math/` n'est **pas** un workspace pnpm et ne doit jamais être ajouté à `pnpm-workspace.yaml`.

---

## Environment

```text
Python  : 3.13.7  (SDK exige >= 3.12)
venv    : math/env/   (non versionné)
Rust    : cargo 1.95.0 — optimiseur opérationnel
```

Le dossier venv s'appelle `env` et non `.venv` : c'est le nom attendu par le `Makefile`
upstream (`VENV_DIR := env`) et par la documentation d'installation Stake. Le garder
identique évite toute divergence avec l'outillage officiel.

> Python 3.14 n'est pas utilisable : `requirements.txt` épingle `numpy==2.2.5`, qui ne
> publie pas de wheel pour 3.14.

---

## SDK structure

```text
math/
├── games/                 # jeux d'exemple officiels (référence exécutable)
├── src/                   # moteur générique Stake — NE PAS MODIFIER
│   ├── calculations/      # plateau, symboles, logique de gains
│   ├── config/            # génération des configs RGS / frontend / optimiseur
│   ├── events/            # structures d'events math → frontend
│   ├── executables/       # regroupements réutilisables de logique
│   ├── state/             # état de simulation
│   ├── wins/              # wallet manager
│   └── write_data/        # écriture books, compression, force files
├── tests/                 # PyTest sur les calculs de gains
├── utils/                 # analyse de distribution, stat sheets, vérification RGS
├── optimization_program/  # algorithme génétique Rust
├── uploads/               # upload S3 (code source Stake, pas un artefact)
├── requirements.txt
├── setup.py
└── Makefile
```

Non copiés depuis l'upstream (inutiles au runtime) : `.github/`, `.vscode/`,
`.devcontainer/`, `docs/`, `mkdocs.yml`, `.nojekyll`. La documentation Stake reste
consultable sur le repository upstream.

---

## Reference sample

```text
math/games/0_0_lines/
```

5 rouleaux × 3 rangées, gains en lignes, `rtp = 0.9670`, `wincap = 5000`.

Les jeux d'exemple officiels sont conservés **tels quels** comme documentation exécutable :
`0_0_lines`, `0_0_ways`, `0_0_cluster`, `0_0_scatter`, `0_0_expwilds`,
`0_0_lines_feature_match`, `fifty_fifty`, `template`.

Ne jamais les renommer, les modifier, ni les transformer en jeux Gogold.

---

## How to install

Depuis `math/`. Make n'étant pas disponible sous Windows, on applique la procédure
manuelle officielle (identique aux cibles du `Makefile`) :

```powershell
py -3.13 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Sous Linux/macOS avec Make disponible : `make setup`.

> `requirements.txt` contient en première ligne un editable `git+https://...@0842bb2`
> pointant vers un commit **plus ancien** que notre baseline. Le `pip install -e .` final
> l'écrase par notre copie locale. Vérification :
> `pip show stakeengine` doit afficher `Editable project location: ...\Gogold\math`.

---

## How to run a sample

```powershell
.\env\Scripts\Activate.ps1
python games/0_0_lines/run.py
```

Avec Make : `make run GAME=0_0_lines`.

Les paramètres de run (nombre de simulations, threads, compression, activation de
l'optimisation et de l'analyse) sont définis dans le `run.py` du jeu. Toujours les lire
avant de lancer : un run mal dimensionné peut coûter des heures.

---

## How to run tests

```powershell
python -m pytest tests/
```

---

## Publication outputs

Emplacement réel (vérifié, pas supposé) :

```text
math/games/<game_id>/library/publish_files/
```

Contenu produit pour `0_0_lines` :

```text
index.json
lookUpTable_base_0.csv
lookUpTable_bonus_0.csv
books_base.jsonl.zst
books_bonus.jsonl.zst
```

Autres sorties générées, sous `library/` : `books/`, `books_compressed/`,
`lookup_tables/`, `configs/`, `forces/`, `optimization_files/`.

### Frontend ≠ Math

Deux livrables strictement séparés :

```text
Frontend  → apps/<game>/build/
Math      → math/games/<game_id>/library/publish_files/
```

Ne jamais mélanger les artefacts math dans le build frontend.

---

## Minimum Stake math files

Par game mode, le RGS exige :

```text
index.json                  manifeste des modes
lookUpTable_<mode>_0.csv    lookup table optimisée
books_<mode>.jsonl.zst      game logic compressé
```

`index.json` référence, pour chaque mode : `name`, `cost`, `events`, `weights`.

La lookup table est un CSV à 3 colonnes sans en-tête : `simulation ID`, `poids` (entier
uint64), `payout multiplier`.

Chaque book contient `id`, `events`, `payoutMultiplier`.

---

## Gogold rules

- **Stake first.** Utiliser le SDK tel quel. Aucune `MathFactory`, `GogoldMathEngine`,
  `MechanicFactory`, générateur de jeu ni CLI math Gogold.
- **Ne pas modifier `math/src/`** sans raison forte. C'est le moteur générique Stake.
  Toute divergence doit être documentée ici.
- **Ne pas dupliquer la math dans le frontend.** Le frontend rejoue des events, il ne
  calcule jamais un gain.
- **Ne pas éditer à la main les fichiers de publication.** Ils sont générés par le
  workflow du SDK. Les fabriquer manuellement pour faire passer un test est interdit.
- **Ne rien versionner de généré.** `library/**`, `env/`, `__pycache__/`,
  `optimization_program/target/` sont ignorés par Git. Les fichiers de publication se
  régénèrent avec `run.py`.

---

## Divergences avec l'upstream

Une seule, et elle ne touche pas le moteur :

`math/.gitignore` — ajout de `!optimization_program/Cargo.toml`.

La règle upstream `*.toml` masquerait le manifeste Cargo, nécessaire pour compiler
l'optimiseur Rust. Stake le versionne malgré cette règle (il a été ajouté avant elle) ;
sur une copie neuve il serait perdu. `optimization_program/src/setup.toml` reste ignoré :
il est réécrit à chaque run par `OptimizationExecution`.

Le `.gitignore` racine de Gogold a par ailleurs été ajusté : `uploads/` → `/uploads/`,
car `math/uploads/` est du code source du SDK, pas un artefact de publication.

`math/src/`, `math/tests/`, `math/utils/`, `math/games/`, `math/uploads/`,
`requirements.txt`, `setup.py`, `Makefile` sont **identiques à l'upstream** (vérifié par
`diff -r`).
