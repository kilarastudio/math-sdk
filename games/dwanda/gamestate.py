from game_override import GameStateOverride


class GameState(GameStateOverride):
    """Gamestate for a single round."""

    def run_spin(self, sim: int, simulation_seed=None):
        self.reset_seed(sim)
        self.tail_attempts = 0
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board()
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

    def run_freespin_from_base(self, scatter_key: str = "scatter") -> None:
        self.trigger_scatters = self.count_special_symbols(scatter_key)
        super().run_freespin_from_base(scatter_key)

    def run_freespin(self):
        self.reset_fs_spin()
        self.start_clash()
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
        """Evaluate, mark the territory, tumble; until the board stops paying."""
        self.get_clusters_update_wins()
        self.emit_tumble_win_events()
        while self.win_data["totalWin"] > 0 and not self.wincap_triggered:
            self.mark_territory()
            self.tumble_game_board()
            self.cascade_count += 1
            self.get_clusters_update_wins()
            self.emit_tumble_win_events()

    # Measurement without books (run.py --natural / --feature).
    def run_natural_spin(self) -> tuple:
        self.quiet = True
        self.reset_book()
        self.create_board_reelstrips()
        self.run_tumbles()
        return self.win_manager.running_bet_win, self.count_special_symbols("scatter")

    def run_natural_feature(self, scatters: int, mode: str) -> dict:
        self.quiet = True
        self.betmode = mode
        self.reset_book()
        self.trigger_scatters = scatters
        self.tot_fs = self.config.fs_by_scatters[scatters]
        self.reset_fs_spin()
        self.start_clash()
        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.fs += 1
            self.win_manager.reset_spin_win()
            self.create_board_reelstrips()
            self.run_tumbles()
            if self.count_special_symbols("scatter") >= 3:
                self.tot_fs += self.config.fs_retrigger
        cells = [v for col in self.clash for v in col if v]
        return {
            "win": self.win_manager.running_bet_win,
            "spins": self.fs,
            "clashes": self.clashes_made,
            "top": max(cells, default=0),
            "cells": len(cells),
            "cascades": self.cascade_count,
        }
