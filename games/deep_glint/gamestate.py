from game_override import GameStateOverride
from game_events import update_glint_event


class GameState(GameStateOverride):
    """Gamestate for a single round."""

    def run_spin(self, sim: int, simulation_seed=None):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board()
            self.glint_strike()
            self.run_tumbles()

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self):
        self.reset_fs_spin()
        self.apply_fs_start_glint()
        update_glint_event(self)
        if self.config.fs_start_strike is not None:
            self.strike_spots(self.config.fs_start_strike)
        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.update_freespin()
            self.draw_board()
            self.run_tumbles()

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

        self.end_freespin()

    def run_tumbles(self):
        """Evaluate, light the spots under the wins, and tumble until the board stops paying."""
        self.get_scatterpays_update_wins()
        self.emit_tumble_win_events()
        self.update_glint_spots()
        while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
            self.tumble_game_board()
            self.get_scatterpays_update_wins()
            self.emit_tumble_win_events()
            self.update_glint_spots()
