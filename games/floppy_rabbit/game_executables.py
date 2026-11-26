"""Footprints and the rabbit's two actions, Hop and Flop."""

import random

from game_calculations import GameCalculations
from game_events import rabbits_enter_event, rabbit_hop_event, rabbit_flop_event
from src.calculations.cluster import Cluster
from src.events.events import update_freespin_event


class GameExecutables(GameCalculations):
    """Game specific executable functions."""

    def reset_footprints(self):
        """Clear every footprint and take the rabbits off the board."""
        self.footprints = [[0 for _ in range(self.config.num_rows[reel])] for reel in range(self.config.num_reels)]
        self.rabbits = []

    def all_cells(self) -> list:
        return [(reel, row) for reel in range(self.config.num_reels) for row in range(self.config.num_rows[reel])]

    def step_up(self, cell: tuple):
        """A footprint appears at 2x, or doubles up to the cap."""
        reel, row = cell
        value = self.footprints[reel][row]
        self.footprints[reel][row] = 2 if value == 0 else min(value * 2, self.config.footprint_cap)

    def hop_targets(self, rabbit: int) -> list:
        """Cells within hopping reach of a rabbit, other than its own and those other rabbits sit on."""
        reel, row = self.rabbits[rabbit]
        reach = self.config.hop_reach
        return [
            (r, c)
            for r, c in self.all_cells()
            if max(abs(r - reel), abs(c - row)) <= reach and (r, c) not in self.rabbits
        ]

    def hop(self, rabbit: int, target: tuple = None):
        start = self.rabbits[rabbit] if rabbit < len(self.rabbits) else None
        if target is None:
            target = random.choice(self.hop_targets(rabbit))
        if start is None:
            self.rabbits.append(target)
        else:
            self.rabbits[rabbit] = target
        self.step_up(target)
        self.hop_count += 1
        rabbit_hop_event(self, rabbit, start, target)

    def flop(self, rabbit: int):
        """Every footprint on the board doubles."""
        cap = self.config.footprint_cap
        for reel, row in self.all_cells():
            value = self.footprints[reel][row]
            if value:
                self.footprints[reel][row] = min(value * 2, cap)
        self.flop_count += 1
        rabbit_flop_event(self, rabbit, self.rabbits[rabbit])

    def reveal_hop(self):
        """Base game: when the board is revealed the rabbit hops once, to any cell."""
        self.rabbits = []
        self.hop(0, random.choice(self.all_cells()))

    def flop_chance(self) -> float:
        if self.gametype == self.config.freegame_type:
            return self.config.fs_flop[len(self.rabbits)]
        return self.config.base_flop

    def rabbits_act(self, allow_flop: bool, sure_flop: bool = False):
        """Every rabbit takes one action: it flops where it is, or hops within reach.

        With sure_flop the first rabbit's action is a flop.
        """
        chance = self.flop_chance() if allow_flop else 0.0
        for rabbit in range(len(self.rabbits)):
            if (sure_flop and rabbit == 0) or random.random() < chance:
                self.flop(rabbit)
            else:
                self.hop(rabbit)

    def rabbits_for(self, scatters: int) -> int:
        """Three scatters bring one rabbit, four bring two, five or more bring three."""
        return max(count for need, count in self.config.rabbits_by_scatters.items() if scatters >= need)

    def enter_rabbits(self):
        """Flop Time starts on a clear board: each rabbit takes a random cell and marks it 2x."""
        self.rabbits = random.sample(self.all_cells(), self.rabbits_for(self.trigger_scatters))
        for cell in self.rabbits:
            self.step_up(cell)
        rabbits_enter_event(self)

    def run_freespin_from_base(self, scatter_key: str = "scatter") -> None:
        """Remember how many scatters triggered: they decide how many rabbits come."""
        self.trigger_scatters = self.count_special_symbols(scatter_key)
        super().run_freespin_from_base(scatter_key)

    def get_clusters_update_wins(self):
        """Evaluate the board through the footprints and update the wallet."""
        self.win_data = self.evaluate_clusters_with_footprints()
        Cluster.record_cluster_wins(self)
        self.win_manager.tumble_win = self.win_data["totalWin"]
        self.win_manager.update_spinwin(self.win_data["totalWin"])

    def update_freespin(self) -> None:
        """Called before a new reveal during free spins. Footprints and rabbits persist."""
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.win_data = {}
