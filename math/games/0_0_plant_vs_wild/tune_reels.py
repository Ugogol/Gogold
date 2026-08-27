"""Banc de mesure pour le réglage des bandes — OUTIL DE DÉVELOPPEMENT.

Il pilote le vrai `GameState.run_spin` : aucun simulateur parallèle, aucune
règle réécrite. Il sert uniquement à mesurer vite un jeu de poids de bandes
avant de lancer le pipeline complet.

Ce qu'il mesure, et pourquoi : le RTP de PLANT VS WILD est dominé par la
RECONNEXION — la même zone qui regagne cascade après cascade, chaque case
doublant à chaque passage. Les compteurs ci-dessous séparent le premier hit
(qu'on veut garder) de la reconnexion (qu'on veut rendre rare).

    python games/0_0_plant_vs_wild/tune_reels.py --wagers 8000
"""

import argparse
import io
import os
import statistics
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402

STRIP_LENGTH = 300


def build_strip(weights: dict, columns: int = 5, length: int = STRIP_LENGTH) -> list:
    """Construit des bandes où chaque symbole est réparti le plus régulièrement possible.

    Deux symboles identiques collés dans une bande créent une paire verticale sur
    le plateau, donc une amorce de connexion. En étalant chaque symbole au
    maximum, on réduit ces amorces sans toucher à sa densité — c'est un levier de
    bande, pas une règle de jeu.

    Le placement est déterministe : à poids identiques, bandes identiques.
    """
    total = sum(weights.values())
    counts = {name: max(1, round(weight / total * length)) for name, weight in weights.items() if weight > 0}

    ordered = []
    for name, count in sorted(counts.items()):
        for index in range(count):
            ordered.append(((index + 0.5) / count, name))
    ordered.sort()
    base = [name for _, name in ordered]

    # Chaque colonne est la même bande décalée : les colonnes restent
    # indépendantes sans avoir à décrire cinq bandes à la main.
    step = max(1, len(base) // columns)
    return [[base[(row + column * step) % len(base)] for row in range(len(base))] for column in range(columns)]


def write_strip(path: str, strip: list) -> None:
    """Écrit une bande au format CSV du SDK : une ligne par position, une colonne par reel."""
    rows = zip(*strip)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(",".join(row) + "\n")


class Metrics:
    """Compteurs d'un lot de simulations."""

    def __init__(self):
        self.wagers = 0
        self.payout = 0.0
        self.paying_wagers = 0
        self.wincaps = 0
        self.spins = 0
        self.free_spins = 0
        self.initial_hits = 0
        self.reconnect_attempts = Counter()
        self.reconnect_hits = Counter()
        self.connections = 0
        self.cluster_mult_total = 0
        self.cluster_mults = []
        self.cascade_depths = []
        self.spins_with_wild = 0
        self.wild_reveal = 0
        self.wild_refill = 0
        self.wild_moves = 0
        self.bonus_rounds = 0
        self.bonus_wins = []
        self.retriggers = 0
        self.activation_counts = []
        self.max_activation = 0
        self.winning_positions = []
        self.repeated_positions = []
        self.mult_levels = Counter()


def measure(config, wagers: int, mode: str = "base") -> Metrics:
    state = GameState(config)
    state.betmode = mode
    state.criteria = "basegame" if mode == "base" else "freegame"
    metrics = Metrics()

    for sim in range(wagers):
        state.run_spin(sim)
        book = state.book
        metrics.wagers += 1
        payout = book.payout_multiplier
        metrics.payout += payout
        if payout > 0:
            metrics.paying_wagers += 1

        depth = 0
        seen_grid = {}
        activations = Counter()
        spin_positions = []
        wild_on_board = False
        bonus_open = False

        for event in book.events:
            kind = event["type"]

            if kind == "reveal":
                if metrics.spins:
                    metrics.cascade_depths.append(depth)
                    metrics.winning_positions.append(len(spin_positions))
                    metrics.repeated_positions.append(len(spin_positions) - len(set(spin_positions)))
                depth = 0
                spin_positions = []
                metrics.spins += 1
                if event["gameType"] == "freegame":
                    metrics.free_spins += 1
                wild_on_board = any(
                    cell["name"] == "W"
                    for column in event["board"]
                    for row, cell in enumerate(column)
                    if 1 <= row <= 5
                )
                if wild_on_board:
                    metrics.spins_with_wild += 1
                    metrics.wild_reveal += 1

            elif kind == "wincap":
                metrics.wincaps += 1

            elif kind == "winInfo":
                if depth == 0:
                    metrics.initial_hits += 1
                else:
                    metrics.reconnect_hits[min(depth, 4)] += 1
                for win in event["wins"]:
                    metrics.connections += 1
                    mult = win["meta"]["clusterMult"]
                    metrics.cluster_mult_total += mult
                    metrics.cluster_mults.append(mult)
                    for position in win["positions"]:
                        key = (position["reel"], position["row"])
                        spin_positions.append(key)
                        activations[key] += 1

            elif kind == "tumbleBoard":
                depth += 1
                metrics.reconnect_attempts[min(depth, 4)] += 1
                if not wild_on_board:
                    for column in event["newSymbols"]:
                        if any(cell["name"] == "W" for cell in column):
                            wild_on_board = True
                            metrics.spins_with_wild += 1
                            metrics.wild_refill += 1
                            break

            elif kind == "wildMove":
                metrics.wild_moves += 1

            elif kind == "updateGrid":
                for reel, column in enumerate(event["gridMultipliers"]):
                    for row, value in enumerate(column):
                        key = (reel, row)
                        if value > seen_grid.get(key, 0):
                            seen_grid[key] = value
                            metrics.mult_levels[value] += 1

            elif kind == "freeSpinTrigger":
                metrics.bonus_rounds += 1
                bonus_open = True

            elif kind == "freeSpinRetrigger":
                metrics.retriggers += 1

            elif kind == "freeSpinEnd":
                if bonus_open:
                    metrics.bonus_wins.append(event["amount"] / 100.0)
                    bonus_open = False

        metrics.cascade_depths.append(depth)
        metrics.winning_positions.append(len(spin_positions))
        metrics.repeated_positions.append(len(spin_positions) - len(set(spin_positions)))
        if activations:
            metrics.activation_counts.extend(activations.values())
            metrics.max_activation = max(metrics.max_activation, max(activations.values()))

    return metrics


def summarise(metrics: Metrics, cost: float) -> dict:
    wagers = metrics.wagers or 1
    spins = metrics.spins or 1
    connections = metrics.connections or 1

    reconnect = {}
    for depth in (1, 2, 3, 4):
        attempts = metrics.reconnect_attempts.get(depth, 0)
        hits = metrics.reconnect_hits.get(depth, 0)
        reconnect[f"reconnect{depth}"] = round(hits / attempts, 4) if attempts else None

    bonus_wins = sorted(metrics.bonus_wins)
    return {
        "rtp": round(metrics.payout / (wagers * cost), 4),
        "hit_rate": round(metrics.paying_wagers / wagers, 4),
        "initial_hit_rate": round(metrics.initial_hits / spins, 4),
        **reconnect,
        "avg_cluster_mult": round(metrics.cluster_mult_total / connections, 2),
        "median_cluster_mult": statistics.median(metrics.cluster_mults) if metrics.cluster_mults else 0,
        "connections_per_spin": round(connections / spins, 4),
        "avg_cascade_depth": round(statistics.fmean(metrics.cascade_depths), 3),
        "max_cascade_depth": max(metrics.cascade_depths) if metrics.cascade_depths else 0,
        "avg_winning_positions_per_spin": round(statistics.fmean(metrics.winning_positions), 3),
        "avg_repeated_positions_per_spin": round(statistics.fmean(metrics.repeated_positions), 3),
        "avg_position_activations": round(statistics.fmean(metrics.activation_counts), 3)
        if metrics.activation_counts
        else 0,
        "max_position_activations": metrics.max_activation,
        "wild_spin_frequency": round(metrics.spins_with_wild / spins, 4),
        "wild_reveal": metrics.wild_reveal,
        "wild_refill": metrics.wild_refill,
        "wild_moves_per_spin": round(metrics.wild_moves / spins, 4),
        "bonus_one_in": round(wagers / metrics.bonus_rounds, 1) if metrics.bonus_rounds else None,
        "bonus_median": round(statistics.median(bonus_wins), 2) if bonus_wins else None,
        "bonus_average": round(statistics.fmean(bonus_wins), 2) if bonus_wins else None,
        "bonus_under_20x": round(sum(1 for w in bonus_wins if w < 20) / len(bonus_wins), 4)
        if bonus_wins
        else None,
        "bonus_over_100x": round(sum(1 for w in bonus_wins if w > 100) / len(bonus_wins), 4)
        if bonus_wins
        else None,
        "bonus_over_500x": round(sum(1 for w in bonus_wins if w > 500) / len(bonus_wins), 4)
        if bonus_wins
        else None,
        "retriggers_per_bonus": round(metrics.retriggers / metrics.bonus_rounds, 4)
        if metrics.bonus_rounds
        else None,
        "wincap_one_in": round(wagers / metrics.wincaps, 1) if metrics.wincaps else None,
        "mult_levels": {str(k): v for k, v in sorted(metrics.mult_levels.items()) if k > 0},
    }


def main():
    parser = argparse.ArgumentParser(description="Banc de reglage des bandes PLANT VS WILD")
    parser.add_argument("--wagers", type=int, default=8000)
    parser.add_argument("--mode", default="base", choices=["base", "bonus"])
    args = parser.parse_args()

    config = GameConfig()
    result = summarise(measure(config, args.wagers, args.mode), 1.0 if args.mode == "base" else 100.0)
    for key, value in result.items():
        print(f"{key:34} {value}")


if __name__ == "__main__":
    main()
