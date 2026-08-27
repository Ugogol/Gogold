"""Rage, Wild Snake, Wild Split et la limite d'une feature par spin.

Tests 22 à 32 du cahier, plus une régression (35) sur le suivi des Wild
temporaires à travers une cascade.
"""

import pytest

from game_config import GameConfig, SPLIT_WILD_COUNT
from gamestate import GameState
from tests.plant_vs_wild.conftest import load, neutral_board, place, spin_slices, unpad

CENTRE = {"reel": 2, "row": 2}


def dead_board():
    """Plateau sans connexion, Wild compris."""
    return place(neutral_board(), [(0, 0)], "W")


def prepared(bonus_game, seed=11):
    """Un Bonus placé sur un plateau mort, prêt à recevoir une feature."""
    bonus_game.force(boards=[dead_board()], seed=seed)
    bonus_game.draw_board(emit_event=False)
    bonus_game.get_clusters_update_wins()
    return bonus_game


def last_feature(game):
    return [event for event in game.book.events if event["type"] == "wildFeature"][-1]


# ── Rage ────────────────────────────────────────────────────────────────────


def test_22_rage_recentre_le_wild(bonus_game):
    game = prepared(bonus_game)
    game.apply_rage()

    event = last_feature(game)
    assert event["feature"] == "rage"
    assert unpad(event["wildTo"]) == CENTRE
    assert game.wild_position == CENTRE
    assert game.symbol_at(CENTRE).name == "W"
    # Le plateau complet est fourni : Rage ne passe pas par un tumble.
    assert [len(reel) for reel in event["board"]] == [7] * 5


def test_23_rage_conserve_les_multiplicateurs(bonus_game):
    game = prepared(bonus_game)
    game.position_multipliers[1][1] = 8
    before = [row[:] for row in game.position_multipliers]

    events_before = len(game.book.events)
    game.apply_rage()

    assert game.position_multipliers == before
    emitted = [event["type"] for event in game.book.events[events_before:]]
    assert "updateGrid" not in emitted


# ── Wild Snake ──────────────────────────────────────────────────────────────


def test_24_le_trajet_du_snake_est_orthogonal(bonus_game):
    game = prepared(bonus_game)
    game.apply_wild_snake()
    event = last_feature(game)

    steps = [event["from"]] + event["path"] + [event["to"]]
    for previous, step in zip(steps, steps[1:]):
        distance = abs(step["reel"] - previous["reel"]) + abs(step["row"] - previous["row"])
        assert distance == 1
    assert len(event["path"]) >= 1


def test_25_le_snake_ne_repasse_jamais_sur_une_case(bonus_game):
    game = prepared(bonus_game)
    game.apply_wild_snake()
    event = last_feature(game)

    steps = [event["from"]] + event["path"] + [event["to"]]
    keys = [(step["reel"], step["row"]) for step in steps]
    assert len(set(keys)) == len(keys)


def test_26_le_snake_conserve_les_multiplicateurs(bonus_game):
    game = prepared(bonus_game)
    game.position_multipliers[3][3] = 16
    before = [row[:] for row in game.position_multipliers]

    events_before = len(game.book.events)
    game.apply_wild_snake()

    assert game.position_multipliers == before
    assert "updateGrid" not in [event["type"] for event in game.book.events[events_before:]]


def test_27_le_snake_ne_donne_aucune_charge(bonus_game):
    game = prepared(bonus_game)
    charge_before = game.wild_charge

    game.apply_wild_snake()

    assert game.wild_charge == charge_before
    event = last_feature(game)
    # Le Wild occupe bien la case d'arrivée annoncée par le book.
    assert game.wild_position == unpad(event["to"])
    assert game.symbol_at(game.wild_position).name == "W"


# ── Wild Split ──────────────────────────────────────────────────────────────


def test_28_le_split_produit_trois_wild_temporaires(bonus_game):
    game = prepared(bonus_game)
    game.apply_wild_split()

    event = last_feature(game)
    assert event["feature"] == "wildSplit"
    assert len(event["positions"]) == SPLIT_WILD_COUNT
    assert len(game.temporary_wilds) == SPLIT_WILD_COUNT


def test_29_les_temporaires_sont_distinguables_du_wild_principal(bonus_game):
    game = prepared(bonus_game)
    main = dict(game.wild_position)
    game.apply_wild_split()

    assert main not in game.temporary_wilds
    assert game.wild_position == main
    assert len(game.wild_positions()) == SPLIT_WILD_COUNT + 1
    # Le contrat frontend attend le drapeau `temporary` sur ces cases.
    from game_events import client_board

    board = client_board(game)
    for position in game.temporary_wilds:
        assert board[position["reel"]][position["row"] + 1].get("temporary") is True
    assert "temporary" not in board[main["reel"]][main["row"] + 1]


