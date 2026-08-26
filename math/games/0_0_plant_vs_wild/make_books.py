"""Génère les Books canoniques de PLANT VS WILD.

Ce ne sont PAS des simulations : chaque book est produit par le vrai
`GameState.run_spin`, mais avec un plateau imposé ou un numéro de simulation
fixé. Relancer ce script redonne exactement les mêmes fichiers.

Ils servent de référence commune entre le Math et le frontend, et seront
injectés dans le Debug Playground à l'étape suivante.

    python games/0_0_plant_vs_wild/make_books.py     (depuis math/)
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402

#: Dossier volontairement nommé `canonical_books` et non `books` : la règle
#: `**/books/*` de `math/.gitignore` vise les sorties de simulation et
#: exclurait ces fichiers, qui eux doivent être versionnés.
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canonical_books")

#: Symboles de remplissage. Quatre valeurs suffisent pour qu'aucune case voisine
#: ne se ressemble : le plateau ne contient alors aucune connexion.
FILLERS = ("L1", "L2", "L3", "L4")


def neutral_board():
    """Plateau 5x5 sans la moindre connexion."""
    return [[FILLERS[(reel + 2 * row) % 4] for row in range(5)] for reel in range(5)]


def place(board, positions, name):
    for reel, row in positions:
        board[reel][row] = name
    return board


def new_game(mode, criteria):
    state = GameState(GameConfig())
    state.betmode = mode
    state.criteria = criteria
    return state


def forced_book(board, features=None, seed=0, mode="base", criteria="basegame", sim=0):
    """Un spin joué sur un plateau imposé."""
    state = new_game(mode, criteria)
    state.force(boards=[board], features=features, seed=seed)
    # `force` fixe la graine ; `run_spin` la refixe sur le numéro de simulation.
    state.run_spin(sim, simulation_seed=seed)
    return state.book.to_json()


def simulated_book(mode, criteria, sim, features=None):
    """Un spin joué normalement, dont le numéro fixe la graine."""
    state = new_game(mode, criteria)
    if features:
        state.force(features=features, seed=sim)
    state.run_spin(sim)
    return state.book.to_json()


def find_sim(mode, criteria, predicate, candidates=range(400), features=None):
    """Premier numéro de simulation satisfaisant un critère de forme.

    La recherche est déterministe et le numéro retenu est écrit dans le fichier
    produit : le book reste reproductible sans rejouer la recherche.
    """
    for sim in candidates:
        book = simulated_book(mode, criteria, sim, features=features)
        if predicate([event["type"] for event in book["events"]], book):
            return sim, book
    raise RuntimeError("aucune simulation ne satisfait le critère")


def count(types, name):
    return types.count(name)


def build():
    """Construit les onze books canoniques."""
    books = {}

    # ── Base Game ───────────────────────────────────────────────────────────
    books["math-base-no-win"] = forced_book(neutral_board())

    cluster = place(neutral_board(), [(0, 0), (0, 1), (1, 0), (1, 1)], "H1")
    books["math-simple-cluster"] = forced_book(cluster, seed=1)

    wild_cluster = place(place(neutral_board(), [(0, 0), (0, 1), (1, 0)], "H1"), [(1, 1)], "W")
    books["math-wild-connection"] = forced_book(wild_cluster, seed=1)

    sim, book = find_sim(
        "base",
        "basegame",
        lambda types, _: count(types, "tumbleBoard") >= 3 and "freeSpinTrigger" not in types,
    )
    books["math-multi-cascade"] = book

    def reaches_x4(_types, book):
        grids = [e["gridMultipliers"] for e in book["events"] if e["type"] == "updateGrid"]
        return bool(grids) and max(max(row) for row in grids[-1]) >= 4

    sim, book = find_sim("base", "basegame", reaches_x4)
    books["math-multipliers"] = book

    sim, book = find_sim("base", "basegame", lambda types, _: "freeSpinTrigger" in types)
    books["math-bonus-trigger"] = book

    # ── Bonus ───────────────────────────────────────────────────────────────
    sim, book = find_sim(
        "bonus",
        "freegame",
        lambda types, _: "freeSpinRetrigger" not in types,
        candidates=range(60),
    )
    books["math-free-spins"] = book

    sim, book = find_sim(
        "bonus",
        "freegame",
        lambda types, _: "freeSpinRetrigger" in types,
        candidates=range(60),
    )
    books["math-retrigger"] = book

    # ── Features ────────────────────────────────────────────────────────────
    for name, feature in (
        ("math-rage", "rage"),
        ("math-snake", "wildSnake"),
        ("math-split", "wildSplit"),
    ):
        sim, book = find_sim(
            "bonus",
            "freegame",
            lambda types, _: count(types, "wildFeature") == 1,
            candidates=range(60),
            features=[feature],
        )
        books[name] = book

    return books


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    books = build()

    index = []
    for name, book in books.items():
        path = os.path.join(OUTPUT_DIR, name + ".json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(book, handle, indent=1)
            handle.write("\n")
        index.append(
            {
                "name": name,
                "events": len(book["events"]),
                "payoutMultiplier": book["payoutMultiplier"],
            }
        )
        print(f"{name:24} {len(book['events']):4} events   payout {book['payoutMultiplier']}")

    with open(os.path.join(OUTPUT_DIR, "index.json"), "w", encoding="utf-8") as handle:
        json.dump({"gameId": GameConfig().game_id, "books": index}, handle, indent=1)
        handle.write("\n")


if __name__ == "__main__":
    main()
