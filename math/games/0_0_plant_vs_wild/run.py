"""Simulation de PLANT VS WILD.

Aucun optimizer, aucune cible de RTP : ce run MESURE le jeu tel qu'il est. Les
chiffres produits décrivent la paytable TEST_ONLY et les paramètres de
balancing actuels — ils ne valident rien.

    python games/0_0_plant_vs_wild/run.py                      (depuis math/)
    python games/0_0_plant_vs_wild/run.py --base 50000 --bonus 10000

Reproductible : le SDK dérive la graine de chaque simulation de son numéro
(`simulation_seeds = range(n)`) et fige la répartition des criteria avec
`random.seed(0)`. À configuration et volumes identiques, les books sont
identiques.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402
from src.state.run_sims import create_books  # noqa: E402
from src.write_data.write_configs import generate_configs  # noqa: E402
from utils.rgs_verification import execute_all_tests  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="Simulation PLANT VS WILD")
    parser.add_argument("--base", type=int, default=50000, help="wagers du mode base")
    parser.add_argument("--bonus", type=int, default=10000, help="wagers du mode bonus")
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="lance l'optimizer officiel Stake sur les modes générés",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    num_threads = 1
    # Défaut upstream connu : `GeneralGameState._payout_ints` n'est remis à zéro
    # ni entre deux batches, ni entre deux bet modes. Le fichier
    # `books_<mode>.verification.json` cumule alors les payouts et fait échouer
    # `execute_all_tests`, alors que les books et la lookup table sont corrects
    # et rigoureusement identiques (vérifié). `math/src/` étant traité comme
    # upstream, on contourne : un seul batch, et un gamestate neuf par bet mode.
    compression = True
    profiling = False

    num_sim_args = {"base": args.base, "bonus": args.bonus}
    # Un seul batch par mode : voir le défaut upstream décrit ci-dessus.
    batching_size = max(num_sim_args.values()) + 1

    config = GameConfig()

    if args.optimize:
        # Doit être posé AVANT toute écriture de configuration.
        from game_optimization import OptimizationSetup

        OptimizationSetup(config)

    for mode, sims in num_sim_args.items():
        create_books(
            GameState(config), config, {mode: sims}, batching_size, num_threads, compression, profiling
        )

    generate_configs(GameState(config))

    if args.optimize:
        # Optimizer OFFICIEL Stake. Il ne cherche que les POIDS de la lookup
        # table : il ne touche ni aux books, ni aux payouts, ni aux mécaniques.
        #
        # `math_config.json` ne contient les sections d'optimisation que si
        # `opt_params` existe DÉJÀ au moment où il est écrit — sinon le binaire
        # Rust ne trouve pas le bet mode. On repasse donc par `generate_configs`
        # une fois le setup posé, comme le fait le sample Stake.
        from optimization_program.run_script import OptimizationExecution

        generate_configs(GameState(config))
        OptimizationExecution().run_all_modes(config, ["base"], num_threads)
        generate_configs(GameState(config))

    # Contrôle de format Stake sur les fichiers produits : cohérence entre les
    # books et les lookup tables. C'est l'outil du SDK, pas un contrôle maison.
    execute_all_tests(config)
