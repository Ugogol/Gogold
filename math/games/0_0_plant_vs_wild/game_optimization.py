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
#:
#: `medium_long` est la part des Bonus 20-100x QUI ONT retriggé. C'est la seule
#: façon de viser une fréquence de retrigger sans déformer la forme des gains :
#: les deux grandeurs deviennent indépendantes. Le Math corrigé lie encore plus
#: fort le niveau de gain au retrigger — mesuré sur la population V5 : low
#: 3.02 %, medium 45.35 %, high 79.81 %, mega 98.48 %. Le plancher imposé par
#: `high` et `mega` seuls vaut déjà 10.5 % ; `medium_long` sert à ne pas monter
#: au-dessus.
BONUS_SHARE = {"low": 0.70, "medium_long": 0.01, "medium": 0.19,
               "high": 0.08, "mega": 0.02}

#: Gain moyen visé dans chaque fence, en multiplicateurs de mise.
#:
#: Chaque valeur doit non seulement tomber dans l'intervalle des Books de sa
#: fence, mais y occuper un percentile raisonnable : viser le 95e obligerait
#: l'optimizer à écraser toute la fence sur son extrémité haute. Vérifié avec
#: `plan_fences.py` — les cinq cibles tiennent entre le 59e et le 79e
#: percentile de leur propre population.
#:
#: Population V5 mesurée (Math corrigé), 100 000 Books :
#:    low            0.00 -   19.90   médiane   3.30   moyenne    4.81
#:    medium        20.00 -   99.80   médiane  29.00   moyenne   34.75
#:    medium_long   20.00 -   99.90   médiane  39.60   moyenne   45.21
#:    high         100.10 -  499.30   médiane 162.95   moyenne  194.65
#:    mega         503.10 - 8772.80   médiane 935.70   moyenne 1364.02
BONUS_AVERAGE = {"low": 8.0, "medium_long": 45.0, "medium": 35.0, "high": 195.0}

#: Base Game : sec par construction. 1 pari sur 12.5 paie, 2.00x en moyenne.
#: Les Books de cette fence vont de 0.40x à 16.10x (médiane 1.10x, moyenne
#: 1.36x) : la cible est au 76e percentile, atteignable sans déformer la forme.
#: On ne monte pas plus haut — le Base Game ne doit pas devenir le moyen
#: d'atteindre 96 %.
BASEGAME_HIT = 12.5
BASEGAME_RTP = 0.16

#: Max Win. Convention du sample officiel : une part de RTP infime, dont la
#: fréquence se DÉDUIT (hr = av_win / rtp). 0.001 sur un plafond de 10 000x
#: donne 1 pari sur 10 000 000. La seule exigence dure est P(Max Win) > 0.
WINCAP_RTP = 0.001


#: RETRIGGER — plancher imposé par la forme.
#:
#: Dans PLANT VS WILD, un Bonus n'atteint les paliers élevés qu'en retriggant, et
#: le Math corrigé renforce ce lien. Part des Bonus AVEC retrigger, mesurée sur
#: la population V5 :
#:
#:    low (<20x)        3.02 %
#:    medium (20-100x) 45.35 %
#:    high (100-500x)  79.81 %
#:    mega (500x+)     98.48 %
#:
#: `high` à 8 % et `mega` à 2 % apportent à eux seuls 6.38 + 1.97 = 8.35 points,
#: et `low` 2.11 : le plancher est donc de 10.5 % AVANT toute autre décision.
#: Scinder `medium` par retrigger permet de ne pas monter au-delà — sans ce
#: découpage, la forme visée donnerait mécaniquement 19.5 %.


# ═════════════════════════════════════════════════════════════════════════════
# BONUS BUY — BetMode `bonus`, coût 100x
# ═════════════════════════════════════════════════════════════════════════════
#
# CONVENTION DE COÛT, relevée dans le Rust et non déduite :
#   `bet_amount = bet_modes[i].cost`, et `avg_win = fence.avg_win * bet_amount`.
# Un `av_win` de fence est donc en MULTIPLES DU PRIX D'ACHAT, pas de la mise de
# base. Sur le mode `base` (coût 1) les deux coïncident, ce qui masque le piège.
# On ne fournit donc que `rtp` et `hr`, jamais `av_win` : le Rust en déduit
# `avg_win = hr * rtp`, sans ambiguïté d'unité.
#
# RTP du mode = payout moyen / coût. Viser 0.960 veut dire un payout moyen
# pondéré de 96x, pas de 0.96x.
#
# Les buckets réutilisent les bornes du mode base (`BONUS_BUCKET_BOUNDS`) : en
# changer une réécrirait les force records du mode base et invaliderait
# BALANCING_V5.

#: Part de chaque fence dans les achats. La somme fait 1 : tout achat produit un
#: Bonus, il n'y a pas de fence « perdant » séparée.
#:
#:   low + medium = 0.79   -> P(payout < 100x), le joueur perd sur ~4 achats sur 5
#:   high + mega  = 0.21   -> P(payout >= 100x)
#:   mega         = 0.04   -> P(payout >= 500x)
#: `medium_long` est la part des achats 20-100x QUI ONT retriggé — la seule
#: façon de piloter la fréquence de retrigger sans déformer la forme des gains.
#: Sans ce découpage, la forme visée donnait 44 % de retrigger (mesuré au run 1).
BUY_SHARE = {"low": 0.35, "medium": 0.43, "medium_long": 0.02, "high": 0.17, "mega": 0.03}

