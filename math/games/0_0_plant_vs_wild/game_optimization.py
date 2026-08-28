"""Conditions de l'optimizer officiel Stake pour PLANT VS WILD.

L'optimizer ne touche NI aux books, NI aux payouts, NI aux mécaniques : il
cherche les POIDS de la lookup table. Vérifié dans le code Rust local : les deux
seuls points d'écriture font `value.weight = ...`, jamais `value.win`.

POURQUOI HUIT FENCES
--------------------
Le premier candidat n'avait qu'un seul criteria couvrant tous les paris. Le RTP
tombait juste (0.960000) mais l'optimizer, libre de traiter 100 000 Books comme
une population interchangeable, avait détruit la forme du jeu : hit rate 50 %,
Bonus 1/53, médiane 32.9x, P(Max Win) = 0. Candidat rejeté.

Chaque fence porte donc une cible de RTP ET de fréquence. L'optimizer ne peut
plus financer le RTP en gonflant les petits gains de base : la place de chacun
est bornée.

COMMENT UNE FENCE ATTRAPE SES BOOKS (relevé dans `main.rs`)
-----------------------------------------------------------
`sort_wins_by_parameter` traite les fences DANS L'ORDRE et RETIRE les Books
attribués. Trois modes, selon `search_conditions` :

    nombre        -> fence "payout exact" : Books dont le win vaut ce nombre.
    dictionnaire  -> fence "force record" : Books portant ces clés.
    rien          -> attrape-tout : tout ce qui reste.

Un intervalle `(min, max)` N'EST PAS un filtre de payout dans cette version :
`win_type` n'est vrai que si `min == max`, sinon la branche de repli matche des
clés vides et ramasse tout. Les Bonus sont donc segmentés par CLÉ DE FORCE,
inscrite par `GameStateOverride.record_optimization_criteria`.

L'ORDRE EST SIGNIFICATIF
------------------------
1 983 Books sont à la fois "payout 0" et "Bonus faible" : un Bonus s'est produit
sans rien rapporter. Les fences Bonus passent AVANT `0` pour qu'ils restent
comptés comme des Bonus. Et l'attrape-tout `basegame` passe en DERNIER, sinon il
vide la table.

Une fence sans Book fait sortir l'optimizer en erreur (`exit_if_fence_has_no_books`) :
aucune fence "filet de sécurité" n'est donc déclarée. Les huit sont peuplées,
mesure à l'appui — voir `criteria_population.py`.
"""

from optimization_program.optimization_config import (
    ConstructConditions,
    ConstructParameters,
    ConstructScaling,
    verify_optimization_input,
)

#: Fréquence du Bonus visée, en paris. La plage autorisée est 1/75 à 1/85 ;
#: 1/75 est retenu parce qu'un Bonus plus fréquent porte une moyenne plus
#: basse, donc une queue moins lourde — et une queue moins lourde retrigge
#: moins. Voir la note sur le conflit retrigger, plus bas.
BONUS_HIT = 78.0

#: Répartition visée des Bonus, en part de tous les Bonus. Au milieu des
#: fourchettes cibles : beaucoup de faibles, une longue queue mince.
#: `medium_long` est la part des Bonus 20-100x QUI ONT retrigge. C'est la
#: seule facon de viser une frequence de retrigger sans deformer la forme des
#: gains : les deux grandeurs deviennent enfin independantes.
BONUS_SHARE = {"low": 0.72, "medium_long": 0.02, "medium": 0.16,
               "high": 0.08, "mega": 0.02}

#: Gain moyen visé dans chaque fence, en multiplicateurs de mise. Chaque valeur
#: doit tomber dans l'intervalle RÉEL des Books de sa fence, sinon l'optimizer
#: cherche une moyenne que sa population ne peut pas produire. Intervalles
#: mesurés sur 100 000 Books :
#:    low      0.00 -   19.90   (médiane   3.30)
#:    medium  20.00 -   99.90   (médiane  33.50)
#:    high   100.10 -  498.20   (médiane 157.60)
#:    mega   500.60 - 8779.80   (médiane 989.90)
BONUS_AVERAGE = {"low": 8.0, "medium_long": 60.0, "medium": 36.0, "high": 190.0}

#: Base Game : sec par construction. 1 pari sur 12.5 paie, 2.75x en moyenne.
#: Les Books de cette fence vont de 0.40x à 16.10x (médiane 1.10x) : cette
#: moyenne y est atteignable sans déformer la forme. On ne monte pas plus
#: haut : le Base Game ne doit pas devenir le moyen d'atteindre 96 %.
BASEGAME_HIT = 12.5
BASEGAME_RTP = 0.20

#: Max Win. Convention du sample officiel : une part de RTP infime, dont la
#: fréquence se DÉDUIT (hr = av_win / rtp). 0.001 sur un plafond de 10 000x
#: donne 1 pari sur 10 000 000. La seule exigence dure est P(Max Win) > 0.
WINCAP_RTP = 0.001


