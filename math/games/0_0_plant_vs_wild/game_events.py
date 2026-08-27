"""BookEvents de PLANT VS WILD.

Les événements génériques (`reveal`, `winInfo`, `updateTumbleWin`, `setWin`,
`setTotalWin`, `updateFreeSpin`, `freeSpinEnd`, `finalWin`) viennent de
`src/events/events.py` et ne sont pas réécrits ici.

Ce module ne contient que ce qui est propre au jeu :

* `updateGrid`      progression par DOUBLEMENT (le sample cluster incrémente) ;
* `wildMove`        déplacement et charge du Wild principal ;
* `wildFeature`     Rage / Wild Snake / Wild Split ;
* `tumbleBoard`     variante PVW : la case d'arrivée du Wild n'explose pas ;
* `freeSpinTrigger` déclenché par la charge du Wild, pas par des scatters ;
* deux annotations de plateau (`charge`, `temporary`) que le SDK ne peut pas
  porter : `Symbol` utilise `__slots__` et n'accepte aucun attribut nouveau.

Les payloads reprennent EXACTEMENT le contrat déjà validé côté frontend —
`apps/plant-vs-wild/src/game/typesBookEvent.ts`.
"""

from copy import deepcopy

from src.events.events import json_ready_sym, reveal_event as stake_reveal_event
from src.events.event_constants import EventConstants

UPDATE_GRID = "updateGrid"
WILD_MOVE = "wildMove"
WILD_FEATURE = "wildFeature"


def padded(position: dict) -> dict:
    """Position interne (lignes visibles 0..4) → position de book (reel paddé).

    Même décalage que `include_padding_index` dans `win_info_event` : la ligne 0
    du book est le padding haut, 1 à 5 les lignes visibles.
    """
    return {"reel": position["reel"], "row": position["row"] + 1}


def annotate_board(gamestate, board_client: list) -> list:
    """Ajoute au plateau client ce que `Symbol` ne peut pas porter.

    `Symbol.__slots__` interdit d'attacher `charge` ou `temporary` au symbole, et
    `math/src/` est de l'upstream Stake que l'on ne modifie pas. On annote donc
    le plateau déjà sérialisé par le SDK.

    Le drapeau `wild` ajouté par `json_ready_sym` est retiré : il ne fait pas
    partie du contrat frontend, où le nom `W` suffit.
    """
    for reel in board_client:
        for cell in reel:
            cell.pop("wild", None)

    if gamestate.wild_position is not None:
        spot = padded(gamestate.wild_position)
        board_client[spot["reel"]][spot["row"]]["charge"] = int(gamestate.wild_charge)

    for position in gamestate.temporary_wilds:
        spot = padded(position)
        board_client[spot["reel"]][spot["row"]]["temporary"] = True

    return board_client


def client_board(gamestate) -> list:
    """Plateau complet au format du book : 7 lignes, padding compris."""
    attributes = list(gamestate.config.special_symbols.keys())
    board_client = []
    for reel, _ in enumerate(gamestate.board):
        column = [json_ready_sym(gamestate.top_symbols[reel], attributes)]
        column += [json_ready_sym(symbol, attributes) for symbol in gamestate.board[reel]]
        column.append(json_ready_sym(gamestate.bottom_symbols[reel], attributes))
        board_client.append(column)
    return annotate_board(gamestate, board_client)


def reveal_event(gamestate):
    """`reveal` du SDK, puis annotation du Wild."""
    stake_reveal_event(gamestate)
    annotate_board(gamestate, gamestate.book.events[-1]["board"])


def tumble_board_event(gamestate, exploding_positions: list):
    """Disparition et refill.

    Différence avec le SDK : la liste des cases qui explosent est fournie, elle
    n'est pas déduite de `winInfo`. La case d'arrivée du Wild appartient bien à
    la connexion mais n'est PAS recomplétée — le Wild s'y trouve.
    """
    attributes = list(gamestate.config.special_symbols.keys())
    new_symbols = [[] for _ in range(gamestate.config.num_reels)]
    for reel, _ in enumerate(gamestate.new_symbols_from_tumble):
        new_symbols[reel] = [
            json_ready_sym(symbol, attributes) for symbol in gamestate.new_symbols_from_tumble[reel]
        ]
        for cell in new_symbols[reel]:
            cell.pop("wild", None)

    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": EventConstants.TUMBLE_BOARD.value,
            "newSymbols": new_symbols,
            "explodingSymbols": sorted(
                [padded(position) for position in exploding_positions],
                key=lambda p: (p["reel"], p["row"]),
            ),
        }
    )


def update_grid_event(gamestate):
    """Grille COMPLÈTE des multiplicateurs, lignes visibles uniquement (5×5)."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": UPDATE_GRID,
            "gridMultipliers": deepcopy(gamestate.position_multipliers),
        }
    )


def wild_move_event(gamestate, source: dict, destination: dict, charge: int):
    """Déplacement du Wild principal. `charge` est ABSOLU, jamais un incrément."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": WILD_MOVE,
            "from": padded(source),
            "to": padded(destination),
            "charge": int(charge),
        }
    )


def wild_feature_rage_event(gamestate, wild_from: dict, wild_to: dict):
    """Rage : le Wild se recentre, les 24 autres cases sont renouvelées SUR PLACE.

    Le plateau complet est transmis parce qu'un `tumbleBoard` ferait chuter le
    Wild que l'on vient de recentrer.
    """
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": WILD_FEATURE,
            "feature": "rage",
            "wildFrom": padded(wild_from),
            "wildTo": padded(wild_to),
            "board": client_board(gamestate),
        }
    )


def wild_feature_snake_event(gamestate, source: dict, path: list, destination: dict, symbol: str):
    """Wild Snake : trajet ordonné (`from` et `to` exclus) et plateau final."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": WILD_FEATURE,
            "feature": "wildSnake",
            "from": padded(source),
            "path": [padded(step) for step in path],
            "to": padded(destination),
            "symbol": symbol,
            "board": client_board(gamestate),
        }
    )


def wild_feature_split_event(gamestate, positions: list):
    """Wild Split : les Wild temporaires, posés aux cases indiquées."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": WILD_FEATURE,
            "feature": "wildSplit",
            "positions": [padded(position) for position in positions],
        }
    )


def free_spin_trigger_event(gamestate, positions: list, retrigger: bool = False):
    """Entrée en Bonus / retrigger.

    Chez nous le déclencheur n'est pas un groupe de scatters mais la charge du
    Wild : `positions` porte la case du Wild. `totalFs` est le NOUVEAU total.
    """
    assert gamestate.tot_fs > 0, "tot_fs doit être > 0"
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": (
                EventConstants.FREESPINRETRIGGER.value if retrigger else EventConstants.FREESPINTRIGGER.value
            ),
            "totalFs": int(gamestate.tot_fs),
            "positions": [padded(position) for position in positions],
        }
    )
