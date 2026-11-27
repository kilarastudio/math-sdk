"""Kilara Keno (working id): 40-number keno with a streak multiplier.

Every mode is one (level, picks) pair: Low with 1 to 10 picks, High with 3 to 10, Chain and Chain
Max with 10. The design and its measurements are in MATH.md.
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
        # One and two numbers have one table each: at that size a second level changes little.
        self.level_picks = {"low": list(range(1, 11)), "high": list(range(3, 11)), "chain": [10], "chainmax": [10]}
        self.level_cost = {"low": 1.0, "high": 1.0, "chain": 10.0, "chainmax": 100.0}
        # Kilau numbers: marked numbers the player did not pick. Each one drawn adds a meter step.
        self.level_kilau = {"low": 1, "high": 1, "chain": 1, "chainmax": 3}
        # Kilau round: in these levels 1 round in 5 marks 3 Kilau numbers instead of 1. Chain Max
        # marks 3 in every round. The share is (rounds, out of).
        self.kilau_round_levels = {"low", "high", "chain"}
        self.kilau_round_numbers = 3
        self.kilau_round_share = (1, 5)
        # Levels where a miss lowers the run by one instead of ending it.
        self.soft_levels = {"chain", "chainmax"}

        # Meter level (best run of hits + Kilau balls drawn) -> multiplier on the whole win.
        self.top_streak = 7
        self.streak_multiplier = {0: 1, 1: 1, 2: 2, 3: 3, 4: 5, 5: 10, 6: 15, 7: 25}

        # pay_tables[level][picks][hits], in base bets, before the multiplier.
        # Found with design_tables.py.
        self.pay_tables = {
            "low": {
                1: [0, 2.9],
                2: [0, 1, 5.2],
                3: [0, 0.8, 1.5, 7.8],
                4: [0, 0.3, 1.5, 2.5, 18],
                5: [0, 0.2, 1, 1.4, 6, 50],
                6: [0, 0, 0.8, 1.2, 3, 12, 30],
                7: [0, 0, 0.6, 1, 1.5, 5, 12, 30],
                8: [0, 0, 0.2, 1, 1.2, 3, 7.5, 10, 20],
                9: [0, 0, 0.3, 0.5, 1, 2, 5, 6, 20, 20],
                10: [0, 0, 0, 0.5, 0.8, 1.2, 4.5, 7.5, 10, 20, 20],
            },
            "high": {
                3: [0, 0, 1, 32.5],
                4: [0, 0, 0.5, 7.5, 40],
                5: [0, 0, 0.3, 2, 8.4, 250],
                6: [0, 0, 0.2, 0.8, 6, 25, 500],
                7: [0, 0, 0, 0.5, 3, 11, 100, 1000],
                8: [0, 0, 0, 0.3, 1.2, 4.4, 40, 400, 2000],
                9: [0, 0, 0, 0.1, 0.8, 2.5, 12, 120, 1500, 1500],
                10: [0, 0, 0, 0, 0.5, 1.2, 5, 50, 600, 2000, 2000],
            },
            "chain": {10: [0, 0, 1.2, 2.5, 5, 5, 10, 20, 500, 2000, 2000]},
            "chainmax": {10: [0, 0, 10, 25, 40, 40, 75, 300, 1500, 4000, 4000]},
        }

        # Every round (a draw pattern and how many Kilau numbers it marks) is published this many times over, each copy with its own numbers,
        # so that a mode holds at least this many distinct rounds.
        self.min_books = 100_000

        self.bet_modes = []
        for level in self.levels:
            for picks in self.level_picks[level]:
                table = self.pay_tables[level][picks]
                most_kilau = max(kilau for kilau, _ in self.kilau_options(level))
                top = self.streak_multiplier[min(picks + most_kilau, self.top_streak)]
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

    def kilau_options(self, level: str) -> list:
        """[(Kilau numbers marked, share of the rounds as an integer weight)] of a level."""
        if level not in self.kilau_round_levels:
            return [(self.level_kilau[level], 1)]
        rounds, out_of = self.kilau_round_share
        return [(self.level_kilau[level], out_of - rounds), (self.kilau_round_numbers, rounds)]

    def mode_parts(self, mode: str) -> tuple:
        """(level, picks, draws, Kilau options) of a mode name such as "high_8"."""
        level, picks = mode.rsplit("_", 1)
        return level, int(picks), self.level_draws[level], self.kilau_options(level)
