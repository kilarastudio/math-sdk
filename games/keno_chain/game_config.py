"""Keno Chain (math id keno_chain): 40-number keno with a streak multiplier.

Every mode is one (level, picks) pair: Calm, Bold and Wild with 3, 4, 5, 6, 8 or 10 picks, Chain
and Chain Max with 10. The design and its measurements are in MATH.md.
"""

from src.config.config import Config
from src.config.distributions import Distribution
from src.config.config import BetMode


class GameConfig(Config):
    def __init__(self):
        super().__init__()
        self.game_id = "keno_chain"
        self.provider_numer = 0
        self.working_name = "Keno Chain"
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
        # Calm, Bold and Wild are three volatility levels of the same draw: same odds, other tables.
        self.levels = ["calm", "bold", "wild", "chain", "chainmax"]
        self.level_draws = {"calm": 10, "bold": 10, "wild": 10, "chain": 12, "chainmax": 12}
        # Six sizes, so that three levels fit Engine's 20 modes. 1 and 2 numbers have too few
        # outcomes for three tables; 7 and 9 play like 8 and 10.
        sizes = [3, 4, 5, 6, 8, 10]
        self.level_picks = {"calm": sizes, "bold": sizes, "wild": sizes, "chain": [10], "chainmax": [10]}
        self.level_cost = {"calm": 1.0, "bold": 1.0, "wild": 1.0, "chain": 10.0, "chainmax": 100.0}
        # Kilau numbers: marked numbers the player did not pick. Each one drawn adds a meter step.
        self.level_kilau = {"calm": 1, "bold": 1, "wild": 1, "chain": 1, "chainmax": 3}
        # Kilau round: in these levels 1 round in 5 marks 3 Kilau numbers instead of 1. Chain Max
        # marks 3 in every round. The share is (rounds, out of).
        self.kilau_round_levels = {"calm", "bold", "wild", "chain"}
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
            "calm": {
                3: [0, 0.8, 1.5, 7.8],
                4: [0, 0.3, 1.5, 2.5, 18],
                5: [0, 0.3, 1, 1.2, 6, 30],
                6: [0, 0, 0.8, 1.3, 2.5, 12, 50],
                8: [0, 0, 0.2, 1, 1.3, 2, 10, 40, 60],
                10: [0, 0, 0, 0.5, 0.6, 1.5, 5, 10, 20, 100, 100],
            },
            "bold": {
                3: [0, 0, 2.8, 16.5],
                4: [0, 0, 1, 5.5, 38],
                5: [0, 0, 0.6, 2.2, 11, 80],
                6: [0, 0, 0.5, 1.2, 4, 20, 160],
                8: [0, 0, 0, 0.5, 1.5, 6.5, 20, 100, 300],
                10: [0, 0, 0, 0, 1, 1.5, 6, 25, 120, 400, 400],
            },
            "wild": {
                3: [0, 0, 1, 32.5],
                4: [0, 0, 0.6, 2.5, 100],
                5: [0, 0, 0.3, 2, 8.4, 250],
                6: [0, 0, 0.2, 0.8, 6, 25, 500],
                8: [0, 0, 0, 0.3, 1.2, 4.4, 40, 400, 2000],
                10: [0, 0, 0, 0, 0.5, 1.2, 5, 50, 600, 2000, 2000],
            },
            "chain": {10: [0, 0, 1.2, 2.5, 5, 5, 10, 20, 500, 2000, 2000]},
            "chainmax": {10: [0, 0, 0, 20, 40, 40, 120, 300, 2500, 4000, 4000]},
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
        """(level, picks, draws, Kilau options) of a mode name such as "wild_8"."""
        level, picks = mode.rsplit("_", 1)
        return level, int(picks), self.level_draws[level], self.kilau_options(level)
