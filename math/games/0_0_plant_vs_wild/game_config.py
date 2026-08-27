"""Configuration du jeu PLANT VS WILD."""

import os

from src.config.config import Config
from src.config.betmode import BetMode
from src.config.distributions import Distribution

#: Identifiant de DÉVELOPPEMENT. Stake n'a pas encore attribué le vrai game_id.
#: Centralisé ici : ne pas le recopier ailleurs.
DEV_GAME_ID = "0_0_plant_vs_wild"

#: Nombre de connexions du Wild menant au Bonus.
WILD_MAX_CHARGE = 4

#: Taille minimale d'une connexion.
MIN_CLUSTER_SIZE = 4

#: Plafond du multiplicateur de case.
MAX_POSITION_MULT = 4096

#: Nombre de Wild temporaires produits par le Wild Split.
SPLIT_WILD_COUNT = 3

# ─────────────────────────────────────────────────────────────────────────────
# PARAMÈTRES DE BALANCING
#
# Tout ce qui suit est destiné à être RÉGLÉ. Les règles mécaniques — 5x5,
# connexion minimum 4, progression x2 -> x4096, 10 Free Spins, retrigger +5,
# une seule feature par dead spin, H4 réservé au Bonus — ne sont PAS des
# paramètres : ce sont des invariants, vérifiés par math/tests/plant_vs_wild/.
#
# Le levier principal reste les BANDES (`reels/BR0.csv`, `reels/FR0.csv`) :
# elles portent à elles seules la distribution des symboles, la fréquence
# d'apparition du Wild au reveal comme au refill, et le symbole tiré lors d'un
# remplacement. Cette distribution n'est volontairement dupliquée nulle part.
#
# La paytable est TEST_ONLY : voir plus bas dans `GameConfig`.
# ─────────────────────────────────────────────────────────────────────────────

#: TEST_ONLY - longueur (min, max) du trajet du Wild Snake, en pas.
#: Le minimum de 3 garantit un groupe de 4 cases converties : le contrat
#: frontend exige un trajet non vide et la connexion doit exister.
SNAKE_PATH_LENGTH = (3, 5)

#: TEST_ONLY - symbole vers lequel le Wild Snake rampe.
#:
#: Poids uniformes pour l'instant : le partage Low/High et la rareté de H4 ne
#: sont PAS décidés. H4 est absent du Base Game, comme partout ailleurs.
SNAKE_SYMBOL_WEIGHTS = {
    "basegame": {"L1": 1, "L2": 1, "L3": 1, "L4": 1, "H1": 1, "H2": 1, "H3": 1},
    "freegame": {"L1": 1, "L2": 1, "L3": 1, "L4": 1, "H1": 1, "H2": 1, "H3": 1, "H4": 1},
}

#: TEST_ONLY - feature tirée sur un dead spin éligible du Bonus.
#:
#: `none` seul : AUCUNE fréquence de feature n'est décidée à ce stade, donc
#: aucune ne se déclenche d'elle-même. Les tests et les books canoniques
#: forcent la feature explicitement. C'est LE paramètre à trancher avant
#: l'optimisation.
DEAD_SPIN_FEATURE_WEIGHTS = {"none": 1, "rage": 0, "wildSnake": 0, "wildSplit": 0}


class GameConfig(Config):
    """Configuration singleton de PLANT VS WILD."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = DEV_GAME_ID
        self.provider_number = 0
        self.working_name = "Plant vs Wild"
        self.wincap = 5000.0
        self.win_type = "cluster"
        self.rtp = 0.96
        self.construct_paths()

        # Grille 5x5.
        self.num_reels = 5
        self.num_rows = [5] * self.num_reels

        # TEST_ONLY — aucune paytable définitive. Le SDK exige des payouts pour
        # évaluer un cluster ; ces valeurs n'engagent aucun RTP et seront
        # remplacées pendant le balancing.
        #
        # Contrainte de FORMAT, elle non négociable : le RGS n'accepte que des
        # gains par incréments de 0,10x (`verify_lookup_format`). Bases et
        # paliers restent donc des multiples de 0,10 et des entiers.
        t1, t2, t3, t4 = (MIN_CLUSTER_SIZE, 5), (6, 8), (9, 12), (13, 25)
        pay_group = {}
        for symbol, base in (
            ("H1", 5.0),
            ("H2", 2.5),
            ("H3", 1.5),
            ("H4", 1.0),
            ("L1", 0.6),
            ("L2", 0.4),
            ("L3", 0.3),
            ("L4", 0.2),
        ):
            pay_group[(t1, symbol)] = base
            pay_group[(t2, symbol)] = base * 2
            pay_group[(t3, symbol)] = base * 5
            pay_group[(t4, symbol)] = base * 10
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True
        # Aucun scatter : le Bonus se déclenche sur la 4e connexion du Wild.
        self.special_symbols = {"wild": ["W"]}

        # PLANT VS WILD ne déclenche pas sur des scatters. Le dictionnaire reste
        # présent parce que le SDK le lit, mais la condition réelle est
        # `bonus_pending` — voir GameStateOverride.check_fs_condition.
        self.freespin_triggers = {
            self.basegame_type: {WILD_MAX_CHARGE: 10},
            self.freegame_type: {WILD_MAX_CHARGE: 5},
        }
        self.anticipation_triggers = {
            self.basegame_type: WILD_MAX_CHARGE,
            self.freegame_type: WILD_MAX_CHARGE,
        }

        self.maximum_board_mult = MAX_POSITION_MULT
        self.split_wild_count = SPLIT_WILD_COUNT
        self.snake_path_length = SNAKE_PATH_LENGTH
        self.snake_symbol_weights = SNAKE_SYMBOL_WEIGHTS
        self.dead_spin_feature_weights = DEAD_SPIN_FEATURE_WEIGHTS

        #: H4 n'apparaît qu'en Bonus. Garanti par les bandes : BR0 n'en contient
        #: aucun, FR0 en contient. Vérifié par les tests.
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv"}
        self.reels = {}
        for name, filename in reels.items():
            self.reels[name] = self.read_reels_csv(os.path.join(self.reels_path, filename))

        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=[
                    Distribution(
                        criteria="basegame",
                        quota=1.0,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                ],
            ),
            BetMode(
                name="bonus",
                cost=100.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=True,
                distributions=[
                    Distribution(
                        criteria="freegame",
                        quota=1.0,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                ],
            ),
        ]
