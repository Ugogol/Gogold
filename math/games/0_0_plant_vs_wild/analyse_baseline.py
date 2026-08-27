"""Mesure du comportement de PLANT VS WILD — OUTIL DE DÉVELOPPEMENT.

LECTURE SEULE sur les sorties de simulation. Ne lance aucune simulation, ne
modifie aucun book, ne règle rien. Il décrit le jeu tel qu'il est.

    python games/0_0_plant_vs_wild/run.py --base 50000 --bonus 10000
    python games/0_0_plant_vs_wild/analyse_baseline.py

Entrées   library/publish_files/books_<mode>.jsonl.zst   les books
          library/publish_files/lookUpTable_<mode>_0.csv la lookup table
Sorties   baseline/baseline_report.json                  chiffres bruts
          baseline/BASELINE.md                           résumé lisible

Les statistiques globales — RTP, hit rate, écart-type, percentiles, distribution
des gains — viennent des fonctions du SDK (`utils.rgs_verification`) : ce sont
celles que Stake utilise pour ses propres contrôles, on ne les recalcule pas.
Seul ce que le SDK ne connaît pas est dérivé des books : cascades, Wild,
multiplicateurs, Bonus, features.
"""

import json
import os
import statistics
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zstandard  # noqa: E402

from baseline_markdown import render  # noqa: E402
from game_config import GameConfig, MAX_POSITION_MULT, WILD_MAX_CHARGE  # noqa: E402
from utils.rgs_verification import get_lut_statistics, verify_lookup_format  # noqa: E402

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baseline")

#: Buckets de gain, en multiples de la mise. Les bornes reprennent celles
#: demandées pour la revue ; le SDK a les siennes, plus fines, conservées à part.
WIN_BUCKETS = [
    ("0x", 0.0, 0.0),
    (">0x-1x", 0.0, 1.0),
    ("1x-2x", 1.0, 2.0),
    ("2x-5x", 2.0, 5.0),
    ("5x-10x", 5.0, 10.0),
    ("10x-25x", 10.0, 25.0),
    ("25x-50x", 25.0, 50.0),
    ("50x-100x", 50.0, 100.0),
    ("100x-500x", 100.0, 500.0),
    ("500x+", 500.0, float("inf")),
]


def read_books(path):
    """Décompresse et parcourt les books un par un."""
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


def bucket_of(payout):
    """Bucket d'un gain exprimé en multiple de mise."""
    for name, low, high in WIN_BUCKETS:
        if name == "0x":
            if payout == 0:
                return name
            continue
        if low < payout <= high:
            return name
    return WIN_BUCKETS[-1][0]


class SpinStats:
    """Compteurs dérivés des books, par mode de jeu."""

    def __init__(self):
        self.spins = 0
        self.spins_with_win = 0
        self.cascades = Counter()
        self.cascade_total = 0
        self.cascade_max = 0
        self.spins_with_wild = 0
        self.wild_at_reveal = 0
        self.wild_from_refill = 0
        self.wild_connections = Counter()
        self.multiplier_peaks = Counter()
        self.win_amount = 0.0
        self.win_without_mult = 0.0
        self.wild_cluster_win = 0.0
        self.features = Counter()
        self.feature_wins = {}
        self.snake_lengths = []
        self.snake_symbols = Counter()


