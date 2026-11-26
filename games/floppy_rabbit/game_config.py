import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Floppy Rabbit: cluster pays, cascades, footprints, Hop and Flop. Design and targets: MATH.md."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "floppy_rabbit"
        self.game_name = "floppy_rabbit"
        self.provider_name = "kilara"
        self.provider_numer = 0
        self.working_name = "Floppy Rabbit"
        self.wincap = 25000.0
        self.win_type = "cluster"
        self.rtp = 0.967
        self.construct_paths()

        # Game Dimensions
        self.num_reels = 7
        self.num_rows = [7] * self.num_reels
        # Clusters of 5, 6-8, 9-12 and 13+ like symbols.
        tiers = ((5, 5), (6, 8), (9, 12), (13, 49))
        pays = {
            "H1": (5.0, 12.0, 25.0, 60.0),
            "H2": (2.0, 5.0, 10.0, 40.0),
            "H3": (1.2, 3.0, 7.0, 30.0),
            "H4": (0.9, 2.4, 6.0, 20.0),
            "L1": (0.6, 1.4, 4.0, 10.0),
            "L2": (0.4, 1.1, 3.5, 8.0),
            "L3": (0.2, 0.7, 2.5, 5.0),
        }
        pay_group = {(tier, sym): value for sym, values in pays.items() for tier, value in zip(tiers, values)}
        self.paytable = self.convert_range_table(pay_group)

        self.include_padding = True
        self.special_symbols = {"wild": ["W"], "scatter": ["S"]}

        # Footprints: 0 = none, otherwise the cell's multiplier (2, 4, ... up to the cap). A cluster
        # is paid times the sum of the footprints under it.
        self.footprint_cap = 4096
        # A hop reaches this many cells in any direction.
        self.hop_reach = 2
        # Base game: the chance that the action after a winning cascade is a flop, from this
        # cascade on. The hop at the reveal is always a hop.
        self.base_flop = 0.2
        self.base_flop_from_cascade = 2
        # Flop Time: scatters that triggered -> rabbits, and the chance that one action of one
        # rabbit is a flop, by the number of rabbits on the board.
        self.rabbits_by_scatters = {3: 1, 4: 2, 5: 3}
        self.fs_flop = {1: 0.114, 2: 0.049, 3: 0.0335}

        # Free spins before which the first rabbit flops for certain, so no Flop Time goes
        # without a flop.
        self.fs_sure_flop_spins = (9,)

        self.freespin_triggers = {
            self.basegame_type: {n: 12 for n in range(3, 50)},
            self.freegame_type: {n: 5 for n in range(3, 50)},
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

        # Scatters shown at the reveal of a base board that is forced to trigger. Cascades can
        # bring more scatters down before the trigger is counted, so these are the reveal weights
        # that give the counts unforced play ends with: 95.53% three, 4.33% four, 0.14% five or
        # more (10,000,000 unforced base spins, 28,860 triggers; solved from 600,000 forced
        # boards per count, run.py --natural and --forced).
        natural_scatters = {3: 96414, 4: 3476, 5: 110}

        def freegame_distribution(criteria: str, quota: float, scatters: dict, min_win=None, exact=None):
            conditions = {
                "reel_weights": {
                    self.basegame_type: {"BR0": 1},
                    self.freegame_type: {"FR0": 1},
                },
                "scatter_triggers": scatters,
                "force_wincap": False,
                "force_freegame": True,
            }
            if min_win is not None:
                conditions["min_win"] = min_win
            if exact is not None:
                conditions["exact_scatters"] = exact
            return Distribution(criteria=criteria, quota=quota, conditions=conditions)

        def spin_distributions() -> list:
            """Distributions of the modes played spin by spin (base, ante)."""
            base_only = {
                "reel_weights": {self.basegame_type: {"BR0": 1}},
                "force_wincap": False,
                "force_freegame": False,
            }
            return [
                freegame_distribution("freegame", 0.1, natural_scatters),
                freegame_distribution("freegame_tail", 0.01, natural_scatters, min_win=2000),
                Distribution(criteria="0", quota=0.4, win_criteria=0.0, conditions=dict(base_only)),
                Distribution(criteria="basegame", quota=0.49, conditions=dict(base_only)),
            ]

        def feature_distributions(scatters: int, tail_min) -> list:
            """Distributions of the modes that go straight to Flop Time."""
            forced = {scatters: 1}
            if tail_min is None:
                return [freegame_distribution("freegame", 1.0, forced, exact=scatters)]
            return [
                freegame_distribution("freegame", 0.98, forced, exact=scatters),
                freegame_distribution("freegame_tail", 0.02, forced, min_win=tail_min, exact=scatters),
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

        # Costs are each mode's natural value / RTP (MATH.md, "Anggaran").
        self.bet_modes = [
            mode("base", 1.0, spin_distributions(), False),
            mode("ante", 3.0, spin_distributions(), False),
            mode("bonus", 110.0, feature_distributions(3, 2000), True),
            mode("double", 250.0, feature_distributions(4, 5000), True),
            mode("fluffle", 500.0, feature_distributions(5, None), True),
        ]
