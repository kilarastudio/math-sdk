"""Glint Spot, Glint Strike and Dragon's Gaze actions for Pratala."""

import random

from game_calculations import GameCalculations
from game_events import update_glint_event, glint_strike_event, glint_gaze_event
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

    def run_freespin_from_base(self, scatter_key: str = "scatter") -> None:
        """Remember how many eyes triggered: the free spins start hotter with six or more."""
        self.trigger_eyes = self.count_special_symbols(scatter_key)
        super().run_freespin_from_base(scatter_key)

    def apply_fs_start_glint(self):
        """Light every spot at the start of free spins when the trigger or the mode asks for it.

        Six or more triggering eyes light the whole floor (config.fs_trigger_glint); super and
        hoard start with a lit floor of their own. The brighter of the two applies.
        """
        value = 0
        for eyes, floor in self.config.fs_trigger_glint.items():
            if self.trigger_eyes >= eyes:
                value = max(value, floor)
        start = self.get_current_distribution_conditions()["fs_start_glint"]
        if start is not None:
            value = max(value, start)
        if value:
            for pos in self.all_positions():
                self.glint[pos["reel"]][pos["row"]] = value

    def update_glint_spots(self):
        """Heat the spot under every winning symbol: unlit -> primed -> 2x -> doubles up to the explosion cap.

        Explosions stop at glint_rule["explode_cap"]; only the dragon's gaze takes a spot further.
        """
        if self.win_data["totalWin"] <= 0:
            return
        explode_cap = self.config.glint_rule["explode_cap"]
        exploded = {(p["reel"], p["row"]) for win in self.win_data["wins"] for p in win["positions"]}
        for reel, row in exploded:
            value = self.glint[reel][row]
            if value == 0:
                self.glint[reel][row] = 1
            elif value == 1:
                self.glint[reel][row] = 2
            elif value < explode_cap:
                self.glint[reel][row] = min(value * 2, explode_cap)
        update_glint_event(self)

    def dragon_gaze(self, eyes: list, reels: list):
        """Double every spot on each listed reel (an unlit or primed spot lights at 2x), up to the cap."""
        if not reels:
            return
        cap = self.config.glint_rule["cap"]
        for reel in reels:
            for row in range(self.config.num_rows[reel]):
                value = self.glint[reel][row]
                self.glint[reel][row] = 2 if value < 2 else min(value * 2, cap)
        self.gaze_count += len(reels)
        glint_gaze_event(self, eyes, reels)

    def gaze_from_board(self):
        """Free spins: every eye on the revealed board gazes down its reel before the board is evaluated."""
        eyes = [dict(pos) for pos in self.special_syms_on_board["scatter"]]
        self.dragon_gaze(eyes, [e["reel"] for e in eyes])

    def exploding_per_reel(self) -> list:
        """How many symbols each reel is about to lose, so the symbols that replace them can be found."""
        counts = [0] * self.config.num_reels
        for reel, row in {(p["reel"], p["row"]) for win in self.win_data["wins"] for p in win["positions"]}:
            counts[reel] += 1
        return counts

    def gaze_from_tumble(self, landed: list):
        """Free spins: an eye that drops in with a tumble gazes too, before the next evaluation."""
        eyes = [
            {"reel": reel, "row": row}
            for reel, count in enumerate(landed)
            for row in range(count)
            if self.board[reel][row].name in self.config.special_symbols["scatter"]
        ]
        self.dragon_gaze(eyes, [e["reel"] for e in eyes])

    def sweep_gaze(self):
        """Hoard: before every free spin the gaze sweeps on to the next reel, left to right."""
        if not self.get_current_distribution_conditions()["fs_sweep"]:
            return
        self.dragon_gaze([], [(self.fs - 1) % self.config.num_reels])

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
