"""Run minimal de PLANT VS WILD.

Volontairement modeste : à ce stade le jeu doit être MÉCANIQUEMENT correct, pas
équilibré. Aucun optimizer, aucune cible de RTP, aucune fréquence finale — ces
étapes viendront quand les règles seront figées.

    python games/0_0_plant_vs_wild/run.py            (depuis math/)
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402
from src.state.run_sims import create_books  # noqa: E402
from src.write_data.write_configs import generate_configs  # noqa: E402
from utils.rgs_verification import execute_all_tests  # noqa: E402

if __name__ == "__main__":
    num_threads = 1
    # Défaut upstream connu : `GeneralGameState._payout_ints` n'est remis à zéro
    # ni entre deux batches, ni entre deux bet modes. Le fichier
    # `books_<mode>.verification.json` cumule alors les payouts et fait échouer
    # `execute_all_tests`, alors que les books et la lookup table sont corrects
    # et rigoureusement identiques (vérifié). `math/src/` étant traité comme
    # upstream, on contourne : un seul batch, et un gamestate neuf par bet mode.
    batching_size = 500
    compression = True
    profiling = False

    # Petit volume : de quoi vérifier que la chaîne complète produit des
    # fichiers valides, pas de quoi mesurer quoi que ce soit.
    num_sim_args = {"base": 200, "bonus": 50}

    config = GameConfig()

    for mode, sims in num_sim_args.items():
        create_books(
            GameState(config), config, {mode: sims}, batching_size, num_threads, compression, profiling
        )

    generate_configs(GameState(config))

    # Contrôle de format Stake sur les fichiers produits : cohérence entre les
    # books et les lookup tables. C'est l'outil du SDK, pas un contrôle maison.
    execute_all_tests(config)
