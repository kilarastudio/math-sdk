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
            self.reveal_hop()
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
        to be set; it writes no book.
        """
        self.reset_book()
        self.create_board_reelstrips()
        self.reveal_hop()
        self.run_tumbles()
        return self.win_manager.running_bet_win, self.count_special_symbols("scatter")

    def run_natural_feature(self, scatters: int) -> dict:
        """One unconditioned Flop Time session as `scatters` would trigger it (run.py --feature)."""
        self.reset_book()
        self.trigger_scatters = scatters
        self.tot_fs = self.config.freespin_triggers[self.config.basegame_type][scatters]
        self.run_freespin()
        return {
            "win": self.win_manager.running_bet_win,
            "hops": self.hop_count,
            "flops": self.flop_count,
            "spins": self.fs,
            "top": max(max(reel) for reel in self.footprints),
            "cells": sum(1 for reel in self.footprints for value in reel if value),
        }

    def run_freespin(self):
        self.reset_fs_spin()
        self.enter_rabbits()
        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.update_freespin()
            self.draw_board()
            self.rabbits_act(allow_flop=True, sure_flop=self.fs in self.config.fs_sure_flop_spins)
            self.run_tumbles()

            self.set_end_tumble_event()
            self.win_manager.update_gametype_wins(self.gametype)

            if self.check_fs_condition():
                self.update_fs_retrigger_amt()

        self.end_freespin()

    def run_tumbles(self):
        """Evaluate and tumble until the board stops paying; the rabbits act after every winning cascade."""
        in_free_spins = self.gametype == self.config.freegame_type
        flop_from = self.config.base_flop_from_cascade
        cascade = 0
        self.get_clusters_update_wins()
        self.emit_tumble_win_events()
        while self.win_data["totalWin"] > 0 and not (self.wincap_triggered):
            self.tumble_game_board()
            cascade += 1
            self.cascade_count += 1
            self.rabbits_act(allow_flop=in_free_spins or cascade >= flop_from)
            self.get_clusters_update_wins()
            self.emit_tumble_win_events()
