"""Multiplicateurs positionnels : doublement, reset et persistance (12 à 17)."""

import pytest

from game_config import GameConfig, MAX_POSITION_MULT
from gamestate import GameState

CELL = {"reel": 2, "row": 2}


def hit(game, position=CELL):
    """Simule une participation de la case à une connexion."""
    game.win_data = {"totalWin": 1.0, "wins": [{"positions": [dict(position)]}]}
    game.update_grid_mults()
    return game.position_multipliers[position["reel"]][position["row"]]


def test_12_une_case_activee_passe_de_x1_a_x2(game):
    assert game.position_multipliers[CELL["reel"]][CELL["row"]] == 0
    assert hit(game) == 2


def test_13_une_case_deja_activee_double(game):
    hit(game)
    assert hit(game) == 4


def test_13b_une_case_partagee_par_plusieurs_connexions_ne_monte_que_d_un_cran(game):
    """UN SEUL CRAN PAR RESOLUTION, quel que soit le nombre de connexions.

    Autour d'un Wild — qui remplace tous les symboles — une meme case appartient
    couramment a plusieurs connexions simultanees. Doubler une fois par connexion
    donnerait `x2^nombre de connexions`.

    Regression : un Book reel (freegame high, free spin 4) montrait une case
    partagee par six connexions passer de x1 a x64 en une seule resolution,
    pendant que les cases d'une seule connexion faisaient x1 -> x2.
    """
    partagee = {"reel": 2, "row": 2}
    propre = {"reel": 0, "row": 0}
    game.win_data = {
        "totalWin": 1.0,
        "wins": [
            {"positions": [dict(partagee), dict(propre)]},
            {"positions": [dict(partagee)]},
            {"positions": [dict(partagee)]},
        ],
    }
    game.update_grid_mults()
    assert game.position_multipliers[partagee["reel"]][partagee["row"]] == 2
    assert game.position_multipliers[propre["reel"]][propre["row"]] == 2


def test_13c_le_cran_unique_se_cumule_bien_de_resolution_en_resolution(game):
    """Une seule marche par resolution, mais les resolutions s'enchainent."""
    partagee = {"reel": 2, "row": 2}
    for attendu in (2, 4, 8):
        game.win_data = {
            "totalWin": 1.0,
            "wins": [{"positions": [dict(partagee)]} for _ in range(5)],
        }
        game.update_grid_mults()
        assert game.position_multipliers[partagee["reel"]][partagee["row"]] == attendu


def test_14_la_progression_va_jusqu_a_x4096_et_plafonne(game):
    values = [hit(game) for _ in range(20)]
    expected = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]

    assert values[: len(expected)] == expected
    assert set(values[len(expected) :]) == {MAX_POSITION_MULT}


@pytest.fixture(scope="module")
def base_books():
    """Deux paris de base successifs, joués par le même gamestate."""
    state = GameState(GameConfig())
    state.betmode = "base"
    state.criteria = "basegame"
    books = []
    for sim in (2, 5):
        state.run_spin(sim)
        books.append([dict(event) for event in state.book.events])
    return books


@pytest.fixture(scope="module")
def bonus_book():
    """Un pari qui joue un Bonus complet."""
    state = GameState(GameConfig())
    state.betmode = "bonus"
    state.criteria = "freegame"
    state.run_spin(3)
    return [dict(event) for event in state.book.events]


def first_grid_after(events, start):
    for event in events[start:]:
        if event["type"] == "updateGrid":
            return event["gridMultipliers"]
    return None


def last_grid_before(events, stop):
    grid = None
    for event in events[:stop]:
        if event["type"] == "updateGrid":
            grid = event["gridMultipliers"]
    return grid


def test_15_chaque_pari_de_base_repart_dune_grille_vide(base_books):
    for events in base_books:
        assert events[0]["type"] == "reveal"
        assert first_grid_after(events, 0) == [[0] * 5 for _ in range(5)]


def test_16_la_grille_persiste_entre_les_free_spins(bonus_book):
    marks = [index for index, event in enumerate(bonus_book) if event["type"] == "updateFreeSpin"]
    assert len(marks) >= 2

    for previous, current in zip(marks, marks[1:]):
        assert first_grid_after(bonus_book, current) == last_grid_before(bonus_book, current)
        # La grille ne peut que croître pendant le Bonus.
        before = last_grid_before(bonus_book, previous)
        after = last_grid_before(bonus_book, current)
        assert all(
            after[reel][row] >= before[reel][row] for reel in range(5) for row in range(5)
        )


def test_17_le_premier_free_spin_herite_de_la_grille_du_spin_declencheur(bonus_book):
    trigger = [index for index, event in enumerate(bonus_book) if event["type"] == "freeSpinTrigger"][0]

    assert first_grid_after(bonus_book, trigger) == last_grid_before(bonus_book, trigger)


def test_43_quatre_cases_vierges_paient_x4_puis_passent_a_x2(game):
    """Le x1 implicite compte dans la somme, et le doublement vient APRÈS.

        4 cases vierges -> x1+x1+x1+x1 = x4
        puis la grille passe à x2 sur ces quatre cases
        connexion suivante -> x2+x2+x2+x2 = x8
    """
    from tests.plant_vs_wild.conftest import load, neutral_board, place

    board = place(neutral_board(), [(0, 0), (0, 1), (1, 0), (1, 1)], "H1")
    cells = [(0, 0), (0, 1), (1, 0), (1, 1)]

    load(game, board)
    game.get_clusters_update_wins()

    first = game.win_data["wins"][0]
    assert first["clusterSize"] == 4
    assert first["meta"]["clusterMult"] == 4, "quatre x1 implicites font x4"
    # PAY -> UPGRADE : la grille est encore vierge au moment du paiement.
    assert all(game.position_multipliers[reel][row] == 0 for reel, row in cells)

    game.update_grid_mults()
    assert all(game.position_multipliers[reel][row] == 2 for reel, row in cells)

    load(game, board, keep_charge=True)
    game.get_clusters_update_wins()
    assert game.win_data["wins"][0]["meta"]["clusterMult"] == 8, "quatre x2 font x8"


def test_46_les_quatre_low_paient_exactement_pareil(game):
    """Décision de design : L1, L2, L3 et L4 sont un seul niveau économique."""
    for size in range(4, 26):
        values = {game.config.paytable[(size, symbol)] for symbol in ("L1", "L2", "L3", "L4")}
        assert len(values) == 1, f"taille {size} : les Low divergent ({values})"


def test_47_la_hierarchie_low_puis_high_est_conservee(game):
    """LOW <= H1 <= H2 <= H3 <= H4 à chaque taille, H4 le plus rémunérateur."""
    for size in range(4, 26):
        row = [game.config.paytable[(size, symbol)] for symbol in ("L1", "H1", "H2", "H3", "H4")]
        assert row == sorted(row), f"taille {size} : hiérarchie rompue ({row})"
        assert row[-1] > row[0], f"taille {size} : H4 doit payer plus que les Low"