#: Payout moyen visé par fence, en multiples de la MISE DE BASE. Converti en
#: unités de coût plus bas. Population mesurée sur 200 000 Books :
#:   low       0.00 -   19.90   médiane   3.30   moyenne    4.82
#:   medium   20.00 -   99.90   médiane  32.80   moyenne   39.60
#:   high    100.00 -  499.40   médiane 166.30   moyenne  200.89
#:   mega    500.00 - 9717.10   médiane 899.30   moyenne 1498.07
BUY_AVERAGE = {"low": 8.0, "medium": 55.0, "medium_long": 60.0, "high": 230.0}

#: Max Win. Une part de RTP infime dont la fréquence se déduit : 0.001 sur un
#: plafond valant 100 fois le prix d'achat donne 1 achat sur 100 000.
BUY_WINCAP_RTP = 0.001


#: RETRIGGER — plancher imposé par la forme, mesuré sur la population.
#:
#: Part des achats AVEC retrigger, par fence : low 3.34 %, medium 46.48 %,
#: high 84.66 %, mega 96.65 %, wincap 100 %. Atteindre un payout élevé passe par
#: des Free Spins supplémentaires : les deux grandeurs sont liées par la
#: mécanique, pas par le réglage.
#:
#: `high` à 17 % et `mega` à 3 % apportent à eux seuls 14.4 + 2.9 = 17.3 points.
#: Le plancher est donc d'environ 20 % quelle que soit la répartition compatible
#: avec les cibles de forme — la cible 8-15 % n'est pas atteignable sans
#: sacrifier P(>=100x) ou P(>=500x).


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
                #: Volumes repris du sample officiel `0_0_cluster`. Avec les
                #: valeurs plus basses (2000/5000), l'optimizer ne trouvait plus
                #: que 5 distributions valides sur la population corrigée — et
                #: le SDK plante alors, sa boucle d'affichage étant codée en dur
                #: sur 10 (`main.rs:261`). Plus de matière première, plus de
                #: combinaisons valides.
                "parameters": ConstructParameters(
                    num_show=5000,
                    num_per_fence=10000,
                    #: Rapport moyenne/médiane toléré DANS une fence. Le premier
                    #: candidat tournait à 2-60 : une fence pouvait y prendre une
                    #: forme arbitrairement déformée. Resserré sur la plage du
                    #: sample officiel, élargie pour une machine plus volatile.
                    min_m2m=2,
                    max_m2m=20,
                    pmb_rtp=1.0,
                    sim_trials=2000,
                    test_spins=[50, 100, 200],
                    test_weights=[0.3, 0.4, 0.3],
                    score_type="rtp",
                ).return_dict(),
            },
        }

        cost = next(b.get_cost() for b in game_config.bet_modes if b.get_name() == "bonus")

        def buy_hr(bucket):
            return 1.0 / BUY_SHARE[bucket]

        def buy_rtp(bucket):
            """RTP = part x payout moyen, ce dernier ramené au prix d'achat."""
            return round(BUY_SHARE[bucket] * BUY_AVERAGE[bucket] / cost, 6)

        buy_allocated = BUY_WINCAP_RTP + sum(
            buy_rtp(b) for b in ("low", "medium", "medium_long", "high")
        )
        buy_mega_rtp = round(game_config.rtp - buy_allocated, 6)
        buy_mega_average = buy_mega_rtp / BUY_SHARE["mega"] * cost
        assert 500.0 < buy_mega_average < 9717.0, (
            f"moyenne visée pour `mega` hors de portée de sa population : {buy_mega_average:.0f}x"
        )

        self.game_config.opt_params["bonus"] = {
            # ORDRE SIGNIFICATIF : payout exact d'abord, attrape-tout en dernier.
            "conditions": {
                "wincap": ConstructConditions(
                    rtp=BUY_WINCAP_RTP,
                    hr=game_config.wincap / cost / BUY_WINCAP_RTP,
                    search_conditions=game_config.wincap,
                ).return_dict(),
                "buy_mega": ConstructConditions(
                    rtp=buy_mega_rtp,
                    hr=buy_hr("mega"),
                    search_conditions={"bucket": "mega"},
                ).return_dict(),
                "buy_high": ConstructConditions(
                    rtp=buy_rtp("high"),
                    hr=buy_hr("high"),
                    search_conditions={"bucket": "high"},
                ).return_dict(),
                # Les deux fences `medium` sont DISJOINTES par construction :
                # un achat a retriggé ou non.
                "buy_medium_long": ConstructConditions(
                    rtp=buy_rtp("medium_long"),
                    hr=buy_hr("medium_long"),
                    search_conditions={"bucket": "medium", "retrigger": "yes"},
                ).return_dict(),
                "buy_medium": ConstructConditions(
                    rtp=buy_rtp("medium"),
                    hr=buy_hr("medium"),
                    search_conditions={"bucket": "medium", "retrigger": "no"},
                ).return_dict(),
                # `freegame` EST le bucket faible et l'attrape-tout. Ce nom précis
                # est obligatoire : le SDK exige que chaque criteria de
                # Distribution soit une clé de `conditions`.
                "freegame": ConstructConditions(
                    rtp=buy_rtp("low"), hr=buy_hr("low")
                ).return_dict(),
            },
            "scaling": ConstructScaling([]).return_dict(),
            "parameters": ConstructParameters(
                num_show=5000,
                num_per_fence=10000,
                min_m2m=2,
                max_m2m=20,
                pmb_rtp=1.0,
                sim_trials=2000,
                test_spins=[50, 100, 200],
                test_weights=[0.3, 0.4, 0.3],
                score_type="rtp",
            ).return_dict(),
        }

        verify_optimization_input(self.game_config, self.game_config.opt_params)
