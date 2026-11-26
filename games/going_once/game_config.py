import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Going Once: 5x3 lines with an automatic hold & win auction. Design and targets: MATH.md."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "going_once"
        self.game_name = "going_once"
        self.provider_name = "kilara"
        self.provider_numer = 0
        self.working_name = "Going Once"
        self.wincap = 25000.0
        self.win_type = "lines"
        self.rtp = 0.967
        self.construct_paths()

        self.num_reels = 5
        self.num_rows = [3] * self.num_reels

        # Pays for 3, 4 and 5 of a kind on one line, in multiples of the base bet (20 lines).
        line_pays = {
            "H1": (3.0, 12.0, 45.0),
            "H2": (2.0, 7.5, 25.0),
            "H3": (1.5, 4.5, 15.0),
            "H4": (1.2, 3.0, 12.0),
            "L1": (0.8, 1.5, 6.0),
            "L2": (0.6, 1.2, 4.5),
            "L3": (0.4, 1.0, 3.8),
            "L4": (0.3, 0.8, 3.0),
        }
        self.paytable = {(k, sym): v for sym, pays in line_pays.items() for k, v in zip((3, 4, 5), pays)}
        for k, v in zip((3, 4, 5), line_pays["H1"]):
            self.paytable[(k, "W")] = v

        self.paylines = {
            i + 1: line
            for i, line in enumerate(
                [
                    [1, 1, 1, 1, 1], [0, 0, 0, 0, 0], [2, 2, 2, 2, 2], [0, 1, 2, 1, 0], [2, 1, 0, 1, 2],
                    [0, 0, 1, 0, 0], [2, 2, 1, 2, 2], [1, 0, 0, 0, 1], [1, 2, 2, 2, 1], [0, 1, 0, 1, 0],
                    [2, 1, 2, 1, 2], [1, 1, 0, 1, 1], [1, 1, 2, 1, 1], [0, 1, 1, 1, 0], [2, 1, 1, 1, 2],
                    [1, 0, 1, 0, 1], [1, 2, 1, 2, 1], [0, 0, 2, 0, 0], [2, 2, 0, 2, 2], [0, 2, 0, 2, 0],
                ]
            )
        }

        self.include_padding = True
        # W wild (reels 2-4), P lot (carries a value), G gavel (base: reel 3 only), B buyer (auction only).
        self.special_symbols = {"wild": ["W"], "prize": ["P"], "gavel": ["G"], "buyer": ["B"]}

        # Lot values in multiples of the base bet, with weights: base reels and the auction.
        self.lot_values = {
            "base": {1: 400, 2: 250, 3: 150, 5: 100, 10: 50, 25: 12, 50: 3},
            "auction": {1: 400, 2: 250, 3: 150, 5: 100, 10: 50, 25: 12, 50: 3},
        }
        # Lots on the board that start the auction.
        self.auction_trigger = 6
        self.respins = 3
        # In the auction every empty cell draws one of these on every respin (per mille).
        self.respin_draw = {"P": 60, "G": 12, "B": 8}
        # Last Bid: when the hammer falls, the final bid multiplies the auction total (x1 = no raise).
        self.last_bid = {1: 700, 2: 180, 3: 60, 5: 35, 10: 15, 25: 6, 50: 3, 100: 1}
        # A full board of 15 lots doubles the auction total ("Full House").
        self.full_house_mult = 2
        # Base game: a gavel on reel 3 doubles the spin's line wins.
        self.base_gavel_mult = 2

        self.freespin_triggers = {self.basegame_type: {6: 3}, self.freegame_type: {6: 3}}
        self.anticipation_triggers = {self.basegame_type: 99, self.freegame_type: 99}

        reels = {"BR0": "BR0.csv"}
        self.reels = {r: self.read_reels_csv(os.path.join(self.reels_path, f)) for r, f in reels.items()}
        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["BR0"]

        # Bought rounds start the auction on a board with this many lots and these extras.
        self.buy_start = {
            "bonus": {"lots": 6, "gavels": 0},
            "gavel": {"lots": 6, "gavels": 1},
            "private": {"lots": 9, "gavels": 2},
        }

        def dist(criteria, quota, force, min_win=None, win_criteria=None):
            conditions = {
                "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"BR0": 1}},
                "force_wincap": False,
                "force_freegame": force,
            }
            if min_win is not None:
                conditions["min_win"] = min_win
            return Distribution(criteria=criteria, quota=quota, win_criteria=win_criteria, conditions=conditions)

        def spin_distributions():
            return [
                dist("freegame", 0.1, True),
                dist("freegame_tail", 0.01, True, min_win=1500),
                dist("0", 0.4, False, win_criteria=0.0),
                dist("basegame", 0.49, False),
            ]

        def buy_distributions(tail_min):
            return [dist("freegame", 0.98, True), dist("freegame_tail", 0.02, True, min_win=tail_min)]

        def mode(name, cost, distributions, buy):
            return BetMode(
                name=name,
                cost=cost,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=not buy,
                is_buybonus=buy,
                distributions=distributions,
            )

        self.bet_modes = [
            mode("base", 1.0, spin_distributions(), False),
            mode("ante", 1.5, spin_distributions(), False),
            mode("bonus", 110.0, buy_distributions(1500), True),
            mode("gavel", 190.0, buy_distributions(3000), True),
            mode("private", 340.0, buy_distributions(5000), True),
        ]
