from game_override import GameStateOverride


class GameState(GameStateOverride):
    """Gamestate for a single round."""

    def run_spin(self, sim: int, simulation_seed=None):
        self.reset_seed(sim)
        self.tail_attempts = 0
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.play_board()
            self.win_manager.update_gametype_wins(self.gametype)
            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()
            self.evaluate_finalwin()
            self.check_repeat()
        if self.tail_attempts:
            self.record({"tail_attempts": self.tail_attempts})
        self.imprint_wins()

    def run_freespin(self):
        self.reset_fs_spin()
        self.start_crew()
        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.update_freespin()
            self.play_board()
            self.win_manager.update_gametype_wins(self.gametype)
            self.retrigger()
        self.end_freespin()

    # Measurement without books (run.py --natural / --feature): the same play_board, events off.
    def run_natural_spin(self) -> tuple:
        self.reset_book()
        self.quiet = True
        self.play_board(emit=False)
        return self.win_data["totalWin"], self.count_special_symbols("scatter")

    def run_natural_feature(self, mode: str, scatters: int = 3) -> dict:
        self.reset_book()
        self.quiet = True
        self.betmode = mode
        self.tot_fs = self.config.fs_by_scatters[scatters]
        self.reset_fs_spin()
        self.start_crew()
        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.fs += 1
            self.win_manager.reset_spin_win()
            self.play_board(emit=False)
            self.retrigger(emit=False)
        top = max([m for (name, m) in self.sticky.values() if name == "WC"], default=0)
        return {
            "win": self.win_manager.running_bet_win,
            "spins": self.fs,
            "wc": self.crew_landed["WC"],
            "wd": self.crew_landed["WD"],
            "top": top,
            "upgrades": self.upgrades,
        }
