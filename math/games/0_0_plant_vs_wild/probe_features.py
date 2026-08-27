"""Sonde de mesure des features — OUTIL DE DÉVELOPPEMENT.

Pourquoi cette sonde existe : `DEAD_SPIN_FEATURE_WEIGHTS` vaut aujourd'hui
`none` seul, donc AUCUNE feature ne se déclenche d'elle-même. Leur fréquence
n'est pas décidée, et l'inventer fausserait la baseline.

La sonde force donc une feature sur CHAQUE dead spin éligible et mesure ce qui
se passe ensuite. Elle répond à « combien rapporte une feature quand elle part »
et « combien de dead spins seraient éligibles », pas à « à quelle fréquence
doit-elle partir » — cette dernière question reste ouverte.

Elle utilise le vrai `GameState.run_spin` : aucun simulateur parallèle. Elle
n'écrit rien dans `library/` et ne touche pas aux books de la baseline.

    python games/0_0_plant_vs_wild/probe_features.py [--wagers 3000]
"""

import argparse
import json
import os
import statistics
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baseline")

#: Poids de SONDE, à ne pas confondre avec un réglage : une feature part sur
#: chaque dead spin éligible, les trois à parts égales. C'est ce qui donne un
#: échantillon exploitable ; ce n'est pas une proposition de fréquence.
PROBE_WEIGHTS = {"none": 0, "rage": 1, "wildSnake": 1, "wildSplit": 1}

LOW_SYMBOLS = {"L1", "L2", "L3", "L4"}


def measure(wagers: int) -> dict:
    config = GameConfig()
    baseline_weights = dict(config.dead_spin_feature_weights)
    config.dead_spin_feature_weights = PROBE_WEIGHTS

    state = GameState(config)
    state.betmode = "bonus"
    state.criteria = "freegame"

    activations = Counter()
    wins_after = {"rage": [], "wildSnake": [], "wildSplit": []}
    snake_lengths = []
    snake_symbols = Counter()
    free_spins = 0
    eligible_dead_spins = 0

    try:
        for sim in range(wagers):
            state.run_spin(sim)

            feature = None
            win_after = 0.0
            in_freegame = False

            for event in state.book.events:
                kind = event["type"]
                if kind == "reveal":
                    if feature:
                        wins_after[feature].append(win_after)
                    in_freegame = event["gameType"] == "freegame"
                    if in_freegame:
                        free_spins += 1
                    feature = None
                    win_after = 0.0
                elif kind == "wildFeature":
                    feature = event["feature"]
                    activations[feature] += 1
                    eligible_dead_spins += 1
                    if feature == "wildSnake":
                        snake_lengths.append(len(event["path"]) + 1)
                        snake_symbols[event["symbol"]] += 1
                elif kind == "winInfo" and feature:
                    win_after += event["totalWin"] / 100.0

            if feature:
                wins_after[feature].append(win_after)
    finally:
        config.dead_spin_feature_weights = baseline_weights

    lows = sum(count for name, count in snake_symbols.items() if name in LOW_SYMBOLS)
    highs = sum(count for name, count in snake_symbols.items() if name not in LOW_SYMBOLS)

    return {
        "note": (
            "SONDE — une feature est forcée sur chaque dead spin éligible. Les fréquences "
            "réelles ne sont pas décidées ; seules les valeurs conditionnelles ont un sens ici."
        ),
        "probe_weights": PROBE_WEIGHTS,
        "wagers": wagers,
        "bet_mode": "bonus",
        "free_spins_played": free_spins,
        "eligible_dead_spins": eligible_dead_spins,
        "eligible_dead_spin_rate_per_free_spin": round(eligible_dead_spins / max(1, free_spins), 5),
        "features": {
            name: {
                "activations": activations.get(name, 0),
                "average_win_after_x": round(statistics.fmean(wins_after[name]), 3)
                if wins_after[name]
                else None,
                "median_win_after_x": round(statistics.median(wins_after[name]), 3)
                if wins_after[name]
                else None,
                "max_win_after_x": round(max(wins_after[name]), 3) if wins_after[name] else None,
                "share_without_win": round(
                    sum(1 for value in wins_after[name] if value == 0) / len(wins_after[name]), 4
                )
                if wins_after[name]
                else None,
            }
            for name in ("rage", "wildSnake", "wildSplit")
        },
        "snake": {
            "average_path_length": round(statistics.fmean(snake_lengths), 3) if snake_lengths else None,
            "max_path_length": max(snake_lengths) if snake_lengths else None,
            "symbols": dict(sorted(snake_symbols.items())),
            "low_share": round(lows / max(1, lows + highs), 4),
            "high_share": round(highs / max(1, lows + highs), 4),
            "h4_share": round(snake_symbols.get("H4", 0) / max(1, lows + highs), 4),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Sonde features PLANT VS WILD")
    parser.add_argument("--wagers", type=int, default=3000)
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    result = measure(args.wagers)

    with open(os.path.join(OUTPUT_DIR, "feature_probe.json"), "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1, ensure_ascii=False)
        handle.write("\n")

    print(json.dumps(result, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
