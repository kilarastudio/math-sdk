import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Dragon's Glint: scatter pays, tumbles and Glint Spots. Design and targets: MATH.md."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "dragons_glint"
        self.game_name = "dragons_glint"
        self.provider_name = "kilara"
        self.provider_numer = 0
        self.working_name = "Dragon's Glint"
        self.wincap = 25000.0
        self.win_type = "scatter"
        self.rtp = 0.967
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 6
        self.num_rows = [5] * self.num_reels
        # Board and Symbol Properties
        # Three tiers, each one a count that is really seen (8-9 is the common win, 12+ the rare one).
        t1, t2, t3 = (8, 9), (10, 11), (12, 36)
        pays = {
            "H1": (10.0, 25.0, 50.0),
            "H2": (5.0, 12.0, 25.0),
            "H3": (3.0, 6.0, 15.0),
            "H4": (2.0, 4.0, 12.0),
            "L1": (1.0, 2.0, 8.0),
            "L2": (0.6, 1.2, 5.0),
            "L3": (0.4, 1.0, 4.0),
            "L4": (0.3, 0.8, 3.0),
        }
        pay_group = {(tier, sym): value for sym, values in pays.items() for tier, value in zip((t1, t2, t3), values)}
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True
        self.special_symbols = {"wild": ["W"], "scatter": ["S"]}

        # Glint Spots: 0 = unlit, 1 = primed, 2+ = multiplier. An explosion primes an
        # unlit spot, turns a primed spot into 2x, then grows a lit spot up to the cap.
        # "growth" is "double" (2, 4, 8...) or "add" (2, 3, 4...); "combine" is how the lit
        # spots under one symbol win make its multiplier: their "sum" or their "max".
        self.glint_rule = {"combine": "max", "growth": "double", "cap": 4096}

        self.freespin_triggers = {
            self.basegame_type: {n: {4: 10, 5: 12}.get(n, 15) for n in range(4, 31)},
            self.freegame_type: {n: 5 for n in range(3, 31)},
        }
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
            self.freegame_type: min(self.freespin_triggers[self.freegame_type].keys()) - 1,
        }
        # Reels (reels/make_reels.py)
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))

        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["FR0"]

        # Glint Strike: the character lights spots on the revealed board before it is evaluated.
        strike_shape = {"count": {3: 40, 4: 30, 5: 20, 6: 10}, "value": {2: 70, 4: 25, 8: 5}}
        no_strike = {"prob": 0.0, **strike_shape}
        base_strike = {"prob": 0.10, **strike_shape}
        every_strike = {"prob": 1.0, **strike_shape}
        # Every free spins session (triggered or bought) opens with a Glint Strike; None turns it off.
        self.fs_start_strike = strike_shape
        # Upgraded sessions start with every spot already lit.
        super_start = {"count": 30, "value": 4}
        hoard_start = {"count": 30, "value": 8}

        # Scatters on a board that is forced to trigger, in the proportions the base reels give.
        natural_scatters = {4: 926, 5: 71, 6: 3}

        # No round is forced to the max win and no reel exists only to reach it: max-win rounds
        # are free spins that got there. "freegame_tail" books are free spins sampled at min_win
        # or more, so the rare top of the range has books in every mode; game_weights.py gives
        # them the probability the reels give that range.
        def freegame_distribution(criteria: str, quota: float, strike: dict, fs_start_glint, min_win=None):
            conditions = {
                "reel_weights": {
                    self.basegame_type: {"BR0": 1},
                    self.freegame_type: {"FR0": 1},
                },
                "scatter_triggers": natural_scatters,
                "strike": strike,
                "fs_start_glint": fs_start_glint,
                "force_wincap": False,
                "force_freegame": True,
            }
            if min_win is not None:
                conditions["min_win"] = min_win
            return Distribution(criteria=criteria, quota=quota, conditions=conditions)

        def spin_distributions(strike: dict) -> list:
            """Distributions shared by the modes played spin by spin (base, ante, boost)."""
            base_only = {
                "reel_weights": {self.basegame_type: {"BR0": 1}},
                "strike": strike,
                "fs_start_glint": None,
                "force_wincap": False,
                "force_freegame": False,
            }
            return [
                freegame_distribution("freegame", 0.1, strike, None),
                freegame_distribution("freegame_tail", 0.02, strike, None, min_win=2000),
                Distribution(criteria="0", quota=0.4, win_criteria=0.0, conditions=dict(base_only)),
                Distribution(criteria="basegame", quota=0.48, conditions=dict(base_only)),
            ]

        def feature_distributions(fs_start_glint, tail_min) -> list:
            """Distributions for the modes that go straight to free spins (bonus, super, hoard)."""
            if tail_min is None:
                return [freegame_distribution("freegame", 1.0, no_strike, fs_start_glint)]
            return [
                freegame_distribution("freegame", 0.98, no_strike, fs_start_glint),
                freegame_distribution("freegame_tail", 0.02, no_strike, fs_start_glint, min_win=tail_min),
            ]

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

        # Costs are each mode's natural value / RTP (MATH.md, "Budget").
        self.bet_modes = [
            mode("base", 1.0, spin_distributions(base_strike), False),
            mode("ante", 3.0, spin_distributions(base_strike), False),
            mode("boost", 1.9, spin_distributions(every_strike), False),
            mode("bonus", 100.0, feature_distributions(None, 2000), True),
            mode("super", 350.0, feature_distributions(super_start, 5000), True),
            mode("hoard", 640.0, feature_distributions(hoard_start, None), True),
        ]
