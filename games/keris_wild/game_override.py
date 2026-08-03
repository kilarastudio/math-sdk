"""Keris-owned state resets, deterministic RNG, and criteria acceptance."""

import numpy as np

from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    def reset_seed(self, sim: int = 0, seed_override=None) -> None:
        super().reset_seed(sim, seed_override=seed_override)
        seed = sim if seed_override is None else seed_override
        self.rng = np.random.default_rng(seed)

    def reset_book(self) -> None:
        super().reset_book()
        self.sticky_reels = set()
        self.sticky_multipliers = {}
        self.respin_held_reels = set()
        self.initial_scatter = {"count": 0, "positions": [], "pay": 0.0}
        self.forced_base_stops = []
        self.forced_fs_stops = []
        self.forced_boost = None

    def assign_special_sym_function(self) -> None:
        self.special_symbol_functions = {}

    def check_repeat(self) -> None:
        if self.final_win >= self.config.wincap:
            actual_criteria = "wincap"
        elif self.final_win == 0:
            actual_criteria = "0"
        elif self.betmode == "bonus_buy" or self.triggered_freegame:
            actual_criteria = "freegame"
        else:
            actual_criteria = "basegame"
        self.repeat = actual_criteria != self.criteria
        self.repeat_count += 1
        self.check_current_repeat_count()
