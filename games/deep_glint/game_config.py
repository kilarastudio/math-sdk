import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """DEEP GLINT: scatter pays, tumbles and Glint Spots."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "deep_glint"
        self.game_name = "deep_glint"
        self.provider_name = "kilara"
        self.provider_numer = 0
        self.working_name = "DEEP GLINT"
        self.wincap = 15000.0
        self.win_type = "scatter"
        self.rtp = 0.965
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 6
        self.num_rows = [5] * self.num_reels
        # Board and Symbol Properties
        t1, t2, t3, t4 = (8, 8), (9, 10), (11, 13), (14, 36)
        pay_group = {
            (t1, "H1"): 3.0,
            (t2, "H1"): 7.5,
            (t3, "H1"): 15.0,
            (t4, "H1"): 60.0,
            (t1, "H2"): 2.0,
            (t2, "H2"): 5.0,
            (t3, "H2"): 10.0,
            (t4, "H2"): 40.0,
            (t1, "H3"): 1.3,
            (t2, "H3"): 3.2,
            (t3, "H3"): 7.0,
            (t4, "H3"): 30.0,
            (t1, "H4"): 1.0,
            (t2, "H4"): 2.5,
            (t3, "H4"): 6.0,
            (t4, "H4"): 20.0,
            (t1, "L1"): 0.6,
            (t2, "L1"): 1.5,
            (t3, "L1"): 4.0,
            (t4, "L1"): 10.0,
            (t1, "L2"): 0.4,
            (t2, "L2"): 1.2,
            (t3, "L2"): 3.5,
            (t4, "L2"): 8.0,
            (t1, "L3"): 0.2,
            (t2, "L3"): 0.8,
            (t3, "L3"): 2.5,
            (t4, "L3"): 5.0,
            (t1, "L4"): 0.1,
            (t2, "L4"): 0.5,
            (t3, "L4"): 1.5,
            (t4, "L4"): 4.0,
        }
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True
        self.special_symbols = {"wild": ["W"], "scatter": ["S"]}

        # Glint Spots: 0 = unlit, 1 = primed, 2+ = multiplier. An explosion primes an
        # unlit spot, turns a primed spot into 2x, then grows a lit spot up to the cap.
        # "growth" is "double" (2, 4, 8...) or "add" (2, 3, 4...); "combine" is how the lit
        # spots under one symbol win make its multiplier: their "sum" or their "max".
        self.glint_rule = {"combine": "max", "growth": "double", "cap": 256}

        self.freespin_triggers = {
            self.basegame_type: {n: {4: 12, 5: 14}.get(n, 17) for n in range(4, 31)},
            self.freegame_type: {n: 5 for n in range(3, 31)},
        }
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
            self.freegame_type: min(self.freespin_triggers[self.freegame_type].keys()) - 1,
        }
        # Reels
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv", "WCAP": "WCAP.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["FR0"]

        # Glint Strike: the character lights spots on the revealed board before it is evaluated.
        strike_shape = {"count": {3: 40, 4: 30, 5: 20, 6: 10}, "value": {2: 70, 4: 25, 8: 5}}
        no_strike = {"prob": 0.0, **strike_shape}
        base_strike = {"prob": 0.05, **strike_shape}
        every_strike = {"prob": 1.0, **strike_shape}
        # Super free spins start with every spot lit at 2x.
        super_start = {"count": 30, "value": 2}
        # Every free spins session (triggered or bought) opens with a Glint Strike; None turns it off.
        self.fs_start_strike = strike_shape

        # Free spins of at least this win are also sampled on their own ("freegame_tail"), so the
        # rare 5,000x+ range has books in every mode. game_weights.py gives them their natural share.
        self.fs_tail_min = 2000

        def freegame_distribution(criteria: str, quota: float, strike: dict, fs_scatters: dict, fs_start_glint):
            conditions = {
                "reel_weights": {
                    self.basegame_type: {"BR0": 1},
                    self.freegame_type: {"FR0": 1},
                },
                "scatter_triggers": fs_scatters,
                "strike": strike,
                "fs_start_glint": fs_start_glint,
                "force_wincap": False,
                "force_freegame": True,
            }
            if criteria == "freegame_tail":
                conditions["min_win"] = self.fs_tail_min
            return Distribution(criteria=criteria, quota=quota, conditions=conditions)

        def spin_distributions(strike: dict, fs_scatters: dict) -> list:
            """Distributions shared by the modes played spin by spin (base, ante, boost)."""
            return [
                Distribution(
                    criteria="wincap",
                    quota=0.001,
                    win_criteria=self.wincap,
                    conditions={
                        "reel_weights": {
                            self.basegame_type: {"BR0": 1},
                            self.freegame_type: {"FR0": 1, "WCAP": 5},
                        },
                        "scatter_triggers": {5: 1, 6: 2},
                        "strike": strike,
                        "fs_start_glint": None,
                        "force_wincap": True,
                        "force_freegame": True,
                    },
                ),
                freegame_distribution("freegame", 0.1, strike, fs_scatters, None),
                freegame_distribution("freegame_tail", 0.005, strike, fs_scatters, None),
                Distribution(
                    criteria="0",
                    quota=0.4,
                    win_criteria=0.0,
                    conditions={
                        "reel_weights": {self.basegame_type: {"BR0": 1}},
                        "strike": strike,
                        "fs_start_glint": None,
                        "force_wincap": False,
                        "force_freegame": False,
                    },
                ),
                Distribution(
                    criteria="basegame",
                    quota=0.494,
                    conditions={
                        "reel_weights": {self.basegame_type: {"BR0": 1}},
                        "strike": strike,
                        "fs_start_glint": None,
                        "force_wincap": False,
                        "force_freegame": False,
                    },
                ),
            ]

        def feature_distributions(fs_start_glint) -> list:
            """Distributions for the modes that go straight to free spins (bonus, super)."""
            return [
                Distribution(
                    criteria="wincap",
                    quota=0.001,
                    win_criteria=self.wincap,
                    conditions={
                        "reel_weights": {
                            self.basegame_type: {"BR0": 1},
                            self.freegame_type: {"FR0": 1, "WCAP": 5},
                        },
                        "scatter_triggers": {5: 1, 6: 2},
                        "strike": no_strike,
                        "fs_start_glint": fs_start_glint,
                        "force_wincap": True,
                        "force_freegame": True,
                    },
                ),
                freegame_distribution("freegame", 0.994, no_strike, natural_scatters, fs_start_glint),
                freegame_distribution("freegame_tail", 0.005, no_strike, natural_scatters, fs_start_glint),
            ]

        natural_scatters = {4: 20, 5: 4, 6: 1}
        self.bet_modes = [
            BetMode(
                name="base",
                cost=1.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=spin_distributions(base_strike, natural_scatters),
            ),
            BetMode(
                name="ante",
                cost=1.5,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=spin_distributions(base_strike, natural_scatters),
            ),
            BetMode(
                name="boost",
                cost=1.75,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=True,
                is_buybonus=False,
                distributions=spin_distributions(every_strike, natural_scatters),
            ),
            BetMode(
                name="bonus",
                cost=140.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=feature_distributions(None),
            ),
            BetMode(
                name="super",
                cost=250.0,
                rtp=self.rtp,
                max_win=self.wincap,
                auto_close_disabled=False,
                is_feature=False,
                is_buybonus=True,
                distributions=feature_distributions(super_start),
            ),
        ]
