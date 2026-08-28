"""Boucle de jeu de PLANT VS WILD."""

from game_events import update_grid_event
from game_override import GameStateOverride


class GameState(GameStateOverride):
    """Déroulé d'une simulation."""

    def resolve_spin(self) -> None:
        """Résolution complète d'un plateau : connexions, Wild, cascades.

        L'ordre des events par cascade est celui que le frontend rejoue déjà :

            winInfo -> updateTumbleWin -> updateGrid -> wildMove -> tumbleBoard

        Le déplacement du Wild vient bien APRÈS la résolution de la connexion et
        AVANT le refill : c'est ce qui garantit qu'il n'est jamais détruit.
        """
        self.get_clusters_update_wins()
        self.emit_tumble_win_events()
        self.update_grid_mults()
        if not self.wincap_triggered:
            self.handle_wild_connection()

        cascades = 0
        maximum = self.config.max_cascades_per_spin

        while self.win_data["totalWin"] > 0 and not self.wincap_triggered:
            # Plafond de cascades : la résolution qui précède a été payée et ses
            # multiplicateurs appliqués. On refuse seulement d'en engager une
            # nouvelle. Aucun gain n'est retiré, aucun symbole n'est modifié.
            if maximum is not None and cascades >= maximum:
                self.cascade_cap_reached = True
                break

            self.tumble_game_board()
            cascades += 1
            self.get_clusters_update_wins()
            self.emit_tumble_win_events()
            self.update_grid_mults()
            # Plafond atteint : plus aucun refill ne suivra, déplacer le Wild
            # annoncerait un mouvement que la cascade ne conclut jamais.
            if not self.wincap_triggered:
                self.handle_wild_connection()

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim if simulation_seed is None else simulation_seed)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board()
            update_grid_event(self)

            self.resolve_spin()

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            # Le Bonus n'est annoncé qu'ici : la 4e connexion pose seulement
            # `bonus_pending`, les cascades vont jusqu'au bout.
            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        # Hors de la boucle : `final_win` est celui du round ACCEPTE, et
        # `reset_book` a efface les enregistrements des tentatives rejetees.
        self.record_optimization_criteria()
        self.imprint_wins()

    def run_freespin(self):
        self.reset_fs_spin()
        while self.fs < self.tot_fs:
            self.update_freespin()
            self.reset_spin_state()
            self.draw_board()
            # La grille est celle héritée du spin déclencheur, puis celle
            # accumulée par les Free Spins précédents : jamais remise à zéro.
            update_grid_event(self)

            self.resolve_spin()

            # Une seule feature par dead spin, et seulement si le spin n'a rien
            # rapporté. La résolution normale reprend ensuite.
            if self.trigger_dead_spin_feature():
                self.resolve_spin()

            self.expire_temporary_wilds()
            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

        self.end_freespin()
