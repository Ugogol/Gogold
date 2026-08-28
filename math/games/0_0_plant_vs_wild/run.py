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
        "--modes",
        default="base,bonus",
        help="bet modes a (re)generer, separes par des virgules",
    )
    parser.add_argument(
        "--reuse-books",
        action="store_true",
        help="repart des books deja generes au lieu de les recalculer",
    )
    parser.add_argument(
        "--opt-modes",
        default="base",
        help="bet modes a optimiser, separes par des virgules",
    )
    parser.add_argument(
        "--opt-threads",
        type=int,
        default=4,
        help="threads de l'optimizer (voir la note sur les chaines de records)",
    )
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

    # GARDE-FOU. Regenerer un mode ECRASE ses books. Le mode `base` est gele sur
    # BALANCING_V5 : `--modes bonus` permet de travailler le Bonus Buy sans
    # jamais toucher a ses artefacts.
    wanted = {m.strip() for m in args.modes.split(",") if m.strip()}
    unknown = wanted - set(num_sim_args)
    if unknown:
        raise SystemExit(f"bet mode inconnu : {sorted(unknown)}")

    if not args.reuse_books:
        for mode, sims in ((m, n) for m, n in num_sim_args.items() if m in wanted):
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
        # THREADS DE L'OPTIMIZER — distinct de ceux de la generation de books.
        #
        # `create_show_pigs` ne garde une distribution que si son score bat le
        # meilleur precedent : `show_pigs` n'est donc pas un echantillon mais une
        # CHAINE DE RECORDS, dont la longueur croit en ln(nombre de tirages).
        # Mesure : 2 000 tirages -> 5 records, 5 000 -> 6.
        #
        # Or la boucle d'affichage du SDK indexe `show_pigs[0..10]` en dur
        # (`main.rs:261`) : moins de 10 records et le binaire panique. Chaque
        # thread construisant sa PROPRE chaine, augmenter les threads est le
        # levier fiable — et il ne touche pas au SDK.
        opt_modes = [m.strip() for m in args.opt_modes.split(",") if m.strip()]
        OptimizationExecution().run_all_modes(config, opt_modes, args.opt_threads)
        generate_configs(GameState(config))

    # Contrôle de format Stake sur les fichiers produits : cohérence entre les
    # books et les lookup tables. C'est l'outil du SDK, pas un contrôle maison.
    execute_all_tests(config)
