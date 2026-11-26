"""Kilara Keno (working id): 40-number keno with a streak multiplier.

Every mode is one (level, picks) pair: Low and High with 2 to 10 picks, Chain and Chain Max with 10. The design and its measurements are in MATH.md.
"""

from src.config.config import Config
from src.config.distributions import Distribution
from src.config.config import BetMode


class GameConfig(Config):
    def __init__(self):
        super().__init__()
        self.game_id = "kilara_keno"
        self.provider_numer = 0
        self.working_name = "Kilara Keno"
        self.wincap = 100000
        self.win_type = "other"
        self.rtp = 0.967
        self.construct_paths()

        self.num_reels = 0
        self.num_rows = [0] * self.num_reels
        self.paytable = {}
        self.include_padding = False
        self.special_symbols = {"wild": [], "scatter": [], "multiplier": []}
        self.freespin_triggers = {self.basegame_type: {}, self.freegame_type: {}}
        self.anticipation_triggers = {self.basegame_type: 0, self.freegame_type: 0}

        # Board and draw
        self.board_numbers = 40
        self.num_draws = 10
        self.levels = ["low", "high", "chain", "chainmax"]
        self.level_draws = {"low": 10, "high": 10, "chain": 12, "chainmax": 12}
        self.level_picks = {"low": list(range(2, 11)), "high": list(range(2, 11)), "chain": [10], "chainmax": [10]}
        self.level_cost = {"low": 1.0, "high": 1.0, "chain": 10.0, "chainmax": 100.0}
        # Kilau numbers: marked numbers the player did not pick. Each one drawn adds a meter step.
        self.level_kilau = {"low": 1, "high": 1, "chain": 1, "chainmax": 3}
        # Levels where a miss lowers the run by one instead of ending it.
        self.soft_levels = {"chain", "chainmax"}

        # Meter level (best run of hits + Kilau balls drawn) -> multiplier on the whole win.
        self.top_streak = 7
        self.streak_multiplier = {0: 1, 1: 1, 2: 2, 3: 3, 4: 5, 5: 10, 6: 15, 7: 25}

        # pay_tables[level][picks][hits], in base bets, before the multiplier.
        # Found with design_tables.py.
        self.pay_tables = {
            "low": {
                2: [0, 1, 6],
                3: [0, 1, 1.2, 8.4],
                4: [0, 0.3, 1.5, 3.6, 15],
                5: [0, 0.2, 1, 1.5, 8, 50],
                6: [0, 0, 0.8, 1.5, 3, 10, 40],
                7: [0, 0, 0.6, 1, 2, 5, 15, 40],
                8: [0, 0, 0.3, 0.8, 1.5, 4, 6, 12, 20],
                9: [0, 0, 0.3, 0.5, 1, 2.5, 6, 8, 20, 20],
                10: [0, 0, 0, 0.5, 0.8, 1.5, 5, 7.5, 10, 20, 20],
            },
            "high": {
                2: [0, 0.4, 9.5],
                3: [0, 0, 1, 35],
                4: [0, 0, 0.5, 7.5, 50],
                5: [0, 0, 0.4, 2, 9, 250],
                6: [0, 0, 0.2, 1, 5, 35, 500],
                7: [0, 0, 0, 0.6, 3, 12, 100, 1000],
                8: [0, 0, 0, 0.3, 1.2, 5, 44, 400, 2000],
                9: [0, 0, 0, 0.2, 0.8, 2.3, 15, 100, 1500, 1500],
                10: [0, 0, 0, 0, 0.5, 1.2, 5, 60, 600, 2000, 2000],
            },
            "chain": {10: [0, 0, 2, 3, 5, 5, 10, 25, 500, 2000, 2000]},
            "chainmax": {10: [0, 0, 10, 25, 40, 40, 75, 300, 1500, 4000, 4000]},
        }

        # Every draw pattern is published this many times over, each copy with its own numbers,
        # so that a mode holds at least this many distinct rounds.
        self.min_books = 100_000

        self.bet_modes = []
        for level in self.levels:
            for picks in self.level_picks[level]:
                table = self.pay_tables[level][picks]
                top = self.streak_multiplier[min(picks + self.level_kilau[level], self.top_streak)]
                self.bet_modes.append(
                    BetMode(
                        name=f"{level}_{picks}",
                        cost=self.level_cost[level],
                        rtp=self.rtp,
                        max_win=round(min(self.wincap, max(table) * top), 2),
                        auto_close_disabled=False,
                        is_feature=True,
                        is_buybonus=False,
                        distributions=[
                            Distribution(
                                criteria="basegame",
                                quota=1.0,
                                conditions={"reel_weights": {}, "force_wincap": False, "force_freegame": False},
                            ),
                        ],
                    )
                )

    def mode_parts(self, mode: str) -> tuple:
        """(level, picks, draws, kilau numbers) of a mode name such as "high_8"."""
        level, picks = mode.rsplit("_", 1)
        return level, int(picks), self.level_draws[level], self.level_kilau[level]
