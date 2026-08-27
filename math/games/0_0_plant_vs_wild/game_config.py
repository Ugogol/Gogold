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

#: EXPÉRIMENTAL - nombre maximum de cascades enchaînées dans un spin.
#: `None` = aucun plafond (comportement historique).
#:
#: Sémantique quand le plafond est atteint : la résolution en cours est payée
#: normalement, ses multiplicateurs sont appliqués normalement, puis aucune
#: nouvelle cascade n'est engagée. Rien n'est annulé, aucun symbole n'est
#: retiré, aucun gain déjà résolu n'est supprimé — le spin s'arrête simplement
#: de se relancer. Le plafond ne touche NI la progression x2, NI la somme des
#: multiplicateurs, NI le plafond x4096.
MAX_CASCADES_PER_SPIN = None

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


# ── PAYTABLE — BALANCING_V1, NON_FINAL ───────────────────────────────────────
#
# Construite AUTOUR de la mécanique des multiplicateurs, qui est verrouillée :
# une case double à chaque participation et une connexion paie la SOMME des
# multiplicateurs de ses cases. Une valeur de base minuscule y devient énorme —
# 0,10x rencontrant x8+x16+x32+x64 paie déjà 12x.
#
# La paytable est donc volontairement au plus bas :
#
#   * chaque entrée est un multiple de 0,10x, et 0,10x est le PLANCHER absolu.
#     Le RGS refuse tout gain hors de cet incrément (`verify_lookup_format`), et
#     une connexion de 4 cases sans multiplicateur paie exactement la valeur de
#     la case : les entrées ne peuvent donc pas descendre plus bas ;
#   * la ligne de la taille 4 vaut 1 à 8 dixièmes — le minimum pour que les huit
#     symboles restent strictement ordonnés ;
#   * la croissance avec la taille du cluster est douce, et concentrée sur les
#     grandes tailles qui ne se produisent presque jamais. Ce sont les
#     multiplicateurs qui doivent faire exploser les gains, pas le nombre de
#     symboles.
#
# Hiérarchie : L1 < L2 < L3 < L4 < H1 < H2 < H3 < H4 à CHAQUE palier.
# H4 est le plus rémunérateur et reste absent du Base Game (bandes BR0/FR0).
#
# ⚠️ Cette table ne suffit pas à atteindre la cible de RTP — voir
# `baseline/BASELINE.md`, section PAYTABLE_ONLY_FLOOR.

#: Paliers de taille de connexion, en intervalles fermés.
PAYTABLE_TIERS = [
    (MIN_CLUSTER_SIZE, 4),
    (5, 5),
    (6, 6),
    (7, 7),
    (8, 8),
    (9, 9),
    (10, 11),
    (12, 14),
    (15, 19),
    (20, 25),
]

#: Gains en DIXIÈMES de mise — l'unité imposée par le RGS. Une ligne par
#: symbole, une colonne par palier de `PAYTABLE_TIERS`.
PAYTABLE_V1_DIMES = {
    #        4   5   6   7   8   9  10-11 12-14 15-19 20+
    "L1": [  1,  1,  1,  2,  2,  3,   4,    6,    9,   14],
    "L2": [  2,  2,  2,  3,  3,  4,   6,    8,   12,   18],
    "L3": [  3,  3,  4,  4,  5,  6,   8,   11,   16,   24],
    "L4": [  4,  4,  5,  6,  7,  8,  11,   15,   21,   32],
    "H1": [  5,  6,  7,  8,  9, 11,  14,   19,   27,   40],
    "H2": [  6,  7,  8, 10, 12, 14,  18,   24,   34,   50],
    "H3": [  7,  8, 10, 12, 14, 17,  22,   29,   41,   62],
    "H4": [  8, 10, 12, 14, 17, 20,  26,   35,   49,   74],
}


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

        # BALANCING_V1 — NON_FINAL. Voir PAYTABLE_TIERS / PAYTABLE_V1_DIMES.
        pay_group = {}
        for symbol, row in PAYTABLE_V1_DIMES.items():
            for tier, dimes in zip(PAYTABLE_TIERS, row):
                pay_group[(tier, symbol)] = dimes / 10.0
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
        self.max_cascades_per_spin = MAX_CASCADES_PER_SPIN
        self.refill_reels = {self.basegame_type: "BR1", self.freegame_type: "FR1"}
        self.snake_symbol_weights = SNAKE_SYMBOL_WEIGHTS
        self.dead_spin_feature_weights = DEAD_SPIN_FEATURE_WEIGHTS

        #: H4 n'apparaît qu'en Bonus. Garanti par les bandes : BR0 n'en contient
        #: aucun, FR0 en contient. Vérifié par les tests.
        # ── BANDES — BALANCING_V2, NON_FINAL ─────────────────────────────────────
#
# BR0/FR0 (reveal)  concentrees : L2 et L3 a 20 %, ce qui maintient un premier
#                   hit accessible (~14-17 %).
# BR1/FR1 (refill)  uniformes sur tous les symboles payants, Wild tres rare.
#                   Les cases liberees ne reforment donc presque jamais une
#                   connexion immediate, et le multiplicateur s empile beaucoup
#                   moins sur les memes cases.
#
# Effet mesure a hit rate egal (16.7 %) : RTP 15.74 -> 8.95, clusterMult
# 134 -> 66, wincap 1/556 -> 1/1429. Voir baseline/BASELINE.md.
#
#: Deux reelsets par mode : `*R0` pour le reveal, `*R1` pour les refills
        #: après tumble. Séparer les deux est le levier qui découple le premier
        #: hit (qu'on veut accessible) de la reconnexion (qu'on veut rare).
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "BR1": "BR1.csv", "FR1": "FR1.csv"}
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
