import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Pratala: scatter pays, tumbles and Glint Spots. Design and targets: MATH.md."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "pratala"
        self.game_name = "pratala"
        self.provider_name = "kilara"
        self.provider_numer = 0
        self.working_name = "Pratala"
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

        # Glint Spots: 0 = unlit, 1 = primed, 2+ = multiplier. An explosion primes an unlit spot,
        # lights a primed spot at 2x, then doubles a lit spot up to "explode_cap". Past that only
        # the dragon's gaze doubles a spot, up to "cap". A symbol win is multiplied by the
        # brightest lit spot under it.
        self.glint_rule = {"explode_cap": 8, "cap": 4096}

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

        # Glint Strike: the dragon lights spots on the revealed board before it is evaluated.
        strike_values = {2: 70, 4: 25, 8: 5}
        strike_shape = {"count": {3: 25, 4: 30, 5: 25, 6: 20}, "value": strike_values}
        no_strike = {"prob": 0.0, **strike_shape}
        base_strike = {"prob": 0.10, **strike_shape}
        every_strike = {"prob": 1.0, **strike_shape}
        # Every free spins session (triggered or bought) opens with a wider strike; None turns it off.
        self.fs_start_strike = {"count": {8: 52, 10: 30, 12: 14, 15: 4}, "value": strike_values}
        # Six or more triggering eyes: every spot starts lit at this value.
        self.fs_trigger_glint = {6: 128}
        # Bought sessions with a floor of their own: every spot starts lit at this value.
        super_floor = 8
        hoard_floor = 4

        # Scatters shown at the reveal of a board that is forced to trigger. Tumbles can bring more
        # eyes down before the trigger is counted, so these are the reveal weights that give the
        # counts unforced play ends with: 93.52% four, 6.24% five, 0.239% six or more (130,000,000
        # unforced base spins, 441,029 triggers; solved from 4,000,000 forced boards per count).
        natural_scatters = {4: 954759, 5: 44133, 6: 1108}

        # No round is forced to the max win and no reel exists only to reach it: max-win rounds
        # are free spins that got there. "freegame_tail" books are free spins sampled at min_win
        # or more, so the rare top of the range has books in every mode; game_weights.py gives
        # them the probability the reels give that range.
        def freegame_distribution(criteria: str, quota: float, strike: dict, fs_start_glint, min_win=None, sweep=False):
            conditions = {
                "reel_weights": {
                    self.basegame_type: {"BR0": 1},
                    self.freegame_type: {"FR0": 1},
                },
                "scatter_triggers": natural_scatters,
                "strike": strike,
                "fs_start_glint": fs_start_glint,
                "fs_sweep": sweep,
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
                "fs_sweep": False,
                "force_wincap": False,
                "force_freegame": False,
            }
            return [
                freegame_distribution("freegame", 0.1, strike, None),
                freegame_distribution("freegame_tail", 0.01, strike, None, min_win=2000),
                Distribution(criteria="0", quota=0.4, win_criteria=0.0, conditions=dict(base_only)),
                Distribution(criteria="basegame", quota=0.49, conditions=dict(base_only)),
            ]

        def feature_distributions(fs_start_glint, tail_min, sweep=False) -> list:
            """Distributions for the modes that go straight to free spins (bonus, super, hoard)."""
            if tail_min is None:
                return [freegame_distribution("freegame", 1.0, no_strike, fs_start_glint, sweep=sweep)]
            return [
                freegame_distribution("freegame", 0.98, no_strike, fs_start_glint, sweep=sweep),
                freegame_distribution("freegame_tail", 0.02, no_strike, fs_start_glint, min_win=tail_min, sweep=sweep),
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
            mode("boost", 1.85, spin_distributions(every_strike), False),
            mode("bonus", 100.0, feature_distributions(None, 2000), True),
            mode("super", 205.0, feature_distributions(super_floor, 5000), True),
            mode("hoard", 435.0, feature_distributions(hoard_floor, None, sweep=True), True),
        ]
