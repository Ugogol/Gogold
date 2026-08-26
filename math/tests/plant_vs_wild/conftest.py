"""Outils communs aux tests déterministes de PLANT VS WILD.

Aucun test de cette suite n'est probabiliste : soit il travaille sur un plateau
écrit à la main, soit il rejoue une simulation dont le numéro fixe la graine.
"""

import os
import sys

import pytest

GAME_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "games", "0_0_plant_vs_wild"))
if GAME_PATH not in sys.path:
    sys.path.insert(0, GAME_PATH)

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402

#: Symboles de remplissage. Quatre valeurs distinctes suffisent à garantir que
#: deux cases voisines diffèrent toujours dans `neutral_board`.
FILLERS = ("L1", "L2", "L3", "L4")


@pytest.fixture
def game():
    """Un gamestate neuf en Base Game, prêt à recevoir un plateau imposé."""
    state = GameState(GameConfig())
    state.betmode = "base"
    state.criteria = "basegame"
    state.reset_book()
    return state


@pytest.fixture
def bonus_game():
    """Un gamestate neuf placé en Bonus."""
    state = GameState(GameConfig())
    state.betmode = "bonus"
    state.criteria = "freegame"
    state.reset_book()
    state.gametype = state.config.freegame_type
    return state


def neutral_board():
    """Plateau 5x5 sans aucune connexion.

    `(reel + 2 * row) % 4` : deux cases voisines sur une colonne diffèrent de 2,
    deux cases voisines sur une ligne diffèrent de 1. Aucun groupe ne dépasse
    donc une case.
    """
    return [[FILLERS[(reel + 2 * row) % 4] for row in range(5)] for reel in range(5)]


def place(board, positions, name):
    """Pose un symbole sur une liste de cases `(reel, row)`."""
    for reel, row in positions:
        board[reel][row] = name
    return board


def load(game, board, keep_charge=False):
    """Impose un plateau au gamestate, sans émettre de `reveal`.

    `keep_charge` simule un Wild qui a survécu : la charge n'est pas remise à
    zéro par la resynchronisation.
    """
    charge = game.wild_charge
    game.force(boards=[board])
    game.draw_board(emit_event=False)
    if keep_charge:
        game.wild_charge = charge
    return game


def spin_slices(events):
    """Découpe un book en spins, un par `reveal`."""
    slices = []
    for event in events:
        if event["type"] == "reveal":
            slices.append([])
        if slices:
            slices[-1].append(event)
    return slices


def unpad(position):
    """Position de book -> position interne (lignes visibles)."""
    return {"reel": position["reel"], "row": position["row"] - 1}
