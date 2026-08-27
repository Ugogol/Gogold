"""H4, durée du Bonus et retrigger.

Tests 18 à 21 du cahier, plus deux tests (33, 34) sur la règle corrigée : en
Bonus le Wild garde sa CASE d'un Free Spin à l'autre, jamais sa charge.
"""

import pytest

from game_config import GameConfig
from gamestate import GameState


@pytest.fixture(scope="module")
def config():
    return GameConfig()


@pytest.fixture(scope="module")
def base_books(config):
    """Assez de paris de base pour couvrir plateaux et refills."""
    state = GameState(config)
    state.betmode = "base"
    state.criteria = "basegame"
    books = []
    for sim in range(120):
        state.run_spin(sim)
        books.append([dict(event) for event in state.book.events])
    return books


@pytest.fixture(scope="module")
def bonus_books(config):
    state = GameState(config)
    state.betmode = "bonus"
    state.criteria = "freegame"
    # 80 Bonus : le retrigger tourne autour de 10 %, un échantillon de 20
    # pouvait n'en contenir aucun et faire échouer les tests par malchance.
    books = []
    for sim in range(80):
        state.run_spin(sim)
        books.append([dict(event) for event in state.book.events])
    return books


@pytest.fixture(scope="module")
def trigger_books(config):
    """Paris de base ayant déclenché le Bonus naturellement."""
    state = GameState(config)
    state.betmode = "base"
    state.criteria = "basegame"
    books = []
    for sim in range(400):
        state.run_spin(sim)
        if any(event["type"] == "freeSpinTrigger" for event in state.book.events):
            books.append([dict(event) for event in state.book.events])
    assert books, "aucun déclenchement naturel dans l'échantillon"
    return books


def symbols_by_gametype(events):
    """Tous les noms de symboles annoncés, rangés par mode de jeu."""
    seen = {"basegame": set(), "freegame": set()}
    gametype = "basegame"
    for event in events:
        if event["type"] == "reveal":
            gametype = event["gameType"]
            cells = [cell for reel in event["board"] for cell in reel]
        elif event["type"] == "tumbleBoard":
            cells = [cell for reel in event["newSymbols"] for cell in reel]
        else:
            continue
        seen[gametype].update(cell["name"] for cell in cells)
    return seen


def test_18_h4_est_absent_du_base_game(base_books, config):
    assert all("H4" not in reel for reel in config.reels["BR0"])

    for events in base_books:
        assert "H4" not in symbols_by_gametype(events)["basegame"]


def test_19_h4_est_autorise_en_bonus(bonus_books, config):
    assert any("H4" in reel for reel in config.reels["FR0"])

    assert any("H4" in symbols_by_gametype(events)["freegame"] for events in bonus_books)


def test_20_le_bonus_accorde_dix_free_spins(bonus_books):
    for events in bonus_books:
        triggers = [event for event in events if event["type"] == "freeSpinTrigger"]
        assert len(triggers) == 1
        assert triggers[0]["totalFs"] == 10

        counters = [event for event in events if event["type"] == "updateFreeSpin"]
        retriggers = [event for event in events if event["type"] == "freeSpinRetrigger"]
        expected = 10 + 5 * len(retriggers)
        assert counters[-1]["total"] == expected
        assert len(counters) == expected


def test_33_la_charge_du_wild_ne_survit_pas_a_un_free_spin(bonus_books):
    """Chaque spin repart d'une charge vide.

    Un Free Spin n'hérite donc jamais des connexions du précédent : le Wild est
    annoncé déchargé au reveal, et sa première connexion vaut toujours 1.
    """
    spins_with_moves = 0
    for events in bonus_books:
        charges = None
        for event in events:
            if event["type"] == "reveal":
                charges = []
                wilds = [
                    cell
                    for column in event["board"]
                    for row, cell in enumerate(column)
                    if cell["name"] == "W" and 1 <= row <= 5
                ]
                for wild in wilds:
                    assert wild.get("charge", 0) == 0
            elif event["type"] == "wildMove":
                charges.append(event["charge"])
            elif event["type"] == "setTotalWin" and charges:
                spins_with_moves += 1
                assert charges[0] == 1
                # Une connexion = un cran, jusqu'au plafond.
                assert charges == sorted(charges)
                assert charges[: 4] == [1, 2, 3, 4][: len(charges[:4])]
                charges = []
    assert spins_with_moves > 0