def analyse_mode(path, cost):
    """Parcourt tous les books d'un mode et en tire les compteurs par spin."""
    per_gametype = {"basegame": SpinStats(), "freegame": SpinStats()}
    payouts = []
    bonus_rounds = []
    books_with_bonus = 0
    books = 0

    for book in read_books(path):
        books += 1
        payouts.append(book["payoutMultiplier"] / 100.0)

        gametype = "basegame"
        stats = per_gametype[gametype]
        spin_open = False
        cascades = 0
        connections = 0
        spin_win = 0.0
        wild_seen = False
        feature_this_spin = None
        feature_win = 0.0
        grid_peak = {}
        bonus = None

        for event in book["events"]:
            kind = event["type"]

            if kind == "reveal":
                if spin_open:
                    stats.cascades[min(cascades, 4)] += 1
                    stats.cascade_total += cascades
                    stats.cascade_max = max(stats.cascade_max, cascades)
                    stats.wild_connections[min(connections, 4)] += 1
                    if spin_win > 0:
                        stats.spins_with_win += 1
                    if feature_this_spin:
                        stats.feature_wins.setdefault(feature_this_spin, []).append(feature_win)

                gametype = event["gameType"]
                stats = per_gametype[gametype]
                stats.spins += 1
                spin_open = True
                cascades = connections = 0
                spin_win = 0.0
                feature_this_spin = None
                feature_win = 0.0

                wild_cells = [
                    cell
                    for column in event["board"]
                    for row, cell in enumerate(column)
                    if cell["name"] == "W" and 1 <= row <= 5
                ]
                wild_seen = bool(wild_cells)
                if wild_seen:
                    stats.spins_with_wild += 1
                    stats.wild_at_reveal += 1
                if bonus is not None and gametype == "freegame":
                    bonus["spins"] += 1

            elif kind == "winInfo":
                for win in event["wins"]:
                    amount = win["win"] / 100.0
                    stats.win_amount += amount
                    stats.win_without_mult += win["meta"]["winWithoutMult"] / 100.0
                    spin_win += amount
                    if feature_this_spin:
                        feature_win += amount
                if bonus is not None and gametype == "freegame":
                    bonus["win"] += event["totalWin"] / 100.0

            elif kind == "tumbleBoard":
                cascades += 1
                if not wild_seen:
                    for column in event["newSymbols"]:
                        if any(cell["name"] == "W" for cell in column):
                            wild_seen = True
                            stats.spins_with_wild += 1
                            stats.wild_from_refill += 1
                            break

            elif kind == "wildMove":
                connections += 1

            elif kind == "updateGrid":
                for reel, column in enumerate(event["gridMultipliers"]):
                    for row, value in enumerate(column):
                        key = (reel, row)
                        if value > grid_peak.get(key, 0):
                            grid_peak[key] = value
                            stats.multiplier_peaks[value] += 1

            elif kind == "wildFeature":
                feature_this_spin = event["feature"]
                stats.features[event["feature"]] += 1
                if event["feature"] == "wildSnake":
                    stats.snake_lengths.append(len(event["path"]) + 1)
                    stats.snake_symbols[event["symbol"]] += 1

            elif kind == "freeSpinTrigger":
                books_with_bonus += 1
                bonus = {"total_fs": event["totalFs"], "retriggers": 0, "spins": 0, "win": 0.0}

            elif kind == "freeSpinRetrigger":
                if bonus is not None:
                    bonus["retriggers"] += 1
                    bonus["total_fs"] = event["totalFs"]

            elif kind == "freeSpinEnd":
                if bonus is not None:
                    bonus["win"] = event["amount"] / 100.0
                    bonus_rounds.append(bonus)
                    bonus = None

        if spin_open:
            stats.cascades[min(cascades, 4)] += 1
            stats.cascade_total += cascades
            stats.cascade_max = max(stats.cascade_max, cascades)
            stats.wild_connections[min(connections, 4)] += 1
            if spin_win > 0:
                stats.spins_with_win += 1
            if feature_this_spin:
                stats.feature_wins.setdefault(feature_this_spin, []).append(feature_win)

    return {
        "books": books,
        "payouts": payouts,
        "per_gametype": per_gametype,
        "bonus_rounds": bonus_rounds,
        "books_with_bonus": books_with_bonus,
        "cost": cost,
    }


def sdk_statistics(config, mode, cost):
    """Statistiques standard du SDK, lues sur la lookup table publiée."""
    lut = os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv")
    distribution, payouts, weights, min_win, max_win = verify_lookup_format(lut)
    stats = get_lut_statistics(mode, distribution, cost, payouts, weights, min_win, max_win, 0)
    return {
        "rtp": round(stats.rtp, 5),
        "hit_rate": round(stats.non_zero_hr, 5),
        "prob_no_win": round(stats.prob_nil, 5),
        "average_win": round(stats.average_win, 4),
        "std_dev": round(stats.std, 4),
        "variance": round(stats.var, 4),
        "skew": round(stats.skew, 4),
        "excess_kurtosis": round(stats.excess_kurtosis, 4),
        "max_win_observed": max_win / 100.0,
        "max_win_hit_rate": stats.hr_max,
    }


