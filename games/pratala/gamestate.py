from game_override import GameStateOverride
from game_events import update_glint_event


class GameState(GameStateOverride):
    """Gamestate for a single round."""

    def run_spin(self, sim: int, simulation_seed=None):
        self.reset_seed(sim)
        self.tail_attempts = 0
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

        if self.tail_attempts:
            self.record({"tail_attempts": self.tail_attempts})
        self.imprint_wins()

    def run_natural_spin(self) -> tuple:
        """One unconditioned base spin, for measuring what the reels do on their own (run.py --natural).

        Returns (base win, scatters on the final board). Needs a betmode and a base game criteria
        to be set; it uses their strike setting and writes no book.
        """
        self.reset_book()
        self.create_board_reelstrips()
        self.glint_strike()
        self.run_tumbles()
        return self.win_manager.running_bet_win, self.count_special_symbols("scatter")

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