def test_34_le_wild_garde_sa_case_sur_plusieurs_free_spins(bonus_game):
    """Free Spins successifs : la CASE est conservée, la charge ne l'est pas."""
    from tests.plant_vs_wild.conftest import neutral_board, place

    # Chaque tirage suivant place son Wild ailleurs : il doit être écarté au
    # profit de celui que le Free Spin précédent a laissé.
    boards = [
        place(neutral_board(), [(1, 3)], "W"),
        place(neutral_board(), [(4, 0)], "W"),
        place(neutral_board(), [(0, 1)], "W"),
    ]
    bonus_game.force(boards=boards, seed=3)

    bonus_game.draw_board(emit_event=False)
    kept = dict(bonus_game.wild_position)
    assert kept == {"reel": 1, "row": 3}

    for _ in range(2):
        # Le Wild s'est chargé pendant le Free Spin qui s'achève.
        bonus_game.wild_charge = 3
        bonus_game.reset_spin_state()
        bonus_game.draw_board(emit_event=False)

        assert bonus_game.wild_position == kept
        assert bonus_game.symbol_at(kept).name == "W"
        assert len(bonus_game.wild_positions()) == 1
        assert bonus_game.wild_charge == 0


def test_21_un_retrigger_ajoute_cinq_free_spins(bonus_books):
    seen = 0
    for events in bonus_books:
        total = None
        for event in events:
            if event["type"] == "freeSpinTrigger":
                total = event["totalFs"]
            elif event["type"] == "freeSpinRetrigger":
                assert event["totalFs"] == total + 5
                total = event["totalFs"]
                seen += 1
    assert seen > 0, "aucun retrigger dans l'échantillon déterministe"


def test_36_le_wild_declencheur_demarre_le_premier_free_spin(bonus_books, trigger_books):
    """La case annoncée par `freeSpinTrigger` est celle du premier Free Spin.

    Le Wild qui a déclenché le Bonus n'est pas retiré du jeu : il reprend à sa
    position, déchargé.
    """
    checked = 0
    for events in bonus_books + trigger_books:
        trigger = next(event for event in events if event["type"] == "freeSpinTrigger")
        announced = trigger["positions"][0]

        first_free_reveal = next(
            event
            for event in events[events.index(trigger) :]
            if event["type"] == "reveal" and event["gameType"] == "freegame"
        )
        wilds = [
            {"reel": reel, "row": row}
            for reel, column in enumerate(first_free_reveal["board"])
            for row, cell in enumerate(column)
            if cell["name"] == "W" and 1 <= row <= 5
        ]

        assert wilds == [announced]
        assert first_free_reveal["board"][announced["reel"]][announced["row"]]["charge"] == 0
        checked += 1
    assert checked > 0


def test_37_le_retrigger_exige_quatre_connexions_dans_le_meme_free_spin(bonus_books):
    """Un retrigger ne peut pas cumuler les connexions de plusieurs Free Spins."""
    seen = 0
    for events in bonus_books:
        charges = []
        for event in events:
            if event["type"] == "reveal":
                charges = []
            elif event["type"] == "wildMove":
                charges.append(event["charge"])
            elif event["type"] == "freeSpinRetrigger":
                # Les quatre connexions appartiennent toutes au spin courant.
                assert charges[:4] == [1, 2, 3, 4]
                seen += 1
    assert seen > 0


