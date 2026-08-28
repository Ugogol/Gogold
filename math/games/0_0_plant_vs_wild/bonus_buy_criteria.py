"""Population par fence du BetMode Bonus Buy — OUTIL DE DÉVELOPPEMENT.

Répond à la question qui conditionne le lancement de l'optimizer : chaque fence
contient-elle assez de Books RÉELS et DIVERS pour qu'il ait de quoi travailler ?

Une fence vide fait sortir l'optimizer en erreur. Une fence à trois Books le
laisse extrapoler la forme du mode à partir de rien.

Les fences reprennent les bornes de bucket du mode base — `BONUS_BUCKET_BOUNDS`,
déjà inscrites dans les force records. Aucune nouvelle borne n'est introduite :
en changer une réécrirait les force records du mode base et invaliderait
BALANCING_V5.

    python games/0_0_plant_vs_wild/bonus_buy_criteria.py
"""

import json
import os
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zstandard  # noqa: E402

from game_config import GameConfig  # noqa: E402

MODE = "bonus"

#: Nom de fence par bucket enregistré. `wincap` a sa propre fence, définie sur
#: un payout exact et traitée en premier.
FENCE_OF_BUCKET = {
    "mega": "BUY_MEGA",
    "high": "BUY_HIGH",
    "medium": "BUY_MEDIUM",
    "low": "BUY_LOW",
}
ORDER = ["WINCAP", "BUY_MEGA", "BUY_HIGH", "BUY_MEDIUM", "BUY_LOW"]

#: Diversité de la longue queue : l'étape 21 veut ces tranches séparément.
TAIL_BANDS = [
    ("500-1000x", 500, 1000), ("1000-2500x", 1000, 2500),
    ("2500-5000x", 2500, 5000), ("5000-10000x", 5000, 10000),
    ("10000x", 10000, float("inf")),
]


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
    config = GameConfig()
    wincap_hundredths = int(round(config.wincap * 100))

    force_path = os.path.join(config.library_path, "forces", f"force_record_{MODE}.json")
    bucket_of = {}
    with open(force_path, encoding="utf-8") as handle:
        for entry in json.load(handle):
            keys = {k["name"]: k["value"] for k in entry["search"]}
            if "bucket" in keys:
                for book_id in entry["bookIds"]:
                    bucket_of[book_id] = keys["bucket"]

    payouts = defaultdict(list)
    retriggers = defaultdict(int)
    features = defaultdict(Counter)
    tail = Counter()
    total = 0
    unclassified = 0

    for book in read_books(os.path.join(config.publish_path, f"books_{MODE}.jsonl.zst")):
        total += 1
        payout = book["payoutMultiplier"] / 100.0
        if book["payoutMultiplier"] >= wincap_hundredths:
            fence = "WINCAP"
        else:
            bucket = bucket_of.get(book["id"])
            fence = FENCE_OF_BUCKET.get(bucket)
            if fence is None:
                unclassified += 1
                continue

        payouts[fence].append(payout)
        kinds = {e["type"] for e in book["events"]}
        if "freeSpinRetrigger" in kinds:
            retriggers[fence] += 1
        for event in book["events"]:
            if event["type"] == "wildFeature":
                features[fence][event["feature"]] += 1

        for name, low, high in TAIL_BANDS:
            if low <= payout < high:
                tail[name] += 1

    print(f"CRITERIA POPULATION — mode {MODE}   ({total} Books, coût {config.bet_modes[1].get_cost():.0f}x)\n")
    print(f"{'fence':12} {'books':>7} {'part':>7}  {'min':>9} {'median':>9} {'mean':>10} "
          f"{'max':>10}  {'retrig':>7}  features")
    empty = []
    for name in ORDER:
        values = sorted(payouts.get(name, []))
        if not values:
            empty.append(name)
            print(f"{name:12} {0:>7}   VIDE")
            continue
        share = retriggers[name] / len(values) * 100
        feat = " ".join(f"{k[:5]}:{v}" for k, v in sorted(features[name].items()))
        print(f"{name:12} {len(values):>7} {len(values)/total*100:6.2f}% "
              f"{values[0]:9.2f} {statistics.median(values):9.2f} "
              f"{statistics.mean(values):10.2f} {values[-1]:10.2f}  {share:6.2f}%  {feat}")

    print(f"\nBooks sans bucket (anomalie) : {unclassified}")
    print("\nDIVERSITÉ DE LA LONGUE QUEUE")
    for name, _, _ in TAIL_BANDS:
        print(f"   {name:14} {tail.get(name, 0):7d} Books")

    if empty:
        print(f"\nFENCES VIDES : {empty} — NE PAS lancer l'optimizer.")
        return 1
    print("\nToutes les fences sont peuplées.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
