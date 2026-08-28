"""Profil du BetMode Bonus Buy — OUTIL DE DÉVELOPPEMENT.

Deux grandeurs à ne jamais confondre, et c'est toute la raison d'être de ce
fichier :

    PAYOUT      en multiples de la MISE DE BASE, comme dans les Books
    RENDEMENT   ce même payout rapporté au PRIX D'ACHAT du mode

Pour un achat à 100x, un payout de 20x n'est pas un petit gain : c'est une perte
de 80 % de la mise. Un rapport qui n'affiche que des payouts donne une image
fausse du mode. Les deux lectures sont donc données côte à côte.

Lit la population brute par défaut, ou la LUT si `--weighted` est donné : la
première décrit ce que la simulation a produit, la seconde ce que le joueur
rencontrera.

    python games/0_0_plant_vs_wild/bonus_buy_profile.py
    python games/0_0_plant_vs_wild/bonus_buy_profile.py --weighted
"""

import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zstandard  # noqa: E402

from game_config import GameConfig  # noqa: E402

MODE = "bonus"

#: Tranches de PAYOUT, en multiples de la mise de base.
PAYOUT_BANDS = [
    ("0-10x", 0, 10), ("10-20x", 10, 20), ("20-50x", 20, 50), ("50-100x", 50, 100),
    ("100-250x", 100, 250), ("250-500x", 250, 500), ("500-1000x", 500, 1000),
    ("1000-2500x", 1000, 2500), ("2500-5000x", 2500, 5000),
    ("5000-10000x", 5000, 10000), ("10000x", 10000, float("inf")),
]

#: Tranches de RENDEMENT, en part du prix d'achat.
RETURN_BANDS = [
    ("< 10 %", 0.0, 0.10), ("10-25 %", 0.10, 0.25), ("25-50 %", 0.25, 0.50),
    ("50-100 %", 0.50, 1.00), ("100-200 %", 1.00, 2.00), ("200-500 %", 2.00, 5.00),
    ("500-1000 %", 5.00, 10.00), ("1000 %+", 10.00, float("inf")),
]


def band(value, bands):
    for name, low, high in bands:
        if low <= value < high:
            return name
    return bands[-1][0]


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


def quantile(pairs, fraction):
    """Quantile pondéré. `pairs` = [(valeur, poids)], déjà trié par valeur."""
    total = sum(weight for _, weight in pairs)
    running = 0.0
    for value, weight in pairs:
        running += weight
        if running >= total * fraction:
            return value
    return pairs[-1][0] if pairs else 0.0


def main():
    weighted = "--weighted" in sys.argv
    config = GameConfig()
    cost = next(b.get_cost() for b in config.bet_modes if b.get_name() == MODE)

    weights = None
    if weighted:
        lut = os.path.join(config.publish_path, f"lookUpTable_{MODE}_0.csv")
        weights = {}
        with open(lut, encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    sim_id, weight, _ = line.strip().split(",")
                    weights[int(sim_id)] = int(weight)

    pairs = []
    payout_bands = Counter()
    return_bands = Counter()
    features = Counter()
    retrigger_weight = 0.0
    total_weight = 0.0
    for book in read_books(os.path.join(config.publish_path, f"books_{MODE}.jsonl.zst")):
        payout = book["payoutMultiplier"] / 100.0
        weight = float(weights.get(book["id"], 0)) if weighted else 1.0
        if weight == 0:
            continue
        total_weight += weight
        pairs.append((payout, weight))
        payout_bands[band(payout, PAYOUT_BANDS)] += weight
        return_bands[band(payout / cost, RETURN_BANDS)] += weight
        kinds = {e["type"] for e in book["events"]}
        if "freeSpinRetrigger" in kinds:
            retrigger_weight += weight
        for event in book["events"]:
            if event["type"] == "wildFeature":
                features[event["feature"]] += weight

    pairs.sort()
    mean = sum(v * w for v, w in pairs) / total_weight
    rtp = mean / cost

    label = "PONDÉRÉ PAR LA LUT" if weighted else "POPULATION BRUTE"
    print(f"BONUS BUY — {label}   ({len(pairs)} Books, coût {cost:.0f}x)\n")
    print(f"   RTP (moyenne / coût)   {rtp:.6f}")
    print(f"   payout moyen           {mean:.2f}x")
    print(f"   médiane                {quantile(pairs, 0.50):.2f}x")
    for name, fraction in (("P90", 0.90), ("P95", 0.95), ("P99", 0.99), ("P99.9", 0.999)):
        print(f"   {name:22} {quantile(pairs, fraction):.2f}x")
    print(f"   maximum                {pairs[-1][0]:.2f}x")

    print("\n   PAYOUT (multiples de la mise de base)")
    for name, _, _ in PAYOUT_BANDS:
        share = payout_bands.get(name, 0.0) / total_weight
        print(f"      {name:14} {share * 100:8.4f} %")

    print(f"\n   RENDEMENT (part du prix d'achat de {cost:.0f}x)")
    for name, _, _ in RETURN_BANDS:
        share = return_bands.get(name, 0.0) / total_weight
        print(f"      {name:14} {share * 100:8.4f} %")

    def share_at_least(threshold):
        return sum(w for v, w in pairs if v >= threshold) / total_weight

    print("\n   SEUILS")
    print(f"      P(payout < coût {cost:.0f}x)  {(1 - share_at_least(cost)) * 100:7.3f} %")
    for threshold in (100, 250, 500, 1000, 5000, 10000):
        print(f"      P(payout >= {threshold:5}x)     {share_at_least(threshold) * 100:7.4f} %")

    print("\n   AUTRES")
    print(f"      retrigger              {retrigger_weight / total_weight * 100:7.3f} %")
    for name in ("rage", "wildSplit", "wildSnake"):
        share = features.get(name, 0.0) / total_weight
        print(f"      {name:22} {share * 100:7.4f} %")


if __name__ == "__main__":
    main()
