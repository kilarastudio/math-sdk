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
            if self.auction_triggered():
                if self.get_current_distribution_conditions()["force_freegame"]:
                    self.run_auction()
                else:
                    self.repeat = True
            self.evaluate_finalwin()
            self.check_repeat()
        if self.tail_attempts:
            self.record({"tail_attempts": self.tail_attempts})
        self.imprint_wins()

    def run_freespin(self):
        self.run_auction()

    # Measurement without books (run.py --natural / --feature).
    def run_natural_spin(self) -> tuple:
        self.quiet, self.unforced = True, True
        self.reset_book()
        self.play_board()
        return self.win_data["totalWin"], len(self.lots_on_board())

    def run_natural_feature(self, mode: str) -> dict:
        """One auction as `mode` starts it ("base": an unforced board with 6+ lots)."""
        self.quiet = True
        self.unforced = mode == "base"
        self.betmode = mode
        self.reset_book()
        self.draw_base_board()
        while mode == "base" and not self.auction_triggered():
            self.draw_base_board()
        self.run_auction()
        return {
            "win": self.win_manager.running_bet_win,
            "lots": len(self.lots),
            "gavels": self.gavels,
            "buyers": self.buyers,
            "respins": self.respins_played,
            "full": self.full_house,
            "bid": self.bid,
        }
