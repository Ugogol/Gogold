"""Paramètres de l'optimizer officiel Stake pour PLANT VS WILD.

L'optimizer ne touche NI aux books, NI aux payouts, NI aux mécaniques : il
cherche les POIDS de la lookup table qui amènent le RTP à la cible. Vérifié
dans le code Rust local : les deux seuls points d'écriture font
`value.weight = …`, jamais `value.win`.

Le mode `base` de PLANT VS WILD n'a qu'un seul criteria — `basegame` — et le
validateur du SDK l'accepte : il exige seulement que les criteria des
distributions soient couverts par les `conditions`, et que la somme de leurs
RTP égale celui du bet mode.
"""

from optimization_program.optimization_config import (
    ConstructConditions,
    ConstructParameters,
    ConstructScaling,
    verify_optimization_input,
)


class OptimizationSetup:
    """Conditions d'optimisation, par bet mode."""

    def __init__(self, game_config):
        self.game_config = game_config

        #: FRÉQUENCE du criteria, pas hit rate du jeu. `hr` dit à l'optimizer
        #: « ce criteria survient 1 fois sur N ». Le mode `base` n'ayant qu'un
        #: seul criteria, il couvre TOUS les paris : sa fréquence vaut 1.
        #:
        #: Une première tentative avec hr = 10.6 (le hit rate observé) a produit
        #: un RTP pondéré de 10.176, soit exactement 0.96 x 10.6 — l'optimizer
        #: avait réparti 0.96 sur un dixième de la masse seulement.
        criteria_frequency = 1.0

        self.game_config.opt_params = {
            "base": {
                "conditions": {
                    "basegame": ConstructConditions(
                        rtp=game_config.rtp, hr=criteria_frequency
                    ).return_dict(),
                },
                #: Aucune mise à l'échelle : on ne veut pas déformer la forme
                #: obtenue au balancing, seulement fermer le RTP.
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": ConstructParameters(
                    num_show=2000,
                    num_per_fence=5000,
                    min_m2m=2,
                    max_m2m=60,
                    pmb_rtp=1.0,
                    sim_trials=2000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                ).return_dict(),
            },
        }

        verify_optimization_input(self.game_config, self.game_config.opt_params)
