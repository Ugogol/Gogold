"""Wild : implication, déplacement, charge et bonus pending (tests 04 à 11)."""

import pytest

from game_config import WILD_MAX_CHARGE
from tests.plant_vs_wild.conftest import load, neutral_board, place, unpad

#: Simulation de base dont on sait qu'elle déclenche le Bonus naturellement.
#: Le numéro fixe la graine : le book est identique à chaque exécution.
TRIGGER_SIM = 216


def cluster_with_wild():
    """Trois H1 et le Wild qui les complète, en haut à gauche."""
    board = place(neutral_board(), [(0, 0), (0, 1), (1, 0)], "H1")
    return place(board, [(1, 1)], "W")


def cluster_without_wild():
    """Une connexion de quatre H1, et le Wild à l'écart."""
    board = place(neutral_board(), [(0, 0), (0, 1), (1, 0), (1, 1)], "H1")
    return place(board, [(4, 4)], "W")


def test_04_wild_non_implique_ne_gagne_aucune_charge(game):
    load(game, cluster_without_wild())
    game.get_clusters_update_wins()
    game.handle_wild_connection()

    assert game.wild_charge == 0
    assert [event for event in game.book.events if event["type"] == "wildMove"] == []


def test_05_wild_implique_gagne_une_charge(game):
    load(game, cluster_with_wild())
    game.get_clusters_update_wins()
    game.handle_wild_connection()

    moves = [event for event in game.book.events if event["type"] == "wildMove"]
    assert game.wild_charge == 1
    assert len(moves) == 1
    assert moves[0]["charge"] == 1


def test_06_destination_du_wild_appartient_aux_cases_liberees(game):
    load(game, cluster_with_wild())
    game.get_clusters_update_wins()
    released = [dict(position) for position in game.winning_positions()]
    game.handle_wild_connection()

    move = [event for event in game.book.events if event["type"] == "wildMove"][0]
    assert unpad(move["to"]) in released
    assert unpad(move["from"]) in released


def test_07_le_wild_se_deplace_avant_le_refill(game):
    """`wildMove` précède toujours le `tumbleBoard` de la même cascade."""
    game.force(boards=[cluster_with_wild()])
    game.draw_board(emit_event=False)
    game.resolve_spin()

    types = [event["type"] for event in game.book.events]
    assert "wildMove" in types and "tumbleBoard" in types
    assert types.index("wildMove") < types.index("tumbleBoard")


def test_08_la_charge_monte_de_un_a_quatre(game):
    """Un Wild qui survit accumule ses connexions, une par une."""
    charges = []
    for _ in range(WILD_MAX_CHARGE):
        load(game, cluster_with_wild(), keep_charge=True)
        game.get_clusters_update_wins()
        game.handle_wild_connection()
        charges.append(game.wild_charge)

    assert charges == [1, 2, 3, 4]
    moves = [event["charge"] for event in game.book.events if event["type"] == "wildMove"]
    assert moves == [1, 2, 3, 4]


def test_09_la_quatrieme_connexion_met_le_bonus_en_attente(game):
    pending = []
    for _ in range(WILD_MAX_CHARGE):
        load(game, cluster_with_wild(), keep_charge=True)
        game.get_clusters_update_wins()
        game.handle_wild_connection()
        pending.append(game.bonus_pending)

    assert pending == [False, False, False, True]
    # Rien n'est annoncé au joueur à ce moment-là.
    assert [event for event in game.book.events if event["type"] == "freeSpinTrigger"] == []


@pytest.fixture(scope="module")
def trigger_book():
    """Book complet d'un spin de base qui déclenche le Bonus."""
    from game_config import GameConfig
    from gamestate import GameState

    state = GameState(GameConfig())
    state.betmode = "base"
    state.criteria = "basegame"
    state.run_spin(TRIGGER_SIM)
    return [dict(event) for event in state.book.events]


def test_10_les_cascades_continuent_malgre_le_bonus_pending(trigger_book):
    # Le book contient aussi le Bonus : on n'examine que le spin déclencheur.
    all_types = [event["type"] for event in trigger_book]
    base_spin = trigger_book[: all_types.index("freeSpinTrigger")]
    types = [event["type"] for event in base_spin]

    charges = [event["charge"] for event in base_spin if event["type"] == "wildMove"]
    # La 4e connexion pose `bonus_pending` sans rien interrompre : le Wild
    # continue de se déplacer, sa charge restant plafonnée.
    assert charges[:WILD_MAX_CHARGE] == [1, 2, 3, 4]
    assert all(charge == WILD_MAX_CHARGE for charge in charges[WILD_MAX_CHARGE:])
    assert len(charges) > WILD_MAX_CHARGE

    last_charge = max(index for index, event in enumerate(base_spin) if event["type"] == "wildMove")
    # Le spin ne s'arrête pas à la 4e connexion : le plateau se recomplète encore.
    assert "tumbleBoard" in types[last_charge:]


def test_11_le_trigger_arrive_apres_la_stabilisation(trigger_book):
    types = [event["type"] for event in trigger_book]
    trigger = types.index("freeSpinTrigger")

    assert types.index("setTotalWin") < trigger
    # Plus aucune cascade entre la stabilisation et l'annonce.
    assert "tumbleBoard" not in types[types.index("setTotalWin") : trigger]
    assert trigger_book[trigger]["totalFs"] == 10
