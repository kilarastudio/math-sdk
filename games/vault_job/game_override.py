from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Extend the universal state with the sticky crew of The Job."""

    def reset_book(self):
        super().reset_book()
        self.setup_sets()
        self.quiet = False
        self.sticky = {}
        self.upgrades = 0
        self.crew_landed = {"WD": 0, "WC": 0}

    def reset_fs_spin(self):
        super().reset_fs_spin()
        self.sticky = {}

    def assign_special_sym_function(self):
        self.special_symbol_functions = {}

    def check_repeat(self) -> None:
        """Accept a book only when it matches its distribution's criteria."""
        if self.repeat is False:
            conditions = self.get_current_distribution_conditions()
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True
            if conditions["force_freegame"] and not self.triggered_freegame:
                self.repeat = True
            if self.win_manager.running_bet_win == 0 and self.criteria != "0":
                self.repeat = True
            # Tail books start at min_win; count the rounds tried for each one kept (game_weights.py).
            min_win = conditions.get("min_win")
            if min_win is not None and not self.repeat:
                self.tail_attempts += 1
                if self.final_win < min_win:
                    self.repeat = True
        self.repeat_count += 1
        self.check_current_repeat_count()
