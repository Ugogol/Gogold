"""Rapport de POPULATION D'OPTIMISATION — OUTIL DE DEVELOPPEMENT.

Repond a une seule question, avant tout run d'optimizer : la population de
Books contient-elle assez de matiere REELLE dans chaque criteria pour que
l'optimizer ait de quoi travailler ?

Un criteria vide fait sortir l'optimizer en erreur ; un criteria a trois Books
le laisse extrapoler la forme du jeu a partir de rien. C'est ce qui a fait
rejeter le premier candidat.

Aucun poids n'intervient ici : ce sont les Books BRUTS tels que la simulation
les a produits.

    python games/0_0_plant_vs_wild/criteria_population.py base
"""

import json
import os
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zstandard  # noqa: E402

from game_config import GameConfig, BONUS_BUCKET_BOUNDS  # noqa: E402

#: Forme de la population brute demandee par l'etape 28.
SHAPE = [
    ("0x", 0, 0), ("<1x", 0, 1), ("1-10x", 1, 10), ("10-20x", 10, 20),
    ("20-50x", 20, 50), ("50-100x", 50, 100), ("100-250x", 100, 250),
    ("250-500x", 250, 500), ("500-1000x", 500, 1000), ("1000-2500x", 1000, 2500),
    ("2500-5000x", 2500, 5000), ("5000-10000x", 5000, 10000), ("10000x", 10000, float("inf")),
]


def shape_bucket(value):
    """Tranche de payout. Bornes fermees a gauche, ouvertes a droite.

    Le plafond a sa propre tranche : le classer dans `5000-10000x` masquerait
    la seule chose qu'on veut lire ici, la presence de Books a 10 000x.
    """
    if value == 0:
        return "0x"
    if value >= SHAPE[-1][1]:
        return SHAPE[-1][0]
    for name, low, high in SHAPE[1:-1]:
        if low <= value < high:
            return name
    return SHAPE[-1][0]


def read_books(path):
    decompressor = zstandard.ZstdDecompressor()
    books = []
    with open(path, "rb") as handle:
        buffer = ""
        for chunk in decompressor.read_to_iter(handle, read_size=1 << 20):
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    books.append(json.loads(line))
        if buffer.strip():
            books.append(json.loads(buffer))
    return books


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "base"
    config = GameConfig()
    books = read_books(os.path.join(config.publish_path, f"books_{mode}.jsonl.zst"))

    # Le bucket se relit sur le force record : c'est la MEME source que celle
    # que l'optimizer interrogera, pas un recalcul parallele qui pourrait
    # diverger.
    force_path = os.path.join(config.library_path, "forces", f"force_record_{mode}.json")
    bucket_of = {}
    with open(force_path, encoding="utf-8") as handle:
        for entry in json.load(handle):
            keys = {k["name"]: k["value"] for k in entry["search"]}
            if "bucket" in keys:
                for book_id in entry["bookIds"]:
                    bucket_of[book_id] = (keys["bucket"], keys.get("retrigger"))

    by_criteria = defaultdict(list)
    for book in books:
        payout = book["payoutMultiplier"] / 100.0
        criteria = book.get("criteria", "?")
        bucket = bucket_of.get(book["id"])
        # Le criteria de SIMULATION dit d'ou vient le Book ; la fence de
        # l'optimizer, elle, se decide sur le payout exact (wincap, 0) puis sur
        # le bucket. On rapporte donc la fence, pas le criteria de simulation.
        if payout >= config.wincap:
            fence = "WINCAP"
        elif bucket is not None:
            name, retrigger = bucket
            # `medium` est scinde par retrigger : c'est la seule facon de viser
            # une frequence de retrigger sans deformer la forme des gains.
            if name == "medium":
                fence = "FREEGAME_MEDIUM_LONG" if retrigger == "yes" else "FREEGAME_MEDIUM"
            else:
                fence = f"FREEGAME_{name.upper()}"
        elif payout == 0:
            fence = "ZERO"
        else:
            fence = "BASEGAME"
        by_criteria[fence].append(payout)

    order = ["ZERO", "BASEGAME", "FREEGAME_LOW", "FREEGAME_MEDIUM",
             "FREEGAME_MEDIUM_LONG", "FREEGAME_HIGH", "FREEGAME_MEGA", "WINCAP"]
    total = len(books)

    print(f"CRITERIA POPULATION — mode {mode}   ({total} Books)\n")
    print(f"{'criteria':22} {'books':>7} {'part':>7}  {'min':>9} {'median':>9} {'mean':>10} {'max':>10}")
    for name in order:
        vals = sorted(by_criteria.get(name, []))
        if not vals:
            print(f"{name:22} {0:>7}   VIDE   —")
            continue
        print(f"{name:22} {len(vals):>7} {len(vals)/total*100:6.2f}% "
              f"{vals[0]:9.2f} {statistics.median(vals):9.2f} "
              f"{statistics.mean(vals):10.2f} {vals[-1]:10.2f}")

    extra = set(by_criteria) - set(order)
    if extra:
        print(f"\nATTENTION criteria inattendus : {sorted(extra)}")

    print("\nCOHERENCE DES CRITERIA")
    bonus_books = {b["id"] for b in books if bucket_of.get(b["id"]) is not None}
    capped = {b["id"] for b in books if b["payoutMultiplier"] / 100.0 >= config.wincap}
    print(f"   Books avec bucket           {len(bonus_books)}")
    print(f"   Books au plafond            {len(capped)}")
    print(f"   plafond ET bucket           {len(capped & bonus_books)}  "
          f"(saisis par WINCAP, traite en premier)")
    unclassified = [b for b in books if b["payoutMultiplier"] / 100.0 > 0
                    and b["id"] not in bonus_books and b["id"] not in capped]
    print(f"   gains sans bucket           {len(unclassified)}  (fence BASEGAME)")
    bounds_ok = all(BONUS_BUCKET_BOUNDS[a][1] == BONUS_BUCKET_BOUNDS[b][0]
                    for a, b in zip(["low", "medium", "high"], ["medium", "high", "mega"]))
    print(f"   bornes jointives sans trou  {bounds_ok}")

    print("\nPOPULATION PAYOUT SHAPE")
    shape = Counter(shape_bucket(b["payoutMultiplier"] / 100.0) for b in books)
    for name, _, _ in SHAPE:
        count = shape.get(name, 0)
        print(f"   {name:14} {count:8d}  {count/total*100:7.4f} %")


if __name__ == "__main__":
    main()
