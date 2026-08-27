# tooling/debug

Génère les fixtures de développement consommées par le Debug Panel.

Processus complet et règles : [`docs/DEBUG_PANEL.md`](../../docs/DEBUG_PANEL.md).

Deux scripts, deux sources :

| Script | Source | Quand |
| --- | --- | --- |
| `sync-math-books.mjs` | `math/games/<id>/canonical_books/` — books **versionnés** | scénarios de référence, stables, comparables au contrat |
| `export_debug_scenarios.py` | `math/games/<id>/library/` — sorties de **simulation** | cas rares pêchés dans un gros run, non versionnés |

## sync-math-books.mjs

Copie les Books canoniques d'un jeu Math vers son app, après validation du
contrat. Node >= 22, aucune dépendance.

```powershell
node tooling/debug/sync-math-books.mjs `
    --math-game math/games/0_0_plant_vs_wild `
    --config    apps/plant-vs-wild/src/dev/mathBooks.config.json `
    --out       apps/plant-vs-wild/src/dev/generated-books
```

Raccourci : `pnpm --filter=plant-vs-wild run sync:math-books`.

### Entrées

```text
math/games/<id>/canonical_books/index.json    la liste
math/games/<id>/canonical_books/<name>.json   les books
apps/<app>/src/dev/mathBooks.config.json      dimensions, events autorisés, scénarios
```

Les books canoniques sont produits par `python games/<id>/make_books.py`. Ils
sont **versionnés**, contrairement aux sorties de simulation.

### Sorties

```text
<out>/<name>.json    copies conformes, à l'octet près
<out>/index.ts       module GÉNÉRÉ — ne jamais l'éditer à la main
```

### Ce qu'il valide

```text
type d'event connu du contrat frontend
index cohérent avec la position dans le book
board          reels x lignes paddées, symboles nommés
newSymbols     une liste par reel
gridMultipliers  reels x lignes visibles, valeurs numériques
Position       {reel, row} dans le plateau, ligne visible (padding exclu)
finalWin       unique et dernier
setTotalWin    un par reveal (optionnel, selon la config du jeu)
```

Un Book non conforme fait **échouer** la synchronisation et rien n'est écrit. Il
se corrige dans le Math, jamais dans le frontend.

### Ce qu'il ne fait pas

Il n'ajoute aucun event, ne déplace aucune position, ne touche ni aux symboles,
ni aux multiplicateurs, ni aux charges. Il ne répare jamais silencieusement un
Book. Il n'écrit que dans `--out`.

> `resolveJsonModule` est désactivé dans `config-ts/base.json` (upstream Stake).
> Une app qui consomme ces books l'active dans son propre `tsconfig.json`.

## export_debug_scenarios.py

Extrait **quelques books** des sorties du Math SDK et écrit un petit module
TypeScript.

```powershell
& ".\math\env\Scripts\python.exe" tooling/debug/export_debug_scenarios.py `
    --math-game math/games/0_0_lines `
    --config    apps/lines/src/dev/debugScenarios.config.json `
    --out       apps/lines/src/dev/debugScenarios.generated.ts
```

Python vient de l'environnement du Math SDK (`math/env`) : les books sont
compressés en **zstd**, format que Node 22 ne sait pas lire nativement. Utiliser
l'interpréteur déjà en place évite d'ajouter une dépendance au frontend.

### Entrées

```text
math/games/<id>/library/forces/force_record_<mode>.json     critère -> bookIds
math/games/<id>/library/publish_files/books_<mode>.jsonl.zst  les books
```

Ces fichiers sont **générés** par `python games/<id>/run.py` et ne sont pas
versionnés. Sans eux, le script s'arrête avec un message explicite ; le fichier
`.generated.ts` déjà produit reste utilisable.

### Configuration

Un fichier par jeu, à côté du panel. Deux types de sélection :

| `select.type` | Source | Usage |
| --- | --- | --- |
| `force` | force records Stake (`search` -> `bookIds`) | critères de **forme de gain** : `gametype`, `kind`, `symbol`, `mult` |
| `payout` | champs déjà calculés du book | critères de **magnitude** : `min`, `max`, `hasEvent`, `withoutEvent` |

```json
{
  "booksPerScenario": 2,
  "scenarios": [
    { "id": "base-max-win", "label": "Base — MAX WIN", "mode": "base",
      "select": { "type": "payout", "min": 500000 } },
    { "id": "base-scatter-3", "label": "Base — 3 scatters", "mode": "base",
      "select": { "type": "force",
                  "search": { "gametype": "basegame", "kind": "3", "symbol": "scatter" } } }
  ]
}
```

> `payoutMultiplier` est exprimé dans l'échelle du Math du jeu. Pour
> `0_0_lines`, c'est en **centièmes** : `500000` = 5000x = le wincap. Vérifier
> l'échelle du jeu avant d'écrire des seuils.

### Garanties

```text
lecture seule sur math/     n'écrit jamais dans math/
déterministe                books retenus = les premiers par ID croissant
sans dépendance ajoutée     zstandard, déjà dans math/env
ne recalcule rien           sélectionne, ne fabrique aucun résultat
```

### Ce qu'il ne fait pas

Il ne modifie aucune simulation, aucun book, aucune probabilité. Il ne lance pas
de simulation : si les force records manquent, c'est à `math/games/<id>/run.py`
de les produire.

Il n'écrit qu'un seul fichier, celui passé en `--out`.