def percentiles(values):
    ordered = sorted(values)
    if not ordered:
        return {}

    def at(fraction):
        index = min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1))))
        return ordered[index]

    return {
        "P50": at(0.50),
        "P90": at(0.90),
        "P95": at(0.95),
        "P99": at(0.99),
        "P99.9": at(0.999),
    }


def describe(stats: SpinStats):
    """Compteurs d'un mode de jeu, exprimés en fréquences."""
    spins = stats.spins or 1
    return {
        "spins": stats.spins,
        "spins_with_win": stats.spins_with_win,
        "hit_rate_per_spin": round(stats.spins_with_win / spins, 5),
        "cascades": {
            "distribution": {str(k): v for k, v in sorted(stats.cascades.items())},
            "average": round(stats.cascade_total / spins, 4),
            "max": stats.cascade_max,
        },
        "wild": {
            "spins_with_wild": stats.spins_with_wild,
            "frequency": round(stats.spins_with_wild / spins, 5),
            "at_reveal": stats.wild_at_reveal,
            "from_refill": stats.wild_from_refill,
            "connections_per_spin": {str(k): v for k, v in sorted(stats.wild_connections.items())},
        },
        "multiplier_peaks": {str(k): v for k, v in sorted(stats.multiplier_peaks.items())},
        "win_amount_total": round(stats.win_amount, 2),
        "win_without_multipliers_total": round(stats.win_without_mult, 2),
        "features": {
            name: {
                "activations": count,
                "average_win_after": round(
                    sum(stats.feature_wins.get(name, [0])) / max(1, len(stats.feature_wins.get(name, []))), 3
                ),
                "max_win_after": round(max(stats.feature_wins.get(name, [0])), 3),
            }
            for name, count in sorted(stats.features.items())
        },
        "snake": {
            "average_length": round(statistics.fmean(stats.snake_lengths), 3) if stats.snake_lengths else None,
            "max_length": max(stats.snake_lengths) if stats.snake_lengths else None,
            "symbols": {k: v for k, v in sorted(stats.snake_symbols.items())},
        },
    }


def build_report(config, base, bonus):
    report = {
        "meta": {
            "game_id": config.game_id,
            "paytable": "TEST_ONLY",
            "note": "Mesure d'un état, pas une validation. Aucun objectif de RTP n'est fixé.",
            "rules": {
                "min_cluster": 4,
                "board": "5x5",
                "max_position_multiplier": MAX_POSITION_MULT,
                "wild_max_charge": WILD_MAX_CHARGE,
                "free_spins": 10,
                "retrigger": 5,
            },
            "balancing_parameters": {
                "snake_symbol_weights": config.snake_symbol_weights,
                "dead_spin_feature_weights": config.dead_spin_feature_weights,
                "snake_path_length": list(config.snake_path_length),
                "wild_split_extra_wilds": config.wild_split_extra_wilds,
            },
        },
        "simulations": {},
        "modes": {},
    }

    for name, data in (("base", base), ("bonus", bonus)):
        payouts = data["payouts"]
        cost = data["cost"]
        multiples = [payout / cost for payout in payouts]
        buckets = Counter(bucket_of(value) for value in multiples)

        report["simulations"][name] = {
            "wagers": data["books"],
            "bet_cost": cost,
            "seeding": "simulation_seeds = range(n), random.seed(0) — reproductible",
        }

        base_stats = data["per_gametype"]["basegame"]
        free_stats = data["per_gametype"]["freegame"]
        bonus_wins = [round(entry["win"], 3) for entry in data["bonus_rounds"]]
        retriggers = Counter(min(entry["retriggers"], 2) for entry in data["bonus_rounds"])

        report["modes"][name] = {
            "sdk": sdk_statistics(config, name, cost),
            "observed_rtp": round(sum(payouts) / (data["books"] * cost), 5),
            "win_distribution": {
                label: {
                    "count": buckets.get(label, 0),
                    "share": round(buckets.get(label, 0) / max(1, len(multiples)), 5),
                }
                for label, _, _ in WIN_BUCKETS
            },
            "payout_percentiles_in_bet_multiples": {
                key: round(value / cost, 3) for key, value in percentiles(payouts).items()
            },
            "max_observed_win_in_bet_multiples": round(max(payouts) / cost, 3) if payouts else 0,
            "basegame": describe(base_stats),
            "freegame": describe(free_stats),
            "bonus": {
                "wagers_with_bonus": data["books_with_bonus"],
                "trigger_frequency": round(data["books_with_bonus"] / data["books"], 6),
                "one_in": round(data["books"] / data["books_with_bonus"], 1)
                if data["books_with_bonus"]
                else None,
                "rounds": len(data["bonus_rounds"]),
                "average_total_fs": round(
                    statistics.fmean([entry["total_fs"] for entry in data["bonus_rounds"]]), 3
                )
                if data["bonus_rounds"]
                else None,
                "average_win": round(statistics.fmean(bonus_wins), 3) if bonus_wins else None,
                "median_win": round(statistics.median(bonus_wins), 3) if bonus_wins else None,
                "max_win": max(bonus_wins) if bonus_wins else None,
                "retriggers": {
                    "average": round(
                        statistics.fmean([entry["retriggers"] for entry in data["bonus_rounds"]]), 4
                    )
                    if data["bonus_rounds"]
                    else None,
                    "zero": retriggers.get(0, 0),
                    "one": retriggers.get(1, 0),
                    "two_or_more": retriggers.get(2, 0),
                },
            },
            "rtp_contribution": rtp_contribution(data),
        }

    return report


