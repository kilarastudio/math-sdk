from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Extend the universal state with the auction board."""

    def reset_book(self):
        super().reset_book()
        self.setup_sets()
        self.lots = {}
        self.gavels = 0
        self.buyers = 0
        self.respins_played = 0
        self.full_house = False

    # Measurement without books (run.py --natural / --feature): no events, and with `unforced`
    # the opening board is the reels as they fall.
    quiet = False
    unforced = False

    def assign_special_sym_function(self):
        self.special_symbol_functions = {"P": [self.assign_lot]}

    def check_repeat(self) -> None:
        if self.repeat is False:
            conditions = self.get_current_distribution_conditions()
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
            if conditions["force_freegame"] and not self.triggered_freegame:
                self.repeat = True
            if self.win_manager.running_bet_win == 0 and self.criteria != "0":
                self.repeat = True
            min_win = conditions.get("min_win")
            if min_win is not None and not self.repeat:
                self.tail_attempts += 1
                if self.final_win < min_win:
                    self.repeat = True
        self.repeat_count += 1
        self.check_current_repeat_count()
