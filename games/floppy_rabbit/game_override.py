from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Extend the universal state with the footprint grid and the rabbits."""

    def reset_book(self):
        super().reset_book()
        self.tumble_win = 0
        self.hop_count = 0
        self.flop_count = 0
        self.cascade_count = 0
        self.trigger_scatters = 0
        # Footprints belong to one round: the base game starts every round with a clear board.
        self.reset_footprints()

    def reset_fs_spin(self):
        super().reset_fs_spin()
        # Flop Time starts from a clear board and keeps its footprints until it ends.
        self.reset_footprints()

    def assign_special_sym_function(self):
        self.special_symbol_functions = {}

    def check_repeat(self) -> None:
        """Accept a book only when it matches its distribution's criteria."""
        if self.repeat is False:
            conditions = self.get_current_distribution_conditions()
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

            if conditions["force_freegame"] and not (self.triggered_freegame):
                self.repeat = True

            # A bought round shows exactly the scatters its mode names, so it brings exactly
            # that mode's rabbits: a board whose cascades drop another scatter in is drawn again.
            exact = conditions.get("exact_scatters")
            if exact is not None and self.trigger_scatters != exact:
                self.repeat = True

            # A round outside the "0" category always pays something.
            if self.win_manager.running_bet_win == 0 and self.criteria != "0":
                self.repeat = True

            # Tail books start at min_win. Count the rounds tried for each one that is kept:
            # kept / tried is how often the reels reach the tail (game_weights.py).
            min_win = conditions.get("min_win")
            if min_win is not None and not self.repeat:
                self.tail_attempts += 1
                if self.final_win < min_win:
                    self.repeat = True

        self.repeat_count += 1
        self.check_current_repeat_count()
