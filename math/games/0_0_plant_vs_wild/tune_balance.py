"""Banc de balancing de PLANT VS WILD — OUTIL DE DÉVELOPPEMENT.

Il pilote le vrai `GameState.run_spin` : aucun simulateur parallèle, aucune
règle réécrite, aucune probabilité modifiée après coup.

ATTRIBUTION DU RTP — convention, pour qu'aucun gain ne soit compté deux fois :

    normal base     `basegame_wins` des wagers qui NE déclenchent PAS le Bonus
    trigger spins   `basegame_wins` des wagers qui le déclenchent
    free spins      `freegame_wins`, quel que soit le wager
    total           la somme des trois, égale à la somme des payouts

Le « Natural Bonus » est celui déclenché depuis le Base Game. Le mode `bonus`
(acheté/forcé) est mesuré à part : il n'hérite pas de la grille du spin
déclencheur et n'est pas la référence de design.

    python games/0_0_plant_vs_wild/tune_balance.py --wagers 20000
"""

import argparse
import os
import statistics
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402

#: Buckets de gain d'un Bonus, en multiples de mise.
BONUS_BUCKETS = [
    ("0-5x", 0, 5),
    ("5-10x", 5, 10),
    ("10-20x", 10, 20),
    ("20-50x", 20, 50),
    ("50-100x", 50, 100),
    ("100-250x", 100, 250),
    ("250-500x", 250, 500),
    ("500-1000x", 500, 1000),
    ("1000-2500x", 1000, 2500),
    ("2500-5000x", 2500, 5000),
    ("5000x", 5000, float("inf")),
]

BASE_BUCKETS = [("0x", 0, 0), ("<1x", 0, 1), ("1-10x", 1, 10), ("10-100x", 10, 100), ("100x+", 100, float("inf"))]


def bucket(value, table):
    """Range une valeur dans son bucket.

    Le premier bucket est fermé à gauche : un Bonus qui ne rapporte rien
    appartient au plus bas, pas au plus haut.
    """
    for index, (name, low, high) in enumerate(table):
        if name == "0x":
            if value == 0:
                return name
            continue
        if (low <= value if index == 0 or table[0][0] == "0x" and index == 1 else low < value) and value <= high:
            return name
    return table[-1][0]


def percentile(ordered, fraction):
    if not ordered:
        return None
    return ordered[min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1))))]


