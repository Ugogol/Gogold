"""Classement des Books dans les criteria d'optimisation.

Ces tests ne portent sur AUCUNE mecanique de jeu : ils verifient uniquement que
la population d'optimisation est correctement etiquetee. Un Book mal classe fait
travailler l'optimizer sur une forme fausse.
"""

import pytest

from game_config import GameConfig, BONUS_BUCKET_BOUNDS


def test_bornes_jointives_et_sans_recouvrement():
    """Les bornes se touchent sans trou ni chevauchement."""
    ordered = ["low", "medium", "high", "mega"]
    for lower, upper in zip(ordered, ordered[1:]):
        assert BONUS_BUCKET_BOUNDS[lower][1] == BONUS_BUCKET_BOUNDS[upper][0]
    assert BONUS_BUCKET_BOUNDS["low"][0] == 0.0
    assert BONUS_BUCKET_BOUNDS["mega"][1] == GameConfig().wincap


@pytest.mark.parametrize(
    "payout, attendu",
    [
        (0.0, "low"), (19.9, "low"),
        (20.0, "medium"), (99.9, "medium"),      # borne fermee a gauche
        (100.0, "high"), (499.9, "high"),
        (500.0, "mega"), (9999.9, "mega"),
        (10000.0, "wincap"),                     # le plafond n'est pas un bucket
    ],
)
def test_classement_aux_bornes(game, payout, attendu):
    """Chaque borne tombe dans le bucket SUPERIEUR : ferme a gauche."""
    game.final_win = payout
    assert game.bonus_bucket() == attendu


def test_tout_payout_est_classable(game):
    """Aucun trou : tout payout atteignable recoit un bucket."""
    value = 0.0
    while value <= GameConfig().wincap:
        game.final_win = value
        assert game.bonus_bucket() in {"low", "medium", "high", "mega", "wincap"}
        value += 7.3


def test_un_seul_bucket_par_payout(game):
    """Les intervalles sont disjoints : un payout ne peut pas en satisfaire deux."""
    for payout in (0.0, 19.99, 20.0, 99.99, 100.0, 499.99, 500.0, 9999.99):
        matches = [n for n, (lo, hi) in BONUS_BUCKET_BOUNDS.items() if lo <= payout < hi]
        assert len(matches) == 1, f"{payout} tombe dans {matches}"


def test_au_dessus_du_plafond_reste_wincap(game):
    """Le plafond ecrete : rien ne doit passer en `mega` au-dela."""
    game.final_win = GameConfig().wincap * 2
    assert game.bonus_bucket() == "wincap"


def test_aucun_enregistrement_sans_bonus(game):
    """Un round sans Bonus ne recoit pas de bucket : il releve de `0`/`basegame`."""
    game.triggered_freegame = False
    game.final_win = 5.0
    game.temp_wins = []
    game.record_optimization_criteria()
    assert game.temp_wins == []


def test_enregistrement_avec_bonus(game):
    """Un round Bonus est etiquete avec les cles que l'optimizer interroge."""
    game.triggered_freegame = True
    game.final_win = 250.0
    game.temp_wins = []
    game.record_optimization_criteria()
    assert game.temp_wins[0] == {
        "criteria": "freegame",
        "bucket": "high",
        "retrigger": "no",
    }


def test_enregistrement_du_retrigger(game):
    """La dimension retrigger se lit sur les events du Book, pas ailleurs."""
    game.triggered_freegame = True
    game.final_win = 40.0
    game.book.events.append({"type": "freeSpinRetrigger", "amount": 5})
    game.temp_wins = []
    game.record_optimization_criteria()
    assert game.temp_wins[0]["retrigger"] == "yes"
    assert game.temp_wins[0]["bucket"] == "medium"


def test_les_deux_dimensions_sont_independantes(game):
    """Bucket et retrigger se combinent librement : aucune n'implique l'autre."""
    game.triggered_freegame = True
    for payout, bucket in ((5.0, "low"), (250.0, "high")):
        for events, expected in (([], "no"), ([{"type": "freeSpinRetrigger"}], "yes")):
            game.book.events = list(events)
            game.final_win = payout
            game.temp_wins = []
            game.record_optimization_criteria()
            assert game.temp_wins[0]["bucket"] == bucket
            assert game.temp_wins[0]["retrigger"] == expected


def test_criteria_de_simulation_couverts_par_les_fences():
    """Le SDK exige que chaque criteria de Distribution soit une cle de conditions."""
    config = GameConfig()
    from game_optimization import OptimizationSetup

    OptimizationSetup(config)
    for bet_mode in config.bet_modes:
        name = bet_mode.get_name()
        if name not in config.opt_params:
            continue
        fences = set(config.opt_params[name]["conditions"])
        for distribution in bet_mode.get_distributions():
            assert distribution.get_criteria() in fences
