"""Configuration du jeu PLANT VS WILD."""

import os

from src.config.config import Config
from src.config.betmode import BetMode
from src.config.distributions import Distribution

#: Identifiant de DÉVELOPPEMENT. Stake n'a pas encore attribué le vrai game_id.
#: Centralisé ici : ne pas le recopier ailleurs.
DEV_GAME_ID = "0_0_plant_vs_wild"


# ═════════════════════════════════════════════════════════════════════════════
# NIVEAU A — IDENTITÉ DU JEU
#
# Ce qui fait que PLANT VS WILD est PLANT VS WILD. Ces règles ne se règlent
# pas : les toucher change le jeu, pas son équilibre. Chacune est verrouillée
# par un test de `math/tests/plant_vs_wild/`.
#
#   grille 5x5 · connexion minimum 4
#   multiplicateur implicite d'une case = x1
#   une connexion paie la SOMME des multiplicateurs de ses cases
#   ordre PAY -> UPGRADE : on paie à la valeur courante, la case double ensuite
#   progression x1 -> x2 -> x4 -> ... -> x4096
#   multiplicateurs persistants entre les Free Spins
#   Wild principal : charge et déplacement
# ═════════════════════════════════════════════════════════════════════════════

#: Taille minimale d'une connexion.
MIN_CLUSTER_SIZE = 4

#: Plafond du multiplicateur d'une case.
MAX_POSITION_MULT = 4096


# ═════════════════════════════════════════════════════════════════════════════
# NIVEAU B — RÈGLES DE GAMEPLAY
#
# Le design actuel, et il ne bouge pas sans décision explicite. Mais ce ne sont
# PAS des invariants d'identité : ces règles pourront être rediscutées.
#
#   4 connexions Wild en Base -> Bonus       10 Free Spins
#   4 connexions Wild dans un FS -> +5       features sur dead spin
#   H4 réservé au Bonus
# ═════════════════════════════════════════════════════════════════════════════

#: Nombre de connexions du Wild menant au Bonus, puis au retrigger.
WILD_MAX_CHARGE = 4


# ═════════════════════════════════════════════════════════════════════════════
# NIVEAU C — PARAMÈTRES DE BALANCING
#
# Tout ce qui suit se règle. Rien ici n'est une règle de jeu.
#
#   paytable · bandes BR0/BR1/FR0/FR1 · densité du Wild en Base et en Bonus
#   MAX_CASCADES_PER_SPIN · poids des features · poids du symbole du Snake
#   WILD_SPLIT_EXTRA_WILDS · plafond de gain
#
# Le levier principal reste les BANDES : elles portent la distribution des
# symboles et la fréquence d'apparition du Wild, au reveal comme au refill.
# Cette distribution n'est volontairement dupliquée nulle part.
# ═════════════════════════════════════════════════════════════════════════════

#: Plafond de gain d'un pari. Mécanisme Stake standard (`config.wincap`) :
#: le SDK émet un event `wincap` et borne le payout.
MAX_WIN = 10_000.0

#: Nombre de Wild temporaires produits par le Wild Split. Le concept — des Wild
#: temporaires, à usage unique, distincts du Wild principal — est une règle ;
#: leur NOMBRE est un paramètre.
WILD_SPLIT_EXTRA_WILDS = 3

#: EXPÉRIMENTAL - nombre maximum de cascades enchaînées dans un spin.
#: `None` = aucun plafond (comportement historique).
#:
#: Sémantique quand le plafond est atteint : la résolution en cours est payée
#: normalement, ses multiplicateurs sont appliqués normalement, puis aucune
#: nouvelle cascade n'est engagée. Rien n'est annulé, aucun symbole n'est
#: retiré, aucun gain déjà résolu n'est supprimé — le spin s'arrête simplement
#: de se relancer. Le plafond ne touche NI la progression x2, NI la somme des
#: multiplicateurs, NI le plafond x4096.
MAX_CASCADES_PER_SPIN = 3

#: TEST_ONLY - longueur (min, max) du trajet du Wild Snake, en pas.
#: Le minimum de 3 garantit un groupe de 4 cases converties : le contrat
#: frontend exige un trajet non vide et la connexion doit exister.
SNAKE_PATH_LENGTH = (3, 5)