def run(config, wagers, mode="base"):
    """Joue `wagers` paris et renvoie toutes les métriques de balancing."""
    state = GameState(config)
    state.betmode = mode
    state.criteria = "basegame" if mode == "base" else "freegame"
    cap = config.max_cascades_per_spin

    normal_base = trigger_base = free = 0.0
    payouts = []
    base_buckets = Counter()
    bonus_wins = []
    retriggers = Counter()
    features = Counter()
    feature_wins = Counter()
    levels = Counter()
    wincaps = 0
    base_spins = base_cap_hits = 0
    free_spins = free_cap_hits = 0
    base_hits = 0

    for sim in range(wagers):
        state.run_spin(sim)
        book = state.book
        payouts.append(book.payout_multiplier)
        base_buckets[bucket(book.payout_multiplier, BASE_BUCKETS)] += 1

        triggered = any(event["type"] == "freeSpinTrigger" for event in book.events)
        if triggered:
            trigger_base += book.basegame_wins
        else:
            normal_base += book.basegame_wins
        free += book.freegame_wins
        if book.basegame_wins > 0:
            base_hits += 1

        depth = 0
        gametype = "basegame"
        seen = {}
        retrigger_count = 0
        current_feature = None

        for event in book.events:
            kind = event["type"]
            if kind == "reveal":
                if gametype == "basegame":
                    base_spins += 1
                    if cap is not None and depth == cap:
                        base_cap_hits += 1
                else:
                    free_spins += 1
                    if cap is not None and depth == cap:
                        free_cap_hits += 1
                depth = 0
                gametype = event["gameType"]
                current_feature = None
            elif kind == "tumbleBoard":
                depth += 1
            elif kind == "wincap":
                wincaps += 1
            elif kind == "freeSpinRetrigger":
                retrigger_count += 1
            elif kind == "freeSpinEnd":
                bonus_wins.append(event["amount"] / 100.0)
            elif kind == "wildFeature":
                current_feature = event["feature"]
                features[current_feature] += 1
            elif kind == "winInfo" and current_feature:
                feature_wins[current_feature] += event["totalWin"] / 100.0
            elif kind == "updateGrid":
                for reel, column in enumerate(event["gridMultipliers"]):
                    for row, value in enumerate(column):
                        if value > seen.get((reel, row), 0):
                            seen[(reel, row)] = value
                            levels[value] += 1

        # dernier spin du book
        if gametype == "basegame":
            base_spins += 1
            if cap is not None and depth == cap:
                base_cap_hits += 1
        else:
            free_spins += 1
            if cap is not None and depth == cap:
                free_cap_hits += 1
        if triggered:
            retriggers[min(retrigger_count, 2)] += 1

    # Intervalle de confiance du RTP par bootstrap. Le RTP est dominé par de
    # très rares gros gains : sans cet intervalle, un chiffre à quatre décimales
    # donnerait une fausse impression de précision.
    import random as _random

    rng = _random.Random(12345)
    size = len(payouts)
    means = []
    for _ in range(200):
        means.append(sum(payouts[rng.randrange(size)] for _ in range(size)) / size)
    means.sort()
    rtp_ci = (means[4], means[195])

    payouts_sorted = sorted(payouts)
    bonus_sorted = sorted(bonus_wins)
    total_bonus = len(bonus_wins) or 1

    return {
        "wagers": wagers,
        "rtp_total": sum(payouts) / wagers,
        "rtp_ci95": (round(rtp_ci[0], 4), round(rtp_ci[1], 4)),
        "rtp_normal_base": normal_base / wagers,
        "rtp_trigger_spins": trigger_base / wagers,
        "rtp_free_spins": free / wagers,
        "base_hit_rate": base_hits / wagers,
        "base_buckets": {name: base_buckets.get(name, 0) / wagers for name, _, _ in BASE_BUCKETS},
        "bonus_count": len(bonus_wins),
        "bonus_one_in": wagers / len(bonus_wins) if bonus_wins else None,
        "bonus_per_1000": len(bonus_wins) / wagers * 1000,
        "bonus_average": statistics.fmean(bonus_wins) if bonus_wins else None,
        "bonus_median": statistics.median(bonus_wins) if bonus_wins else None,
        "bonus_p75": percentile(bonus_sorted, 0.75),
        "bonus_p90": percentile(bonus_sorted, 0.90),
        "bonus_p95": percentile(bonus_sorted, 0.95),
        "bonus_p99": percentile(bonus_sorted, 0.99),
        "bonus_p999": percentile(bonus_sorted, 0.999),
        "bonus_buckets": {
            name: sum(1 for win in bonus_wins if bucket(win, BONUS_BUCKETS) == name) / total_bonus
            for name, _, _ in BONUS_BUCKETS
        },
        "bonus_under_10": sum(1 for w in bonus_wins if w < 10) / total_bonus,
        "bonus_under_20": sum(1 for w in bonus_wins if w < 20) / total_bonus,
        "bonus_under_50": sum(1 for w in bonus_wins if w < 50) / total_bonus,
        "bonus_over_100": sum(1 for w in bonus_wins if w > 100) / total_bonus,
        "bonus_over_500": sum(1 for w in bonus_wins if w > 500) / total_bonus,
        "bonus_over_1000": sum(1 for w in bonus_wins if w > 1000) / total_bonus,
        "retrigger_0": retriggers.get(0, 0) / total_bonus,
        "retrigger_1": retriggers.get(1, 0) / total_bonus,
        "retrigger_2plus": retriggers.get(2, 0) / total_bonus,
        "retrigger_avg": sum(k * v for k, v in retriggers.items()) / total_bonus,
        "features": dict(features),
        "feature_rtp": {name: total / wagers for name, total in feature_wins.items()},
        "levels": {level: levels.get(level, 0) for level in (32, 128, 512, 4096)},
        "base_cap_hit": base_cap_hits / base_spins if base_spins else 0,
        "free_cap_hit": free_cap_hits / free_spins if free_spins else 0,
        "wincap_one_in": wagers / wincaps if wincaps else None,
        "max_win": max(payouts) if payouts else 0,
        "p95": percentile(payouts_sorted, 0.95),
        "p99": percentile(payouts_sorted, 0.99),
        "p999": percentile(payouts_sorted, 0.999),
    }


def main():
    parser = argparse.ArgumentParser(description="Banc de balancing PLANT VS WILD")
    parser.add_argument("--wagers", type=int, default=20000)
    parser.add_argument("--mode", default="base", choices=["base", "bonus"])
    args = parser.parse_args()

    result = run(GameConfig(), args.wagers, args.mode)
    for key, value in result.items():
        if isinstance(value, dict):
            print(f"{key:22} " + " ".join(f"{k}={round(v, 4) if isinstance(v, float) else v}" for k, v in value.items()))
        elif isinstance(value, float):
            print(f"{key:22} {value:.5f}")
        else:
            print(f"{key:22} {value}")


if __name__ == "__main__":
    main()
