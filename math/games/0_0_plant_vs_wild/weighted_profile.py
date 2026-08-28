"""Profil du jeu PUBLIÉ, pondéré par la lookup table — OUTIL DE DÉVELOPPEMENT.

Après optimisation, la population brute des books ne décrit plus le jeu : c'est
la lookup table qui fixe la probabilité de chaque outcome. Toutes les métriques
ci-dessous sont donc pondérées par `weight / sum(weights)`.

C'est la différence entre « ce que la simulation a produit » et « ce que le
joueur rencontrera ».

CONVENTION : un « gain de Bonus » est ici le payout TOTAL du pari — spin
déclencheur et Free Spins additionnés. C'est la grandeur qui classe les Books
dans les fences de l'optimizer ; mesurer autre chose reviendrait à contrôler des
cibles qui n'ont pas été optimisées.

    python games/0_0_plant_vs_wild/weighted_profile.py base
"""

import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zstandard  # noqa: E402

from game_config import GameConfig  # noqa: E402

PAYOUT_BUCKETS = [
    ("0x", 0, 0),
    ("<1x", 0, 1),
    ("1-10x", 1, 10),
    ("10-50x", 10, 50),
    ("50-100x", 50, 100),
    ("100-500x", 100, 500),
    ("500-1000x", 500, 1000),
    ("1000-5000x", 1000, 5000),
    ("5000-10000x", 5000, 10000),
    ("10000x", 10000, float("inf")),
]

BONUS_BUCKETS = [
    ("0-5x", 0, 5), ("5-10x", 5, 10), ("10-20x", 10, 20), ("20-50x", 20, 50),
    ("50-100x", 50, 100), ("100-250x", 100, 250), ("250-500x", 250, 500),
    ("500-1000x", 500, 1000), ("1000-2500x", 1000, 2500),
    ("2500-5000x", 2500, 5000), ("5000x+", 5000, float("inf")),
]


def bucket(value, table):
    for index, (name, low, high) in enumerate(table):
        if name == "0x":
            if value == 0:
                return name
            continue
        if (low <= value if index <= 1 else low < value) and value <= high:
            return name
    return table[-1][0]


def read_books(path):
    """{id: (payout_x, features)} — tout ce dont le profil a besoin."""
    decompressor = zstandard.ZstdDecompressor()
    data = {}
    with open(path, "rb") as handle:
        buffer = ""
        for chunk in decompressor.read_to_iter(handle, read_size=1 << 20):
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    book = json.loads(line)
                    data[int(book["id"])] = summarise(book)
        if buffer.strip():
            book = json.loads(buffer)
            data[int(book["id"])] = summarise(book)
    return data


def summarise(book):
    payout = book["payoutMultiplier"] / 100.0
    bonus_win = None
    retriggers = 0
    features = set()
    triggered = False
    for event in book["events"]:
        kind = event["type"]
        if kind == "freeSpinTrigger":
            triggered = True
        elif kind == "freeSpinRetrigger":
            retriggers += 1
        elif kind == "freeSpinEnd":
            bonus_win = event["amount"] / 100.0
        elif kind == "wildFeature":
            features.add(event["feature"])
    return payout, triggered, bonus_win, retriggers, features


def weighted_median(pairs):
    """Médiane pondérée : pairs = [(valeur, poids)]."""
    ordered = sorted(pairs)
    total = sum(weight for _, weight in ordered)
    running = 0.0
    for value, weight in ordered:
        running += weight
        if running >= total / 2:
            return value
    return ordered[-1][0] if ordered else None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "base"
    config = GameConfig()
    lut_path = os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv")
    books = read_books(os.path.join(config.publish_path, f"books_{mode}.jsonl.zst"))

    rows = []
    with open(lut_path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                sim_id, weight, payout = line.strip().split(",")
                rows.append((int(sim_id), int(weight), int(float(payout)) / 100.0))

    total = sum(weight for _, weight, _ in rows)
    rtp = sum(weight * payout for _, weight, payout in rows) / total

    hit = payout_buckets = 0.0
    payout_buckets = Counter()
    bonus_prob = 0.0
    bonus_pairs = []
    bonus_buckets = Counter()
    retrigger_prob = Counter()
    feature_prob = Counter()
    max_win_prob = 0.0

    for sim_id, weight, payout in rows:
        share = weight / total
        _, triggered, bonus_win, retriggers, features = books[sim_id]
        if payout > 0:
            hit += share
        payout_buckets[bucket(payout, PAYOUT_BUCKETS)] += share
        if payout >= config.wincap:
            max_win_prob += share
        if triggered:
            bonus_prob += share
            retrigger_prob[min(retriggers, 2)] += share
            # Le Bonus est mesure sur le payout TOTAL du round, pas sur le seul
            # `freeSpinEnd`. C'est la meme grandeur que celle qui classe les
            # Books dans les fences de l'optimizer : sans cela, les cibles
            # verifiees ici ne porteraient pas sur ce qui a ete optimise.
            bonus_pairs.append((payout, share))
            bonus_buckets[bucket(payout, BONUS_BUCKETS)] += share
        for feature in features:
            feature_prob[feature] += share

    bonus_avg = sum(win * share for win, share in bonus_pairs) / bonus_prob if bonus_prob else 0
    bonus_med = weighted_median(bonus_pairs)

    def share_over(threshold):
        return sum(share for win, share in bonus_pairs if win > threshold) / bonus_prob

    def share_under(threshold):
        return sum(share for win, share in bonus_pairs if win < threshold) / bonus_prob

    print(f"WEIGHTED LUT RTP         {rtp:.6f}")
    print(f"weighted hit rate        {hit:.5f}")
    print(f"weighted bonus freq      1 / {1/bonus_prob:.1f}   ({bonus_prob*1000:.2f} / 1000)")
    print(f"weighted bonus average   {bonus_avg:.2f}x")
    print(f"weighted bonus median    {bonus_med:.2f}x")
    print(f"bonus <20x               {share_under(20)*100:.2f} %")
    print(f"bonus >100x              {share_over(100)*100:.2f} %")
    print(f"bonus >500x              {share_over(500)*100:.2f} %")
    print(f"bonus >1000x             {share_over(1000)*100:.2f} %")
    retrig_total = sum(retrigger_prob.values()) or 1
    print(f"retrigger 0/1/2+         {retrigger_prob[0]/retrig_total*100:.2f} % / "
          f"{retrigger_prob[1]/retrig_total*100:.2f} % / {retrigger_prob[2]/retrig_total*100:.2f} %")
    for name in ("rage", "wildSplit", "wildSnake"):
        prob = feature_prob.get(name, 0.0)
        print(f"feature {name:11}      {prob*100:.4f} %  " + (f"1 / {1/prob:.0f}" if prob else "jamais"))
    print(f"P(max win {config.wincap:.0f}x)      {max_win_prob:.3e}" +
          (f"   1 / {1/max_win_prob:,.0f}" if max_win_prob else "   jamais dans la population"))
    print("distribution ponderee des gains :")
    for name, _, _ in PAYOUT_BUCKETS:
        print(f"   {name:14} {payout_buckets.get(name, 0.0)*100:8.4f} %")
    print("distribution ponderee des Bonus :")
    for name, _, _ in BONUS_BUCKETS:
        share = bonus_buckets.get(name, 0.0) / bonus_prob * 100 if bonus_prob else 0
        print(f"   {name:14} {share:8.3f} %")


if __name__ == "__main__":
    main()