#: TEST_ONLY - symbole vers lequel le Wild Snake rampe.
#:
#: Poids uniformes pour l'instant : le partage Low/High et la rareté de H4 ne
#: sont PAS décidés. H4 est absent du Base Game, comme partout ailleurs.
SNAKE_SYMBOL_WEIGHTS = {
    #: Low 65 % / High 35 %. Parmi les High : H1 > H2 > H3 >>> H4.
    "basegame": {"L1": 16.25, "L2": 16.25, "L3": 16.25, "L4": 16.25, "H1": 16, "H2": 11, "H3": 8},
    "freegame": {
        "L1": 16.25, "L2": 16.25, "L3": 16.25, "L4": 16.25,
        "H1": 15, "H2": 10, "H3": 8, "H4": 2,
    },
}

#: BALANCING_V3 - feature tirée sur un dead spin éligible du Bonus.
#:
#: Rage la plus fréquente, Snake la plus rare : elle fabrique directement une
#: connexion, donc un gain quasi certain.
#:
#: Réglées par COMPARAISON APPARIÉE — mêmes graines pour tous les candidats.
#: L'écart entre deux jeux de poids se mesure de façon fiable ; le NIVEAU absolu
#: du RTP, non. Mesuré sur 120 000 wagers :
#:     1.5/1.0/0.4  -> référence
#:     2.1/1.4/0.55 -> +0.014
#:     2.4/1.6/0.65 -> +0.037   <- retenu
#: Appliqué à la meilleure estimation absolue (0.9291 sur 400 000 wagers), cela
#: place le RTP autour de 0.966 et remonte la moyenne du Bonus de 61x à 64x.
#:
#: `none` seul : AUCUNE fréquence de feature n'est décidée à ce stade, donc
#: aucune ne se déclenche d'elle-même. Les tests et les books canoniques
#: forcent la feature explicitement. C'est LE paramètre à trancher avant
#: l'optimisation.
# ── POPULATION D'OPTIMISATION — ni identite, ni gameplay, ni balancing ──────
#
# Ces valeurs ne decrivent PAS le jeu : elles disent seulement combien de books
# de chaque sorte la simulation doit produire pour que l'optimizer ait de quoi
# travailler. La probabilite reelle de chaque issue est fixee ensuite par les
# POIDS de la lookup table, pas par ces quotas.
#
# Le run precedent n'avait qu'un seul criteria couvrant tous les paris :
# l'optimizer traitait 100 000 books comme une population interchangeable et
# detruisait la forme du jeu. Les quotas ci-dessous garantissent au contraire
# une population reelle dans chaque categorie, y compris les rares.
WINCAP_QUOTA = 0.01
FREEGAME_QUOTA = 0.30
ZERO_QUOTA = 0.34
BASEGAME_QUOTA = 0.35

#: Bornes de classement des Bonus, en multiplicateurs de mise. Convention :
#: INTERVALLE FERME A GAUCHE, OUVERT A DROITE. Un Book tombe donc dans un seul
#: bucket, et tout Book Bonus est classable. Le classement porte sur le payout
#: TOTAL du round (spin declencheur + Free Spins), jamais sur le seul Bonus :
#: c'est ce total que la lookup table pondere.
BONUS_BUCKET_BOUNDS = {"low": (0.0, 20.0), "medium": (20.0, 100.0),
                       "high": (100.0, 500.0), "mega": (500.0, MAX_WIN)}

DEAD_SPIN_FEATURE_WEIGHTS = {"none": 95.35, "rage": 2.4, "wildSplit": 1.6, "wildSnake": 0.65}


# ── PAYTABLE — BALANCING_V3_1, NON_FINAL ───────────────────────────────────────
#
# Même structure que BALANCING_V1, ramenée au niveau qu'impose la mécanique :
# une case double à chaque participation et une connexion paie la SOMME des
# multiplicateurs de ses cases. Quatre cases vierges paient déjà x4.
#
# ⚠️ CONTRAINTE STRUCTURELLE : le RGS impose des gains multiples de 0,10x, et
# 0,10x est donc le plancher absolu d'une entrée. À ce niveau de paytable, les
# petites tailles de connexion sont écrasées contre ce plancher : la hiérarchie
# reste NON DÉCROISSANTE mais n'est plus strictement croissante sur les premiers
# paliers. C'est le prix du plancher, pas un choix de design — voir le rapport
# de l'étape 16.
#
# L'ordre L1 <= L2 <= L3 <= L4 <= H1 <= H2 <= H3 <= H4 est conservé partout, H4
# reste le plus rémunérateur et absent du Base Game (bandes BR0/BR1).

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
#: Courbe LOW COMMUNE. Décision de design : les quatre Low forment un seul
#: niveau économique. Ils gardent des distributions et des identités visuelles
#: différentes, mais paient exactement pareil.
#:
#: Dérivée de V3 par MOYENNE PONDÉRÉE PAR L'EXPOSITION RÉELLE — pour chaque
#: palier, la moyenne des valeurs L1..L4 de V3 pondérée par la somme des
#: `clusterMult` que chaque symbole y a réellement produite sur 80 000 wagers.
#: C'est ce qui perturbe le moins le RTP. Les paliers 12+ n'ont aucune
#: exposition mesurée (de telles connexions n'arrivent jamais) : ils reprennent
#: la moyenne simple des quatre courbes V3.
LOW_DIMES = [1, 1, 1, 1, 1, 2, 4, 5, 6, 10]