def rtp_contribution(data):
    """Répartition approximative du payout, en n'attribuant que ce qui est isolable."""
    base_stats = data["per_gametype"]["basegame"]
    free_stats = data["per_gametype"]["freegame"]
    total = base_stats.win_amount + free_stats.win_amount
    if total <= 0:
        return {"note": "aucun gain"}

    multiplier_part = (base_stats.win_amount - base_stats.win_without_mult) + (
        free_stats.win_amount - free_stats.win_without_mult
    )

    return {
        "basegame_share": round(base_stats.win_amount / total, 5),
        "freegame_share": round(free_stats.win_amount / total, 5),
        "position_multipliers_share": round(multiplier_part / total, 5),
        "position_multipliers_note": (
            "Isolable exactement : win - winWithoutMult, les deux montants sont dans winInfo."
        ),
        "wild_share": "NON_ISOLABLE",
        "wild_note": (
            "Le Wild complète des connexions qui n'existeraient pas sans lui et en agrandit "
            "d'autres. Séparer sa part demanderait de rejouer chaque spin sans Wild — ce serait "
            "un autre jeu, pas une mesure."
        ),
        "features_share": round(
            sum(
                sum(wins)
                for stats in (base_stats, free_stats)
                for wins in stats.feature_wins.values()
            )
            / total,
            5,
        ),
        "features_note": (
            "Gains encaissés dans un spin APRÈS l'activation d'une feature. Majorant : une partie "
            "de ces gains serait peut-être survenue sans elle."
        ),
    }


def main():
    config = GameConfig()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    modes = {}
    for name, cost in (("base", 1.0), ("bonus", 100.0)):
        path = os.path.join(config.publish_path, f"books_{name}.jsonl.zst")
        if not os.path.exists(path):
            raise SystemExit(
                f"Books absents : {path}\nLancer d'abord : python games/{config.game_id}/run.py"
            )
        print(f"lecture de {name}...", flush=True)
        modes[name] = analyse_mode(path, cost)

    report = build_report(config, modes["base"], modes["bonus"])

    probe_path = os.path.join(OUTPUT_DIR, "feature_probe.json")
    probe = None
    if os.path.exists(probe_path):
        with open(probe_path, encoding="utf-8") as handle:
            probe = json.load(handle)
        report["feature_probe"] = probe

    with open(os.path.join(OUTPUT_DIR, "baseline_report.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, ensure_ascii=False)
        handle.write("\n")

    with open(os.path.join(OUTPUT_DIR, "BASELINE.md"), "w", encoding="utf-8") as handle:
        handle.write(render(report, probe))

    print(json.dumps(report["modes"]["base"]["sdk"], indent=1))
    print("base RTP observe :", report["modes"]["base"]["observed_rtp"])
    print("bonus RTP observe :", report["modes"]["bonus"]["observed_rtp"])


if __name__ == "__main__":
    main()