def test_30_les_temporaires_sont_a_usage_unique(bonus_game):
    game = prepared(bonus_game)
    game.apply_wild_split()
    assert len(game.wild_positions()) == SPLIT_WILD_COUNT + 1

    game.expire_temporary_wilds()

    assert game.temporary_wilds == []
    assert len(game.wild_positions()) == 1


def test_31_le_plateau_revient_a_un_seul_wild_principal(bonus_game):
    game = prepared(bonus_game)
    main = dict(game.wild_position)
    game.apply_wild_split()
    game.expire_temporary_wilds()
    game.sync_wild_state()

    assert game.wild_positions() == [main]
    assert game.wild_position == main


def test_35_une_cascade_apres_un_split_ne_detruit_pas_le_wild_principal(bonus_game):
    """Régression : les temporaires sont suivis par identité, pas par position.

    Un tumble fait descendre les symboles survivants. Une position mémorisée
    désignerait alors une autre case, et l'expiration effacerait un symbole au
    hasard — le Wild principal compris.
    """
    game = prepared(bonus_game, seed=2)
    main = dict(game.wild_position)
    game.apply_wild_split()
    temporaries = [game.symbol_at(position) for position in game.temporary_wilds]

    # Une connexion quelque part sous les Wild, pour provoquer une chute.
    game.resolve_spin()
    game.expire_temporary_wilds()
    game.sync_wild_state()

    assert game.wild_positions() == [game.wild_position]
    assert game.symbol_at(game.wild_position) is game.wild_symbol
    # Aucun temporaire ne subsiste sur le plateau.
    assert not any(
        game.symbol_at(position) is symbol
        for position in game.all_positions()
        for symbol in temporaries
    )
    assert main is not None


# ── Limite ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def forced_feature_book():
    """Un Bonus où chaque dead spin se voit proposer une feature différente."""
    state = GameState(GameConfig())
    state.betmode = "bonus"
    state.criteria = "freegame"
    state.force(features=["rage", "wildSnake", "wildSplit"] * 6, seed=5)
    state.run_spin(1)
    return [dict(event) for event in state.book.events]


def test_32_au_plus_une_feature_par_dead_spin(forced_feature_book):
    features = [event for event in forced_feature_book if event["type"] == "wildFeature"]
    assert features, "aucune feature déclenchée dans le book forcé"

    for spin in spin_slices(forced_feature_book):
        assert len([event for event in spin if event["type"] == "wildFeature"]) <= 1


# ── Plafond de cascades ─────────────────────────────────────────────────────


def long_cascade_sim(minimum_tumbles=4):
    """Premier numéro de simulation dont le spin de base cascade assez.

    Cherché SANS plafond : le même spin est ensuite rejoué avec le plafond à
    tester, pour comparer deux lectures d'une seule et même donnée.
    """
    config = GameConfig()
    previous = config.max_cascades_per_spin
    config.max_cascades_per_spin = None
    try:
        state = GameState(config)
        state.betmode = "base"
        state.criteria = "basegame"
        for sim in range(600):
            state.run_spin(sim)
            if [event["type"] for event in state.book.events].count("tumbleBoard") >= minimum_tumbles:
                return sim
    finally:
        config.max_cascades_per_spin = previous
    pytest.skip("aucun spin assez long dans l'échantillon")


def cascade_book(maximum, sim):
    """Rejoue un spin donné avec le plafond demandé."""
    config = GameConfig()
    previous = config.max_cascades_per_spin
    config.max_cascades_per_spin = maximum
    try:
        state = GameState(config)
        state.betmode = "base"
        state.criteria = "basegame"
        state.run_spin(sim)
        return [dict(event) for event in state.book.events]
    finally:
        config.max_cascades_per_spin = previous


def test_44_un_plafond_jamais_atteint_ne_change_rien():
    """Plafond très haut : le book est identique à celui sans plafond."""
    sim = long_cascade_sim()
    assert cascade_book(None, sim) == cascade_book(999, sim)


def test_45_le_plafond_paie_la_derniere_resolution_puis_arrete():
    """Au plafond : le dernier gain est payé, puis plus aucune cascade.

    Rien n'est annulé — on vérifie que la dernière connexion a bien produit son
    `winInfo` et son `updateGrid`, et qu'aucun `tumbleBoard` ne suit.
    """
    events = cascade_book(2, long_cascade_sim())
    types = [event["type"] for event in events]

    assert types.count("tumbleBoard") == 2, "le spin s'arrête à deux cascades"

    last_tumble = len(types) - 1 - types[::-1].index("tumbleBoard")
    after = types[last_tumble + 1 :]
    assert "winInfo" in after, "la résolution qui suit la dernière cascade est payée"
    assert "updateGrid" in after, "ses multiplicateurs sont appliqués"
    assert "tumbleBoard" not in after
    # Le spin se termine normalement : le frontend n'a besoin d'aucun event neuf.
    assert "setTotalWin" in after
