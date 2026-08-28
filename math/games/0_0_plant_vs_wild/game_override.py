"""Surcharges d'état pour PLANT VS WILD.

Deux différences structurelles avec le sample cluster :

* le Bonus ne se déclenche pas sur des scatters mais sur la 4e connexion du
  Wild ; toutes les fonctions du SDK qui comptent des scatters sont donc
  redéfinies ;
* la grille de multiplicateurs se remet à zéro à chaque nouveau pari mais
  PERSISTE à l'entrée du Bonus : le premier Free Spin hérite de celle du spin
  déclencheur.
"""

import random

from game_events import reveal_event
from game_executables import GameExecutables
from game_config import WILD_MAX_CHARGE, BONUS_BUCKET_BOUNDS


class GameStateOverride(GameExecutables):
    """Étend ou remplace les fonctions universelles de `state.py`."""

    def reset_book(self) -> None:
        """Nouveau pari : état complètement propre.

        La grille est remise à zéro ICI et nulle part ailleurs dans le cycle de
        base. C'est le garde-fou contre la fuite d'état entre simulations : une
        grille laissée par un Bonus précédent ne peut pas se retrouver dans un
        spin de base suivant.
        """
        super().reset_book()
        self.tumble_win = 0
        self.reset_grid_mults()
        self.wild_position = None
        self.wild_symbol = None
        self.reset_spin_state()

    def reset_fs_spin(self) -> None:
        """Entrée en Bonus.

        Deux choses passent la frontière Base -> Bonus, et deux seulement :

        * la grille de multiplicateurs, héritée du spin déclencheur puis
          persistante d'un Free Spin à l'autre ;
        * la CASE du Wild déclencheur, sur laquelle le premier Free Spin
          démarre et qui est ensuite conservée jusqu'à la sortie.

        La charge, elle, est remise à zéro par `reset_spin_state` — comme au
        début de n'importe quel spin.
        """
        super().reset_fs_spin()
        self.reset_spin_state()

    def reset_spin_state(self) -> None:
        """État valable pour un seul spin.

        La charge du Wild repart de zéro à CHAQUE spin, Base Game comme Free
        Spin. Elle ne se cumule qu'à l'intérieur d'un spin, au fil des cascades.
        En Bonus le Wild garde sa case d'un Free Spin à l'autre, mais pas sa
        charge : il faut donc quatre connexions dans un même Free Spin pour
        obtenir le retrigger.
        """
        self.temporary_wild_symbols = []
        self.feature_used_this_spin = False
        self.wild_charge = 0
        self.bonus_pending = False
        self.cascade_cap_reached = False

    def assign_special_sym_function(self) -> None:
        """Aucun attribut spécial n'est posé à la création d'un symbole.

        La charge du Wild et le drapeau `temporary` ne peuvent pas vivre sur un
        `Symbol` (`__slots__` upstream) : ils sont portés par le gamestate et
        ajoutés au plateau client par `game_events.annotate_board`.

        Le SDK appelle cette fonction une seule fois, avant le premier
        `reset_book` : c'est aussi l'endroit où les listes de forçage sont
        initialisées, pour qu'elles survivent aux resets successifs.
        """
        self.special_symbol_functions = {}
        self.temporary_wild_symbols = []
        self.forced_boards = []
        self.forced_features = []

    # ── Tirage du plateau ───────────────────────────────────────────────────

    def draw_board(self, emit_event: bool = True, trigger_symbol: str = "wild") -> None:
        """Tirage d'un plateau PLANT VS WILD.

        La version du SDK force un nombre de scatters quand la distribution
        demande un Bonus ; sans scatter dans ce jeu, ce chemin n'a pas de sens.
        On tire normalement, puis on applique les deux règles de plateau : au
        plus un Wild principal, et un Wild obligatoire en Bonus.
        """
        if self.forced_boards:
            self.set_board_from_names(self.forced_boards.pop(0))
        else:
            self.create_board_reelstrips()

        self.keep_wild_out_of_padding()
        self.place_carried_wild()
        self.enforce_single_main_wild()
        self.guarantee_wild()
        self.sync_wild_state()

        if emit_event:
            reveal_event(self)

    def set_board_from_names(self, board_names: list) -> None:
        """Plateau imposé, en noms de symboles `[reel][row]`.

        Uniquement pour les tests déterministes et les books canoniques : elle
        n'est jamais utilisée par une simulation. Les bandes et positions
        d'arrêt restent renseignées pour que le tumble suivant fonctionne
        normalement.
        """
        self.refresh_special_syms()
        self.reelstrip_id = "BR0" if self.gametype == self.config.basegame_type else "FR0"
        self.reelstrip = self.config.reels[self.reelstrip_id]

        self.board = [
            [self.create_symbol(name) for name in board_names[reel]] for reel in range(self.config.num_reels)
        ]
        self.reel_positions = [0] * self.config.num_reels
        self.padding_position = [0] * self.config.num_reels
        self.anticipation = [0] * self.config.num_reels
        # Padding volontairement non-Wild : un tumble promeut le symbole du haut
        # dans le plateau visible, ce qui ajouterait un Wild non demandé.
        padding = [
            next(str(name) for name in self.reelstrip[reel] if str(name) != "W")
            for reel in range(self.config.num_reels)
        ]
        self.top_symbols = [self.create_symbol(name) for name in padding]
        self.bottom_symbols = [self.create_symbol(name) for name in padding]
        self.get_special_symbols_on_board()

    # ── Déclenchement du Bonus ──────────────────────────────────────────────

    def check_fs_condition(self, scatter_key: str = "wild") -> bool:
        """Le Bonus part sur `bonus_pending`, pas sur un compte de scatters."""
        if self.repeat:
            return False
        if self.bonus_pending:
            return True
        if self.gametype == self.config.basegame_type:
            # Mode d'entrée directe : la distribution impose le Bonus.
            return bool(self.get_current_distribution_conditions().get("force_freegame"))
        return False

    def check_freespin_entry(self, scatter_key: str = "wild") -> bool:
        """Rien à valider : le Base Game a le droit de déclencher le Bonus."""
        return True

    def run_freespin_from_base(self, scatter_key: str = "wild") -> None:
        """Enregistre le déclenchement puis lance le Bonus."""
        self.record(
            {
                "kind": WILD_MAX_CHARGE,
                "symbol": "wild",
                "gametype": self.gametype,
            }
        )
        self.update_freespin_amount()
        self.run_freespin()

    # ── Population d'optimisation ───────────────────────────────────────────

    def bonus_bucket(self) -> str:
        """Bucket du round, d'apres son payout TOTAL.

        CONVENTION : intervalles fermes a gauche, ouverts a droite. Un round
        appartient donc a exactement un bucket, et tout round Bonus en a un.

        Le classement porte sur `final_win`, le payout TOTAL du pari — spin
        declencheur ET Free Spins additionnes. Le gain du spin declencheur n'est
        donc jamais compte deux fois : il n'existe qu'une seule valeur.

        Le plafond n'est PAS un bucket : un round a `wincap` est saisi par sa
        propre fence, definie sur un payout exact. Le renvoyer ici en `mega`
        serait sans effet — cette fence est traitee avant — mais brouillerait la
        lecture, donc on le nomme.
        """
        if self.final_win >= self.config.wincap:
            return "wincap"
        for name, (low, high) in BONUS_BUCKET_BOUNDS.items():
            if low <= self.final_win < high:
                return name
        raise AssertionError(f"payout non classable : {self.final_win}")

    def record_optimization_criteria(self) -> None:
        """Inscrit la categorie du round au force record.

        C'est le mecanisme OFFICIEL de segmentation : `record()` alimente le
        force record, que l'optimizer interroge via `search_conditions={cle:
        valeur}`. Aucun systeme de ponderation parallele n'est cree.

        Sans cela, tous les Books Bonus forment une seule population et
        l'optimizer est libre d'en detruire la forme interne — c'est exactement
        ce qui a fait rejeter le premier candidat.

        Rien n'est enregistre pour les rounds sans Bonus : ils sont saisis par
        les fences `0` (payout exact 0) et `basegame` (attrape-tout).
        """
        if not self.triggered_freegame:
            return
        # `retrigger` est une SECONDE dimension, independante du bucket. Dans ce
        # jeu, un Bonus n'atteint les paliers eleves qu'en retriggant : sans
        # cette cle, viser une frequence de retrigger revient a viser une forme
        # de Bonus, et les deux cibles se contredisent. Mesure sur 100 000
        # Books — part des Bonus AVEC retrigger : low 2.93 %, medium 42.66 %,
        # high 73.28 %, mega 92.27 %.
        #
        # Ajouter une cle ne casse rien : le Rust exige que les cles CHERCHEES
        # figurent dans l'enregistrement, pas l'inverse. Une fence qui ne
        # demande que `bucket` continue donc de matcher.
        self.record(
            {
                "criteria": "freegame",
                "bucket": self.bonus_bucket(),
                "retrigger": "yes" if self.retriggered_freegame() else "no",
            }
        )

    def retriggered_freegame(self) -> bool:
        """Le Bonus a-t-il ete prolonge ?

        Se lit sur les events du Book, pas sur un compteur parallele : c'est la
        meme source que celle que le frontend rejoue.
        """
        return any(event.get("type") == "freeSpinRetrigger" for event in self.book.events)

    def check_repeat(self) -> None:
        """Rejoue le pari s'il ne satisfait pas la criteria de la distribution."""
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

            if self.get_current_distribution_conditions()["force_freegame"] and not (self.triggered_freegame):
                self.repeat = True

        self.repeat_count += 1
        self.check_current_repeat_count()

    # ── Forçage déterministe ────────────────────────────────────────────────

    def force(self, boards: list = None, features: list = None, seed: int = 0) -> None:
        """Prépare un spin entièrement déterministe.

        `boards` est consommé un plateau par tirage, `features` une feature par
        dead spin. Outil de test et de génération de books : aucune simulation
        n'y touche.
        """
        random.seed(seed)
        self.forced_boards = list(boards) if boards else []
        self.forced_features = list(features) if features else []