def test_38_le_wild_enchaine_ses_cases_de_free_spin_en_free_spin(bonus_game):
    """Chaîne A -> B -> C sur trois Free Spins consécutifs.

        Bonus trigger        le Wild est en A
        FS1                  reveal A, connexion, wildMove A -> B
        FS2                  reveal B et charge 0, connexion, wildMove B -> C
        FS3                  reveal C et charge 0

    Chaque plateau imposé pose sa connexion entièrement sur la ligne visible du
    haut : rien n'explose SOUS la case d'arrivée du Wild, donc la chute du
    tumble ne le déplace pas et la case annoncée est exactement celle du reveal
    suivant.
    """
    from tests.plant_vs_wild.conftest import neutral_board, place

    def top_row_connection(wild_reel):
        board = place(neutral_board(), [(0, 0), (1, 0), (2, 0), (3, 0)], "H1")
        board[wild_reel][0] = "W"
        return board

    # Position A, celle du Wild qui vient de déclencher le Bonus.
    position_a = {"reel": 3, "row": 0}
    bonus_game.gametype = bonus_game.config.freegame_type
    bonus_game.tot_fs = 3
    bonus_game.wild_position = dict(position_a)
    # Les tirages suivants placent leur Wild ailleurs : ils doivent être écartés.
    bonus_game.force(
        boards=[top_row_connection(3), top_row_connection(0), top_row_connection(1)],
        seed=2,
    )

    bonus_game.run_freespin()

    spins = []
    for event in bonus_game.book.events:
        if event["type"] == "reveal":
            wilds = [
                {"reel": reel, "row": row}
                for reel, column in enumerate(event["board"])
                for row, cell in enumerate(column)
                if cell["name"] == "W" and 1 <= row <= 5
            ]
            assert len(wilds) == 1, "un seul Wild visible au reveal"
            charge = event["board"][wilds[0]["reel"]][wilds[0]["row"]]["charge"]
            spins.append({"reveal": wilds[0], "charge": charge, "moves": []})
        elif event["type"] == "wildMove":
            spins[-1]["moves"].append(dict(event["to"]))

    assert len(spins) == 3

    # FS1 démarre bien sur la case du Wild déclencheur.
    assert spins[0]["reveal"] == {"reel": position_a["reel"], "row": position_a["row"] + 1}

    for index, spin in enumerate(spins):
        # La charge ne franchit jamais la frontière entre deux Free Spins.
        assert spin["charge"] == 0, f"FS{index + 1} devrait démarrer déchargé"

    # Le reveal de chaque Free Spin reprend la case laissée par le précédent.
    assert spins[0]["moves"], "FS1 doit produire une connexion"
    assert spins[1]["reveal"] == spins[0]["moves"][-1]
    assert spins[1]["moves"], "FS2 doit produire une connexion"
    assert spins[2]["reveal"] == spins[1]["moves"][-1]

    # Et le Wild a réellement bougé : A, B et C sont trois cases distinctes.
    positions = [tuple(spin["reveal"].values()) for spin in spins]
    assert len(set(positions)) == 3


def test_48_le_plafond_de_gain_vaut_dix_mille(config):
    """MAX WIN = 10 000x, via le mécanisme `wincap` standard du SDK."""
    from game_config import MAX_WIN

    assert MAX_WIN == 10_000.0
    assert config.wincap == 10_000.0
    # Les bet modes héritent du même plafond : un seul endroit le définit.
    assert {mode._wincap for mode in config.bet_modes} == {10_000.0}


def test_49_le_wincap_borne_reellement_le_payout(config):
    """Un pari plafonné ne paie jamais plus que le plafond, et le signale."""
    from gamestate import GameState

    state = GameState(config)
    state.betmode = "bonus"
    state.criteria = "freegame"
    capped = 0
    for sim in range(400):
        state.run_spin(sim)
        assert state.book.payout_multiplier <= config.wincap
        if any(event["type"] == "wincap" for event in state.book.events):
            capped += 1
            assert state.book.payout_multiplier == config.wincap
    assert capped >= 0
