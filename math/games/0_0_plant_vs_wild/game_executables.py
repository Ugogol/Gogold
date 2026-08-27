"""Actions groupées de PLANT VS WILD.

Grille de multiplicateurs, Wild principal, Wild temporaires et features. Ces
fonctions n'évaluent rien elles-mêmes : elles orchestrent `Cluster`, `Tumble` et
les events.
"""

import random

from game_calculations import GameCalculations, WILD_NAME
from game_config import MAX_POSITION_MULT, WILD_MAX_CHARGE
from game_events import (
    free_spin_trigger_event,
    tumble_board_event,
    update_grid_event,
    wild_feature_rage_event,
    wild_feature_snake_event,
    wild_feature_split_event,
    wild_move_event,
)
from src.calculations.cluster import Cluster
from src.events.events import update_freespin_event


class GameExecutables(GameCalculations):
    """Fonctions dépendantes du jeu, regroupées."""

    # ── Grille de multiplicateurs positionnels ──────────────────────────────

    def reset_grid_mults(self) -> None:
        """Grille 5x5 remise à zéro. `0` est le x1 implicite."""
        self.position_multipliers = [
            [0 for _ in range(self.config.num_rows[reel])] for reel in range(self.config.num_reels)
        ]

    def update_grid_mults(self) -> None:
        """Progression par DOUBLEMENT des cases ayant participé à une connexion.

        `0 -> 2 -> 4 -> 8 ... -> 4096`. C'est la différence de fond avec le
        sample cluster, qui incrémente de 1 : le frontend affiche la valeur brute
        reçue, elle doit donc déjà être le multiplicateur montré au joueur.
        """
        if self.win_data["totalWin"] <= 0:
            return

        for win in self.win_data["wins"]:
            for pos in win["positions"]:
                current = self.position_multipliers[pos["reel"]][pos["row"]]
                doubled = 2 if current == 0 else current * 2
                self.position_multipliers[pos["reel"]][pos["row"]] = min(doubled, MAX_POSITION_MULT)

        update_grid_event(self)

    # ── Connexions ──────────────────────────────────────────────────────────

    def get_clusters_update_wins(self) -> None:
        """Cherche les connexions et met à jour le win manager."""
        clusters = Cluster.get_clusters(self.board, "wild")
        self.board, self.win_data = self.evaluate_clusters_with_grid(
            config=self.config,
            board=self.board,
            clusters=clusters,
            pos_mult_grid=self.position_multipliers,
            global_multiplier=self.global_multiplier,
            return_data={"totalWin": 0, "wins": []},
        )

        Cluster.record_cluster_wins(self)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        self.win_manager.tumble_win = self.win_data["totalWin"]

    def winning_positions(self) -> list:
        """Cases libérées par la résolution courante."""
        return [pos for win in self.win_data["wins"] for pos in win["positions"]]

    @property
    def temporary_wilds(self) -> list:
        """Cases des Wild temporaires, retrouvées par IDENTITÉ d'objet.

        Suivre une position ne suffit pas : un tumble fait descendre les
        symboles survivants, et une position mémorisée désignerait alors une
        autre case — potentiellement celle du Wild principal, qui serait effacé
        à l'expiration.
        """
        if not self.temporary_wild_symbols:
            return []
        return [
            position
            for position in self.all_positions()
            if any(self.symbol_at(position) is symbol for symbol in self.temporary_wild_symbols)
        ]

    # ── Wild principal ──────────────────────────────────────────────────────

    def sync_wild_state(self) -> None:
        """Retrouve le Wild principal sur le plateau.

        Le suivi se fait par identité d'objet : tant que le même symbole survit
        aux cascades, il garde la charge accumulée dans CE spin. Un Wild arrivé
        par un refill alors qu'aucun Wild n'était en jeu repart de zéro. La
        charge d'un spin à l'autre est remise à zéro par `reset_spin_state`.
        """
        board_wilds = [pos for pos in self.wild_positions() if pos not in self.temporary_wilds]

        for pos in board_wilds:
            if self.symbol_at(pos) is self.wild_symbol:
                self.wild_position = pos
                return

        if board_wilds:
            self.wild_position = board_wilds[0]
            self.wild_symbol = self.symbol_at(self.wild_position)
            self.wild_charge = 0
        else:
            self.wild_position = None
            self.wild_symbol = None
            self.wild_charge = 0

    def enforce_single_main_wild(self) -> None:
        """Au plus UN Wild principal sur le plateau (règle 6).

        Les bandes contiennent des `W` : un tirage ou un refill peut en amener
        plusieurs. Les surnuméraires sont remplacés par un symbole de la bande.
        Les Wild temporaires du Split ne sont pas concernés.
        """
        board_wilds = [pos for pos in self.wild_positions() if pos not in self.temporary_wilds]
        if len(board_wilds) <= 1:
            return

        keep = next(
            (pos for pos in board_wilds if self.symbol_at(pos) is self.wild_symbol),
            board_wilds[0],
        )
        for pos in board_wilds:
            if pos != keep:
                self.replace_symbol(pos, self.filler_name(pos["reel"]))

    def keep_wild_out_of_padding(self) -> None:
        """Le Wild n'arrive JAMAIS par une case de padding.

        Un symbole de padding est un vrai symbole : au tumble suivant il descend
        dans le plateau visible. Si c'est un Wild alors qu'un Wild principal est
        déjà en jeu, le joueur en voit deux. Et le corriger après coup ne suffit
        pas : le frontend détient déjà ce symbole — il lui a été annoncé dans le
        `newSymbols` d'un tumble précédent — et aucun event ne peut le lui
        reprendre. On l'écarte donc au moment où il est tiré, avant qu'il
        n'entre dans un book.

        Le Wild continue d'apparaître normalement au reveal et dans les cases
        visibles d'un refill : ces deux chemins-là, eux, sont annoncés.
        """
        pending = getattr(self, "new_symbols_from_tumble", None)
        for reel in range(self.config.num_reels):
            for holder in (self.top_symbols, self.bottom_symbols):
                if holder is None or holder[reel].name != WILD_NAME:
                    continue
                replacement = self.create_symbol(self.filler_name(reel))
                if pending:
                    for index, symbol in enumerate(pending[reel]):
                        if symbol is holder[reel]:
                            pending[reel][index] = replacement
                            break
                holder[reel] = replacement

    def place_carried_wild(self) -> None:
        """En Bonus, le Wild principal est CONSERVÉ d'un Free Spin à l'autre.

        Règle 12 : « Wild principal conservé selon le state/book ». Le plateau
        vient d'être tiré ; on efface ses Wild et on repose celui du Free Spin
        précédent, à SA CASE. Seule la position est conservée : la charge, elle,
        a déjà été remise à zéro par `reset_spin_state`. Le retrigger demande
        donc quatre connexions à l'intérieur d'un même Free Spin.
        """
        if self.gametype != self.config.freegame_type or self.wild_position is None:
            return

        for position in self.wild_positions():
            if position != self.wild_position:
                self.replace_symbol(position, self.filler_name(position["reel"]))

        self.replace_symbol(self.wild_position, WILD_NAME)
        self.wild_symbol = self.symbol_at(self.wild_position)

    def guarantee_wild(self) -> None:
        """Un Wild est obligatoire à chaque Free Spin (règle 12)."""
        if self.gametype != self.config.freegame_type:
            return
        if self.wild_positions():
            return
        position = random.choice(self.all_positions())
        self.replace_symbol(position, WILD_NAME)

    def handle_wild_connection(self) -> None:
        """Déplacement et charge du Wild lorsqu'une connexion l'implique.

        La destination est choisie parmi les cases libérées par la connexion —
        la case du Wild lui-même en fait partie, il peut donc ne pas bouger. Le
        déplacement précède le refill : le Wild n'est jamais détruit.

        UNE SEULE CHARGE PAR CASCADE. Un Wild peut compléter deux groupes à la
        fois — il appartient alors aux deux et rapporte dans les deux — mais il
        ne se charge que d'un cran. La fonction est appelée une fois par tour de
        cascade et toutes les cases gagnantes du tour sont réunies dans
        `released` : la règle est structurelle, pas un cas particulier.
        """
        if self.win_data["totalWin"] <= 0 or self.wild_position is None:
            return

        released = self.winning_positions()
        if self.wild_position not in released:
            return

        source = dict(self.wild_position)
        destination = random.choice(released)

        self.wild_charge = min(self.wild_charge + 1, WILD_MAX_CHARGE)
        wild_move_event(self, source, destination, self.wild_charge)

        self.swap_symbols(source, destination)
        self.wild_position = destination
        # La case d'arrivée n'est pas recomplétée : le Wild l'occupe.
        self.symbol_at(destination).explode = False

        if self.wild_charge >= WILD_MAX_CHARGE:
            # Règle 10 : on n'interrompt pas le spin. Le trigger attend la
            # stabilisation du plateau.
            self.bonus_pending = True

    # ── Tumble ──────────────────────────────────────────────────────────────

    def tumble_game_board(self) -> None:
        """Retire les symboles marqués et recomplète.

        La liste des cases qui explosent est relevée AVANT la chute, sur les
        drapeaux `explode` réellement posés — la case d'arrivée du Wild en est
        donc absente.
        """
        exploding = [pos for pos in self.all_positions() if self.symbol_at(pos).explode]

        self.tumble_board()

        self.keep_wild_out_of_padding()
        self.enforce_single_main_wild()
        self.sync_wild_state()
        tumble_board_event(self, exploding)

    # ── Free spins ──────────────────────────────────────────────────────────

    def update_freespin(self) -> None:
        """Appelé avant chaque nouveau reveal du Bonus."""
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.win_data = {"totalWin": 0, "wins": []}

    def update_freespin_amount(self) -> None:
        """Entrée en Bonus : nombre de Free Spins et event de déclenchement."""
        if self.wild_position is None:
            # Entrée forcée d'un mode de test : aucun Wild n'a déclenché quoi
            # que ce soit. On en désigne un pour que le Bonus démarre malgré
            # tout sur une case connue, celle qu'annonce le trigger.
            self.wild_position = {
                "reel": self.config.num_reels // 2,
                "row": self.config.num_rows[0] // 2,
            }

        self.tot_fs = self.config.freespin_triggers[self.config.basegame_type][WILD_MAX_CHARGE]
        free_spin_trigger_event(self, self.trigger_positions(), retrigger=False)
        self.bonus_pending = False

    def update_fs_retrigger_amt(self) -> None:
        """Retrigger : le total augmente, l'event porte le NOUVEAU total."""
        self.tot_fs += self.config.freespin_triggers[self.config.freegame_type][WILD_MAX_CHARGE]
        free_spin_trigger_event(self, self.trigger_positions(), retrigger=True)
        self.bonus_pending = False

    def trigger_positions(self) -> list:
        """Cases mises en avant à l'annonce : celle du Wild déclencheur.

        C'est aussi la case sur laquelle le premier Free Spin démarrera.
        """
        if self.wild_position is not None:
            return [dict(self.wild_position)]
        return [{"reel": self.config.num_reels // 2, "row": self.config.num_rows[0] // 2}]

    # ── Features de dead spin ───────────────────────────────────────────────

    def select_dead_spin_feature(self):
        """Quelle feature déclencher, ou `None`.

        Les fréquences ne sont pas décidées à cette étape. Par défaut aucune
        feature ne part : les tests et les books canoniques utilisent
        `forced_features`, et le balancing branchera une vraie distribution.
        """
        if self.forced_features:
            return self.forced_features.pop(0)
        return None

    def trigger_dead_spin_feature(self) -> bool:
        """Au plus UNE feature par dead spin (règle 17)."""
        if self.gametype != self.config.freegame_type:
            return False
        if self.feature_used_this_spin or self.win_manager.spin_win > 0:
            return False
        if self.wild_position is None:
            return False

        feature = self.select_dead_spin_feature()
        if feature is None:
            return False

        self.feature_used_this_spin = True
        if feature == "rage":
            self.apply_rage()
        elif feature == "wildSnake":
            self.apply_wild_snake()
        elif feature == "wildSplit":
            self.apply_wild_split()
        else:
            raise ValueError("feature inconnue : " + str(feature))
        return True

    def apply_rage(self) -> None:
        """Le Wild se recentre, les 24 autres cases sont renouvelées sur place.

        La grille de multiplicateurs n'est pas touchée. Le plateau complet est
        transmis : un `tumbleBoard` ferait chuter le Wild recentré.
        """
        wild_from = dict(self.wild_position)
        wild_to = {"reel": self.config.num_reels // 2, "row": self.config.num_rows[0] // 2}

        self.swap_symbols(wild_from, wild_to)
        self.wild_position = wild_to

        for position in self.all_positions():
            if position != wild_to:
                self.replace_symbol(position, self.filler_name(position["reel"]))

        self.temporary_wild_symbols = []
        wild_feature_rage_event(self, wild_from, wild_to)

    def snake_symbol(self) -> str:
        """Symbole vers lequel le Wild rampe.

        Le partage Low/High n'est pas décidé à cette étape : le pool vient de la
        bande courante, donc H4 reste impossible en Base Game.
        """
        candidates = sorted({str(name) for name in self.reelstrip[0] if str(name) != WILD_NAME})
        return random.choice(candidates)

    def snake_path(self, source: dict) -> tuple:
        """Trajet orthogonal, sans case revisitée, longueur tirée de la config.

        Retourne `(path, destination)` : `path` est le trajet intermédiaire, la
        destination est la case finale du Wild. Le contrat frontend attend `from`
        et `to` exclus du trajet.
        """
        minimum, maximum = self.config.snake_path_length
        target = random.randint(minimum, maximum)

        visited = [dict(source)]
        while len(visited) - 1 < target:
            options = [pos for pos in self.orthogonal_neighbours(visited[-1]) if pos not in visited]
            if not options:
                break
            visited.append(random.choice(options))

        steps = visited[1:]
        assert len(steps) >= 2, "un trajet de Snake doit compter au moins deux pas"
        return steps[:-1], steps[-1]

    def apply_wild_snake(self) -> None:
        """Le Wild rampe et convertit les cases traversées.

        Le plateau final est la source de vérité : la case de départ et le trajet
        prennent le symbole cible, le Wild occupe la case d'arrivée. Le Snake ne
        donne aucune charge (règle 15).
        """
        source = dict(self.wild_position)
        path, destination = self.snake_path(source)
        symbol = self.snake_symbol()

        wild = self.symbol_at(source)
        for position in [source] + path:
            self.replace_symbol(position, symbol)
        self.board[destination["reel"]][destination["row"]] = wild

        self.wild_position = destination
        self.temporary_wild_symbols = []
        wild_feature_snake_event(self, source, path, destination, symbol)

    def apply_wild_split(self) -> None:
        """Le Wild se dédouble en Wild temporaires, à usage unique.

        Ils participent aux connexions mais ne portent aucune charge : seule la
        case suivie par `wild_position` fait monter le compteur.
        """
        free = [
            position for position in self.all_positions() if self.symbol_at(position).name != WILD_NAME
        ]
        positions = random.sample(free, min(self.config.split_wild_count, len(free)))
        positions.sort(key=lambda p: (p["reel"], p["row"]))

        for position in positions:
            self.replace_symbol(position, WILD_NAME)
        self.temporary_wild_symbols = [self.symbol_at(position) for position in positions]

        wild_feature_split_event(self, positions)

    def expire_temporary_wilds(self) -> None:
        """Fin de spin : retour à un seul Wild principal (règle 16)."""
        for position in self.temporary_wilds:
            self.replace_symbol(position, self.filler_name(position["reel"]))
        self.temporary_wild_symbols = []
