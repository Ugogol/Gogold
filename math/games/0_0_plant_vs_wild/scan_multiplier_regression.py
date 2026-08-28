"""Scan de régression du multiplicateur sur TOUTE la population.

Une seule question, sans tolérance : une position gagnante progresse-t-elle
d'exactement UN cran par résolution ?

Le défaut corrigé doublait une case une fois PAR CONNEXION. Une case partagée
par six connexions passait donc de x1 à x64 en une résolution. Ce scan relit les
`updateGrid` de chaque Book et refuse tout facteur autre que x2.

Il mesure aussi la distribution des multiplicateurs atteints, pour voir ce que
la queue doit réellement au Math et non au défaut.

    python games/0_0_plant_vs_wild/scan_multiplier_regression.py base

Sortie : 0 si aucune régression, 1 sinon.
"""

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zstandard  # noqa: E402

from game_config import GameConfig, MAX_POSITION_MULT  # noqa: E402


def read_books(path):
    decompressor = zstandard.ZstdDecompressor()
    with open(path, "rb") as handle:
        buffer = ""
        for chunk in decompressor.read_to_iter(handle, read_size=1 << 20):
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    yield json.loads(line)
        if buffer.strip():
            yield json.loads(buffer)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "base"
    config = GameConfig()
    path = os.path.join(config.publish_path, f"books_{mode}.jsonl.zst")
    if not os.path.exists(path):
        raise SystemExit(f"population absente : {path}")

    books = regressions = 0
    worst = 1
    examples = []
    reached = Counter()
    #: Une case au plafond ne peut plus doubler : elle reste à sa valeur.
    #: Ce n'est pas une régression, c'est la borne de la progression.
    for book in read_books(path):
        books += 1
        previous = None
        for event in book["events"]:
            if event["type"] != "updateGrid":
                continue
            grid = event["gridMultipliers"]
            for column in grid:
                for value in column:
                    if value > 0:
                        reached[value] += 1
            if previous is not None:
                for reel, column in enumerate(grid):
                    for row, value in enumerate(column):
                        before = max(previous[reel][row], 1)
                        after = max(value, 1)
                        if after == before or after == before * 2:
                            continue
                        if before >= MAX_POSITION_MULT and after == before:
                            continue
                        regressions += 1
                        worst = max(worst, after // before if before else after)
                        if len(examples) < 8:
                            examples.append(
                                f"book {book['id']} case ({reel},{row}) x{before} -> x{after}"
                            )
            previous = grid

    print(f"mode                              {mode}")
    print(f"books analyses                    {books}")
    print(f"MULTI_CLUSTER_MULTIPLIER_REGRESSION = {regressions}")
    if regressions:
        print(f"facteur maximal observe           x{worst} en un cran")
        for line in examples:
            print(f"   {line}")

    total = sum(reached.values()) or 1
    print("\ndistribution des multiplicateurs atteints (cases actives) :")
    value = 2
    while value <= MAX_POSITION_MULT:
        count = reached.get(value, 0)
        print(f"   x{value:<6} {count:9d}  {count / total * 100:7.4f} %")
        value *= 2

    return 0 if regressions == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