PAYTABLE_V3_1_DIMES = {
    #        4   5   6   7   8   9  10-11 12-14 15-19 20+
    "L1": LOW_DIMES,
    "L2": LOW_DIMES,
    "L3": LOW_DIMES,
    "L4": LOW_DIMES,
    "H1": [  2,  3,  3,  4,  4,  5,   6,    9,   12,   18],
    "H2": [  3,  3,  4,  5,  5,  6,   8,   11,   15,   23],
    "H3": [  3,  4,  5,  5,  6,  8,  10,   13,   18,   28],
    "H4": [  4,  5,  5,  6,  8,  9,  12,   16,   22,   33],
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
        self.wincap = MAX_WIN
        self.win_type = "cluster"
        self.rtp = 0.96
        self.construct_paths()

        # Grille 5x5.
        self.num_reels = 5
        self.num_rows = [5] * self.num_reels

        # BALANCING_V3_1 — NON_FINAL. Voir PAYTABLE_TIERS / PAYTABLE_V3_1_DIMES.
        pay_group = {}
        for symbol, row in PAYTABLE_V3_1_DIMES.items():
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
        self.wild_split_extra_wilds = WILD_SPLIT_EXTRA_WILDS
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
                #: ORDRE SIGNIFICATIF. L'optimizer traite les fences dans l'ordre
                #: des criteria et RETIRE les books au fur et a mesure : le
                #: criteria attrape-tout doit venir en dernier, sinon il vide la
                #: table avant les autres. Meme ordre que le sample officiel.
                distributions=[
                    Distribution(
                        criteria="wincap",
                        quota=WINCAP_QUOTA,
                        win_criteria=self.wincap,
                        conditions={
                            #: Le sample officiel atteint le plafond avec une bande
                            #: dediee (WCAP). Mesure ici : FR1, deja presente, y
                            #: parvient 1,07 % du temps contre 0,00 % pour FR0
                            #: (1500 Bonus forces chacun). Une bande de plus serait
                            #: donc inutile. C'est coherent avec l'etape 15 : un
                            #: reveal disperse concentre les gains autour du Wild.
                            #: Ce melange ne sert QU'a peupler le criteria `wincap` ;
                            #: la probabilite reelle du Max Win est fixee ensuite
                            #: par le poids de la lookup table.
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1, "FR1": 5},
                            },
                            "force_wincap": True,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="freegame",
                        quota=FREEGAME_QUOTA,
                        conditions={
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_wincap": False,
                            "force_freegame": True,
                        },
                    ),
                    Distribution(
                        criteria="0",
                        quota=ZERO_QUOTA,
                        win_criteria=0.0,
                        conditions={
                            #: PLANT VS WILD declenche le Bonus sur la 4e connexion
                            #: du Wild, pas sur des scatters : meme sans
                            #: `force_freegame`, un round peut y entrer. Les bandes
                            #: du Bonus doivent donc etre declarees ici aussi.
                            "reel_weights": {
                                self.basegame_type: {"BR0": 1},
                                self.freegame_type: {"FR0": 1},
                            },
                            "force_wincap": False,
                            "force_freegame": False,
                        },
                    ),
                    Distribution(
                        criteria="basegame",
                        quota=BASEGAME_QUOTA,
                        conditions={
                            #: PLANT VS WILD declenche le Bonus sur la 4e connexion
                            #: du Wild, pas sur des scatters : meme sans
                            #: `force_freegame`, un round peut y entrer. Les bandes
                            #: du Bonus doivent donc etre declarees ici aussi.
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
