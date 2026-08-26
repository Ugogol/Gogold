"""Calculs de plateau propres à PLANT VS WILD.

Rien ici ne remplace le moteur Stake : `Cluster` reste le seul détecteur de
connexions et `Tumble` la seule physique de chute. On ajoute uniquement :

* l'évaluation d'un cluster tenant compte de la grille de multiplicateurs
  positionnels (le SDK ne connaît que les multiplicateurs portés par un
  symbole) ;
* quelques manipulations de plateau utilisées par le Wild et les features.
"""

import random

from src.calculations.cluster import Cluster
from src.calculations.board import Board
from src.config.config import Config
from src.executables.executables import Executables

WILD_NAME = "W"


class GameCalculations(Executables):
    """Fonctions de calcul dépendantes du jeu."""

    def evaluate_clusters_with_grid(
        self,
        config: Config,
        board: Board,
        clusters: dict,
        pos_mult_grid: list,
        global_multiplier: int = 1,
        return_data: dict = None,
    ):
        """Paiement d'un cluster, multiplicateurs de case compris.

        Le multiplicateur d'une connexion est la SOMME des multiplicateurs des
        cases qui y participent, avec un plancher à 1 : une case jamais activée
        vaut 0 dans la grille et ne rapporte donc rien de plus.

        `MIN_CLUSTER_SIZE` n'est pas testé ici : la paytable ne contient aucune
        entrée en dessous de 4, donc un groupe de 3 n'est jamais payé.
        """
        if return_data is None:
            return_data = {"totalWin": 0, "wins": []}
        total_win = 0
        for sym in clusters:
            for cluster in clusters[sym]:
                syms_in_cluster = len(cluster)
                if (syms_in_cluster, sym) not in config.paytable:
                    continue

                board_mult = max(sum(pos_mult_grid[reel][row] for reel, row in cluster), 1)
                sym_win = config.paytable[(syms_in_cluster, sym)]
                symwin_mult = sym_win * board_mult * global_multiplier
                total_win += symwin_mult

                json_positions = [{"reel": reel, "row": row} for reel, row in cluster]
                central_pos = Cluster.get_central_cluster_position(json_positions)
                return_data["wins"] += [
                    {
                        "symbol": sym,
                        "clusterSize": syms_in_cluster,
                        "win": symwin_mult,
                        "positions": json_positions,
                        "meta": {
                            "globalMult": global_multiplier,
                            "clusterMult": board_mult,
                            "winWithoutMult": sym_win,
                            "overlay": {"reel": central_pos[0], "row": central_pos[1]},
                        },
                    }
                ]

                for reel, row in cluster:
                    board[reel][row].explode = True

        return_data["totalWin"] += total_win
        return board, return_data

    # ── Manipulations de plateau ────────────────────────────────────────────

    def all_positions(self) -> list:
        """Toutes les cases visibles, ordre de lecture."""
        return [
            {"reel": reel, "row": row}
            for reel in range(self.config.num_reels)
            for row in range(self.config.num_rows[reel])
        ]

    def symbol_at(self, position: dict):
        """Symbole occupant une case."""
        return self.board[position["reel"]][position["row"]]

    def wild_positions(self) -> list:
        """Toutes les cases portant un `W`, temporaires comprises."""
        return [pos for pos in self.all_positions() if self.symbol_at(pos).name == WILD_NAME]

    def filler_name(self, reel: int) -> str:
        """Un symbole non-Wild tiré de la bande courante.

        Passer par la bande garantit la règle « H4 absent du Base Game » sans
        aucune liste parallèle : `BR0` n'en contient pas.
        """
        candidates = sorted({str(name) for name in self.reelstrip[reel] if str(name) != WILD_NAME})
        return random.choice(candidates)

    def replace_symbol(self, position: dict, name: str) -> None:
        """Remplace un symbole, y compris dans les nouveaux symboles d'un tumble.

        Le plateau et `new_symbols_from_tumble` partagent les mêmes objets : le
        remplacement doit se faire des deux côtés, sinon l'event `tumbleBoard`
        annoncerait un symbole que le plateau ne contient pas.
        """
        reel, row = position["reel"], position["row"]
        previous = self.board[reel][row]
        replacement = self.create_symbol(name)
        self.board[reel][row] = replacement

        pending = getattr(self, "new_symbols_from_tumble", None)
        if pending:
            for index, symbol in enumerate(pending[reel]):
                if symbol is previous:
                    pending[reel][index] = replacement
                    break

    def swap_symbols(self, first: dict, second: dict) -> None:
        """Échange deux cases.

        C'est le mécanisme du déplacement du Wild : le Wild et le symbole de la
        case d'arrivée permutent, ce qui préserve le contenu du plateau et
        laisse l'ancienne case du Wild exploser avec le reste de la connexion.
        """
        a, b = self.board[first["reel"]][first["row"]], self.board[second["reel"]][second["row"]]
        self.board[first["reel"]][first["row"]] = b
        self.board[second["reel"]][second["row"]] = a

    def orthogonal_neighbours(self, position: dict) -> list:
        """Cases voisines dans le plateau, sans diagonale."""
        reel, row = position["reel"], position["row"]
        candidates = [
            {"reel": reel - 1, "row": row},
            {"reel": reel + 1, "row": row},
            {"reel": reel, "row": row - 1},
            {"reel": reel, "row": row + 1},
        ]
        return [
            pos
            for pos in candidates
            if 0 <= pos["reel"] < self.config.num_reels and 0 <= pos["row"] < self.config.num_rows[pos["reel"]]
        ]
