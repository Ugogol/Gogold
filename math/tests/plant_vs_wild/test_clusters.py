"""Connexions : taille minimale et substitution du Wild (tests 01 à 03)."""

from tests.plant_vs_wild.conftest import load, neutral_board, place


def resolve(game, board):
    """Charge un plateau et évalue les connexions, sans cascade."""
    load(game, board)
    game.get_clusters_update_wins()
    return game.win_data


def test_01_trois_identiques_ne_forment_pas_de_connexion(game):
    board = place(neutral_board(), [(0, 0), (0, 1), (1, 0)], "H1")
    win_data = resolve(game, board)

    assert win_data["totalWin"] == 0
    assert win_data["wins"] == []


def test_02_quatre_identiques_forment_une_connexion(game):
    board = place(neutral_board(), [(0, 0), (0, 1), (1, 0), (1, 1)], "H1")
    win_data = resolve(game, board)

    assert win_data["totalWin"] > 0
    assert [win["symbol"] for win in win_data["wins"]] == ["H1"]
    assert win_data["wins"][0]["clusterSize"] == 4


def test_03_trois_identiques_plus_un_wild_forment_une_connexion(game):
    board = place(neutral_board(), [(0, 0), (0, 1), (1, 0)], "H1")
    place(board, [(1, 1)], "W")
    win_data = resolve(game, board)

    assert win_data["totalWin"] > 0
    win = win_data["wins"][0]
    assert win["symbol"] == "H1"
    assert win["clusterSize"] == 4
    # Le Wild fait partie du groupe : c'est lui qui complète les trois symboles.
    assert {"reel": 1, "row": 1} in win["positions"]
