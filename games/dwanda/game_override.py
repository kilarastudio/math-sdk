from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Extend the universal state with the territory."""

    quiet = False

    def reset_book(self):
        super().reset_book()
        self.tumble_win = 0
        self.cascade_count = 0
        self.clashes_made = 0
        self.trigger_scatters = 0
        self.reset_territory()

    def reset_fs_spin(self):
        super().reset_fs_spin()
        # The Duel starts on an empty territory and keeps it until it ends.
        self.reset_territory()

    def assign_special_sym_function(self):
        self.special_symbol_functions = {}

    def check_repeat(self) -> None:
        if self.repeat is False:
            conditions = self.get_current_distribution_conditions()
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
            if conditions["force_freegame"] and not self.triggered_freegame:
                self.repeat = True
            exact = conditions.get("exact_scatters")
            if exact is not None and self.trigger_scatters != exact:
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
