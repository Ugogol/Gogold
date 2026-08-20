# tooling/debug

Génère les fixtures de développement consommées par le Debug Panel.

Processus complet et règles : [`docs/DEBUG_PANEL.md`](../../docs/DEBUG_PANEL.md).

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
