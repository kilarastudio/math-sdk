"""Glint Spot and Glint Strike actions for DEEP GLINT."""

import random

from game_calculations import GameCalculations
from game_events import update_glint_event, glint_strike_event
from src.calculations.scatter import Scatter
from src.calculations.statistics import get_random_outcome
from src.events.events import update_freespin_event


class GameExecutables(GameCalculations):
    """Game specific executable functions."""

    def reset_glint(self):
        """Clear every Glint Spot."""
        self.glint = [[0 for _ in range(self.config.num_rows[reel])] for reel in range(self.config.num_reels)]

    def all_positions(self) -> list:
        return [
            {"reel": reel, "row": row}
            for reel in range(self.config.num_reels)
            for row in range(self.config.num_rows[reel])
        ]

    def glint_strike(self):
        """Maybe let the character light a few spots before the base board is evaluated."""
        strike = self.get_current_distribution_conditions()["strike"]
        if random.random() >= strike["prob"]:
            return
        self.strike_spots(strike)

    def strike_spots(self, shape: dict):
        """Light `count` random spots at the drawn values; a spot already brighter keeps its value."""
        count = get_random_outcome(shape["count"])
        spots = []
        for pos in random.sample(self.all_positions(), count):
            value = max(get_random_outcome(shape["value"]), self.glint[pos["reel"]][pos["row"]])
            self.glint[pos["reel"]][pos["row"]] = value
            spots.append({**pos, "value": value})
        self.strike_count += 1
        glint_strike_event(self, spots)

    def apply_fs_start_glint(self):
        """Light spots at the start of free spins when the mode asks for it (super)."""
        start = self.get_current_distribution_conditions()["fs_start_glint"]
        if start is None:
            return
        for pos in random.sample(self.all_positions(), start["count"]):
            self.glint[pos["reel"]][pos["row"]] = start["value"]

    def update_glint_spots(self):
        """Upgrade the spot under every winning symbol: unlit -> primed -> 2x -> grows up to the cap."""
        if self.win_data["totalWin"] <= 0:
            return
        exploded = {(p["reel"], p["row"]) for win in self.win_data["wins"] for p in win["positions"]}
        for reel, row in exploded:
            value = self.glint[reel][row]
            if value == 0:
                self.glint[reel][row] = 1
            elif value == 1:
                self.glint[reel][row] = 2
            else:
                grown = value * 2 if self.config.glint_rule["growth"] == "double" else value + 1
                self.glint[reel][row] = min(grown, self.config.glint_rule["cap"])
        update_glint_event(self)

    def get_scatterpays_update_wins(self):
        """Evaluate the board through the Glint Spots and update the wallet."""
        self.win_data = self.evaluate_scatter_with_glint()
        Scatter.record_scatter_wins(self)
        self.win_manager.tumble_win = self.win_data["totalWin"]
        self.win_manager.update_spinwin(self.win_data["totalWin"])

    def update_freespin(self) -> None:
        """Called before a new reveal during free spins. Spots persist between spins."""
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.win_data = {}
