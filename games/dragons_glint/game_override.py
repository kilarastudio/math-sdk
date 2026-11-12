from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Extend the universal state with the Glint Spot grid."""

    def reset_book(self):
        super().reset_book()
        self.tumble_win = 0
        self.strike_count = 0
        # Spots belong to one round: the base game starts every round with a clear grid.
        self.reset_glint()

    def reset_fs_spin(self):
        super().reset_fs_spin()
        # Free spins start from a clear grid and keep it until they end.
        self.reset_glint()

    def assign_special_sym_function(self):
        self.special_symbol_functions = {}

    def check_repeat(self) -> None:
        """Accept a book only when it matches its distribution's criteria."""
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

            if self.get_current_distribution_conditions()["force_freegame"] and not (self.triggered_freegame):
                self.repeat = True

            if self.win_manager.running_bet_win == 0 and self.criteria != "0":
                self.repeat = True

            # Max-win rounds belong to the wincap category only, and tail books start at min_win.
            if self.criteria in ("freegame", "freegame_tail") and self.final_win >= self.config.wincap:
                self.repeat = True
            min_win = self.get_current_distribution_conditions().get("min_win")
            if min_win is not None and self.final_win < min_win:
                self.repeat = True

        self.repeat_count += 1
        self.check_current_repeat_count()
