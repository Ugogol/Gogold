"""Wild : implication, déplacement, charge et bonus pending (tests 04 à 11)."""

import pytest

from game_config import WILD_MAX_CHARGE
from tests.plant_vs_wild.conftest import load, neutral_board, place, unpad

#: Nombre de simulations balayées pour trouver un déclenchement naturel du
#: Bonus. On ne fige PAS un numéro : il dépendrait des bandes, et changerait à
#: chaque réglage de balancing. Le balayage reste déterministe — même
#: configuration, même book retenu.
TRIGGER_SEARCH = 600


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
    """Premier book de base qui déclenche le Bonus naturellement."""
    from game_config import GameConfig
    from gamestate import GameState

    config = GameConfig()
    # Le plafond de cascades est un PARAMÈTRE de balancing ; la règle testée ici
    # est que `bonus_pending` n'interrompt rien. On l'isole donc du plafond.
    previous = config.max_cascades_per_spin
    config.max_cascades_per_spin = None
    try:
        state = GameState(config)
        state.betmode = "base"
        state.criteria = "basegame"
        for sim in range(TRIGGER_SEARCH):
            state.run_spin(sim)
            if any(event["type"] == "freeSpinTrigger" for event in state.book.events):
                return [dict(event) for event in state.book.events]
    finally:
        config.max_cascades_per_spin = previous
    pytest.skip(f"aucun déclenchement naturel en {TRIGGER_SEARCH} simulations")


def test_10_les_cascades_continuent_malgre_le_bonus_pending(trigger_book):
    # Le book contient aussi le Bonus : on n'examine que le spin déclencheur.
    all_types = [event["type"] for event in trigger_book]
    base_spin = trigger_book[: all_types.index("freeSpinTrigger")]
    types = [event["type"] for event in base_spin]

    charges = [event["charge"] for event in base_spin if event["type"] == "wildMove"]
    # La 4e connexion pose `bonus_pending` sans rien interrompre : le Wild
    # continue de se déplacer, sa charge restant plafonnée.
    assert charges[:WILD_MAX_CHARGE] == [1, 2, 3, 4]
    # Au-delà du maximum la charge est plafonnée. Que le Wild se déplace ou non
    # une fois de plus dépend du plateau, pas de la règle : on ne l'exige pas.
    assert all(charge == WILD_MAX_CHARGE for charge in charges[WILD_MAX_CHARGE:])

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


@pytest.fixture(scope="module")
def mixed_books():
    """Un échantillon déterministe des deux modes."""
    from game_config import GameConfig
    from gamestate import GameState

    config = GameConfig()
    books = []
    for mode, criteria, count in (("base", "basegame", 60), ("bonus", "freegame", 15)):
        state = GameState(config)
        state.betmode = mode
        state.criteria = criteria
        for sim in range(count):
            state.run_spin(sim)
            books.append([dict(event) for event in state.book.events])
    return books


def test_39_le_wild_n_arrive_jamais_par_une_case_de_padding(mixed_books):
    """Régression : un Wild posé en padding produit deux Wild à l'écran.

    Une case de padding porte un vrai symbole : au tumble suivant elle descend
    dans le plateau visible. Un Wild qui arrive par là s'ajoute au Wild
    principal, et le frontend — qui détient déjà ce symbole depuis un
    `newSymbols` précédent — ne peut pas être averti d'une correction faite
    après coup côté Math.
    """
    padding_wilds = 0
    for events in mixed_books:
        for event in events:
            if event["type"] == "reveal":
                for column in event["board"]:
                    padding_wilds += sum(1 for row in (0, -1) if column[row]["name"] == "W")
            elif event["type"] == "tumbleBoard":
                # L'entrée 0 de chaque reel est le NOUVEAU symbole de padding haut.
                for column in event["newSymbols"]:
                    if column and column[0]["name"] == "W":
                        padding_wilds += 1
            elif event["type"] == "wildFeature" and event["feature"] in ("rage", "wildSnake"):
                for column in event["board"]:
                    padding_wilds += sum(1 for row in (0, -1) if column[row]["name"] == "W")

    assert padding_wilds == 0


def test_40_un_seul_wild_est_visible_a_tout_instant(mixed_books):
    """Rejoue la physique de chute du frontend et compte les Wild à l'écran.

    C'est la seule vérification qui voit ce que le joueur voit : le plateau du
    Math est toujours correct, c'est la vue du frontend qui pouvait diverger.
    Pendant un Wild Split, les trois temporaires s'ajoutent au Wild principal.
    """
    for events in mixed_books:
        board = None
        split = False
        for event in events:
            kind = event["type"]
            if kind == "reveal":
                board = [[cell["name"] for cell in column] for column in event["board"]]
                split = False
            elif kind == "wildMove" and board:
                source, target = event["from"], event["to"]
                a = board[source["reel"]][source["row"]]
                b = board[target["reel"]][target["row"]]
                board[source["reel"]][source["row"]] = b
                board[target["reel"]][target["row"]] = a
            elif kind == "tumbleBoard" and board:
                exploding = {}
                for position in event["explodingSymbols"]:
                    exploding.setdefault(position["reel"], set()).add(position["row"])
                for reel, rows in exploding.items():
                    survivors = [board[reel][row] for row in range(7) if row not in rows]
                    incoming = [cell["name"] for cell in event["newSymbols"][reel]]
                    board[reel] = incoming + survivors
            elif kind == "wildFeature" and board:
                if event["feature"] in ("rage", "wildSnake"):
                    board = [[cell["name"] for cell in column] for column in event["board"]]
                else:
                    split = True
                    for position in event["positions"]:
                        board[position["reel"]][position["row"]] = "W"

            if board:
                visible = sum(column[1:6].count("W") for column in board)
                assert visible <= (4 if split else 1), f"{visible} Wild visibles après {kind}"


def test_41_deux_clusters_dans_une_cascade_ne_chargent_le_wild_qu_une_fois(game):
    """Le Wild qui complète deux groupes à la fois ne gagne qu'un cran.

    Il appartient bien aux deux connexions et rapporte dans les deux ; la
    charge, elle, compte les cascades, pas les groupes.
    """
    board = place(neutral_board(), [(2, 1), (1, 1), (1, 2)], "H1")
    place(board, [(2, 3), (3, 3), (3, 2)], "H2")
    place(board, [(2, 2)], "W")

    load(game, board)
    game.get_clusters_update_wins()

    wild = {"reel": 2, "row": 2}
    holding = [win for win in game.win_data["wins"] if wild in win["positions"]]
    assert len(holding) >= 2, "le plateau doit faire participer le Wild à deux connexions"

    game.handle_wild_connection()

    moves = [event for event in game.book.events if event["type"] == "wildMove"]
    assert len(moves) == 1
    assert moves[0]["charge"] == 1
    assert game.wild_charge == 1


def test_42_la_charge_ne_progresse_que_dun_cran_par_cascade(mixed_books):
    """Sur un book entier : deux `wildMove` successifs d'un même spin se suivent."""
    for events in mixed_books:
        charges = []
        for event in events:
            if event["type"] == "reveal":
                charges = []
            elif event["type"] == "wildMove":
                if charges:
                    step = event["charge"] - charges[-1]
                    # Un cran, ou aucun une fois le plafond atteint.
                    assert step == 1 or (step == 0 and charges[-1] == WILD_MAX_CHARGE)
                charges.append(event["charge"])