#: CONFLIT MESURE — forme des Bonus contre frequence de retrigger.
#:
#: Dans PLANT VS WILD, un Bonus n'atteint les gros paliers qu'en retriggant.
#: Part des Bonus AVEC retrigger, relevee sur 100 000 Books :
#:
#:    low (<20x)        2.93 %
#:    medium (20-100x) 42.66 %
#:    high (100-500x)  73.28 %
#:    mega (500x+)     92.27 %
#:
#: La forme de Bonus demandee impose donc arithmetiquement son taux de
#: retrigger. Meme la repartition la plus favorable autorisee (low 75 %,
#: medium 18 %, high 6 %, mega 1 %) donne 0.75x2.93 + 0.18x42.66 + 0.06x73.28
#: + 0.01x92.27 = 15.2 %, au-dessus de la cible 8-12 %.
#:
#: Ce n'est pas un defaut de reglage : c'est la mecanique verrouillee
#: (4 connexions Wild pendant un Free Spin -> +5) qui lie les deux grandeurs.
#: Aucun poids de lookup table ne peut les separer.


class OptimizationSetup:
    """Conditions d'optimisation, par bet mode."""

    def __init__(self, game_config):
        self.game_config = game_config
        wincap = game_config.wincap

        def bonus_hr(bucket):
            """1 pari sur N pour ce bucket."""
            return BONUS_HIT / BONUS_SHARE[bucket]

        def bonus_rtp(bucket):
            return round(BONUS_AVERAGE[bucket] / bonus_hr(bucket), 6)

        # Le bucket `mega` absorbe le solde du budget RTP : c'est lui qui porte
        # la longue queue, et c'est la seule fence dont la population a assez
        # d'amplitude (500x - 8780x) pour l'encaisser sans être irréalisable.
        allocated = (
            BASEGAME_RTP
            + WINCAP_RTP
            + sum(bonus_rtp(b) for b in ("low", "medium_long", "medium", "high"))
        )
        mega_rtp = round(game_config.rtp - allocated, 6)
        mega_average = mega_rtp * bonus_hr("mega")
        assert 500.0 < mega_average < 8779.0, (
            f"moyenne visée pour `mega` hors de portée de sa population : {mega_average:.0f}x"
        )

        self.game_config.opt_params = {
            "base": {
                # ORDRE SIGNIFICATIF — voir l'en-tête.
                "conditions": {
                    "wincap": ConstructConditions(
                        rtp=WINCAP_RTP, av_win=wincap, search_conditions=wincap
                    ).return_dict(),
                    "freegame_mega": ConstructConditions(
                        rtp=mega_rtp,
                        hr=bonus_hr("mega"),
                        search_conditions={"bucket": "mega"},
                    ).return_dict(),
                    "freegame_high": ConstructConditions(
                        rtp=bonus_rtp("high"),
                        hr=bonus_hr("high"),
                        search_conditions={"bucket": "high"},
                    ).return_dict(),
                    # Les deux fences `medium` sont DISJOINTES par
                    # construction : un Book a retrigge ou non.
                    "freegame_medium_long": ConstructConditions(
                        rtp=bonus_rtp("medium_long"),
                        hr=bonus_hr("medium_long"),
                        search_conditions={"bucket": "medium", "retrigger": "yes"},
                    ).return_dict(),
                    "freegame_medium": ConstructConditions(
                        rtp=bonus_rtp("medium"),
                        hr=bonus_hr("medium"),
                        search_conditions={"bucket": "medium", "retrigger": "no"},
                    ).return_dict(),
                    # `freegame` EST le bucket faible. Ce nom précis est
                    # obligatoire : le SDK exige que chaque criteria de
                    # Distribution soit une clé de `conditions`.
                    "freegame": ConstructConditions(
                        rtp=bonus_rtp("low"),
                        hr=bonus_hr("low"),
                        search_conditions={"bucket": "low"},
                    ).return_dict(),
                    # Sans `hr`, cette fence absorbe la probabilité restante :
                    # c'est elle qui fixe la proportion de paris perdants.
                    "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                    "basegame": ConstructConditions(
                        rtp=BASEGAME_RTP, hr=BASEGAME_HIT
                    ).return_dict(),
                },
                #: Aucune mise à l'échelle : la forme visée est déjà portée par
                #: les huit fences. Ajouter des `scale_factor` par-dessus
                #: déformerait une répartition qu'on vient de contraindre.
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": ConstructParameters(
                    num_show=2000,
                    num_per_fence=5000,
                    #: Rapport moyenne/médiane toléré DANS une fence. Le premier
                    #: candidat tournait à 2-60 : une fence pouvait y prendre une
                    #: forme arbitrairement déformée. Resserré sur la plage du
                    #: sample officiel, élargie pour une machine plus volatile.
                    min_m2m=2,
                    max_m2m=12,
                    pmb_rtp=1.0,
                    sim_trials=2000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                ).return_dict(),
            },
        }

        verify_optimization_input(self.game_config, self.game_config.opt_params)
