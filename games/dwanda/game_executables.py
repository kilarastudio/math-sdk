"""Territory: phoenix and dragon marks, and the Clash cells where they meet."""

import random

from game_calculations import GameCalculations
from game_events import territory_event
from src.calculations.cluster import Cluster
from src.events.events import update_freespin_event

NONE, PHOENIX, DRAGON, CLASH = 0, 1, 2, 3
SIDE = {"P": PHOENIX, "D": DRAGON}


class GameExecutables(GameCalculations):
    """Game specific executable functions."""

    def reset_territory(self):
        self.marks = [[NONE] * self.config.num_rows[reel] for reel in range(self.config.num_reels)]
        self.clash = [[0] * self.config.num_rows[reel] for reel in range(self.config.num_reels)]

    def mark_territory(self):
        """Every winning cluster marks its cells for its side; where sides meet, Clash cells grow."""
        cap = self.config.clash_cap
        changed = False
        spread = self.gametype == self.config.freegame_type and self.config.duel_spread
        for win in self.win_data["wins"]:
            side = SIDE[self.config.side[win["symbol"]]]
            cells = {(p["reel"], p["row"]) for p in win["positions"]}
            if spread:
                # In the Duel the mark also spreads to the cells next to the cluster (not doubling Clash cells there).
                edge = {
                    (r + dr, c + dc)
                    for r, c in cells
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= r + dr < self.config.num_reels and 0 <= c + dc < self.config.num_rows[r + dr]
                } - cells
                for reel, row in edge:
                    mark = self.marks[reel][row]
                    if mark == NONE:
                        self.marks[reel][row] = side
                        changed = True
                    elif mark != side and mark != CLASH:
                        self.marks[reel][row] = CLASH
                        self.clash[reel][row] = self.config.clash_start
                        self.clashes_made += 1
                        changed = True
            for reel, row in cells:
                mark = self.marks[reel][row]
                if mark == NONE:
                    self.marks[reel][row] = side
                    changed = True
                elif mark == CLASH:
                    if self.clash[reel][row] < cap:
                        self.clash[reel][row] = min(self.clash[reel][row] * 2, cap)
                        changed = True
                elif mark != side:
                    self.marks[reel][row] = CLASH
                    self.clash[reel][row] = self.config.clash_start
                    self.clashes_made += 1
                    changed = True
        if changed:
            territory_event(self, "marked")

    def start_clash(self):
        """A bought Duel can start with Clash cells on random cells."""
        count, value = self.config.buy_start_clash.get(self.betmode, (0, 0))
        if count:
            cells = [(r, c) for r in range(self.config.num_reels) for c in range(self.config.num_rows[r])]
            for reel, row in random.sample(cells, count):
                self.marks[reel][row] = CLASH
                self.clash[reel][row] = value
            territory_event(self, "start")

    def get_clusters_update_wins(self):
        self.win_data = self.evaluate_clusters_with_clash()
        Cluster.record_cluster_wins(self)
        self.win_manager.tumble_win = self.win_data["totalWin"]
        self.win_manager.update_spinwin(self.win_data["totalWin"])

    def update_freespin(self) -> None:
        """Called before a new reveal during the Duel. The territory stays."""
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.win_data = {}
