import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Dwanda: cluster pays, tumbles, two-sided territory and Clash cells. Design and targets: MATH.md."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "dwanda"
        self.game_name = "dwanda"
        self.provider_name = "kilara"
        self.provider_numer = 0
        self.working_name = "Dwanda"
        self.wincap = 25000.0
        self.win_type = "cluster"
        self.rtp = 0.967
        self.construct_paths()

        self.num_reels = 7
        self.num_rows = [7] * self.num_reels
        # Clusters of 5, 6-8, 9-12 and 13+ like symbols. Phoenix symbols P1-P4 (warm) and dragon
        # symbols D1-D4 (cool) pay the same by rank.
        tiers = ((5, 5), (6, 8), (9, 12), (13, 49))
        by_rank = {
            1: (5.0, 13.0, 32.0, 80.0),
            2: (2.0, 5.0, 13.0, 40.0),
            3: (0.8, 2.0, 5.0, 16.0),
            4: (0.4, 1.0, 3.2, 8.0),
        }
        pays = {f"{side}{rank}": values for rank, values in by_rank.items() for side in ("P", "D")}
        pay_group = {(tier, sym): value for sym, values in pays.items() for tier, value in zip(tiers, values)}
        self.paytable = self.convert_range_table(pay_group)
        self.side = {sym: sym[0] for sym in pays}

        self.include_padding = True
        self.special_symbols = {"wild": ["W"], "scatter": ["S"]}

        # Territory: a winning cluster marks its cells for its side. A cell marked for both sides
        # becomes a Clash cell at clash_start; a Clash cell under a later winning cluster doubles,
        # up to clash_cap. Clusters are paid times the sum of the Clash cells under them.
        self.clash_start = 2
        self.clash_cap = 1024
        # In the Duel a winning cluster's mark also spreads to the cells next to it.
        self.duel_spread = True

        # Free spins (the Duel): territory and Clash cells stay for the whole feature.
        self.fs_by_scatters = {3: 10, 4: 12, 5: 15}
        self.fs_retrigger = 5
        self.freespin_triggers = {
            self.basegame_type: {n: self.fs_by_scatters.get(n, 15) for n in range(3, 50)},
            self.freegame_type: {n: self.fs_retrigger for n in range(3, 50)},
        }
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 2}

        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv"}
        self.reels = {r: self.read_reels_csv(os.path.join(self.reels_path, f)) for r, f in reels.items()}
        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["FR0"]

        # Bought rounds that start the Duel with Clash cells already on the board: (count, value).
        self.buy_start_clash = {"bonus": (0, 0), "blaze": (5, 4), "eclipse": (9, 8)}

        natural_scatters = {3: 96113, 4: 3792, 5: 95}

        def fs_dist(criteria, quota, scatters, min_win=None, exact=None):
            conditions = {
                "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}},
                "scatter_triggers": scatters,
                "force_wincap": False,
                "force_freegame": True,
            }
            if min_win is not None:
                conditions["min_win"] = min_win
            if exact is not None:
                conditions["exact_scatters"] = exact
            return Distribution(criteria=criteria, quota=quota, conditions=conditions)

        def spin_distributions():
            base_only = {"reel_weights": {self.basegame_type: {"BR0": 1}}, "force_wincap": False, "force_freegame": False}
            return [
                fs_dist("freegame", 0.1, natural_scatters),
                fs_dist("freegame_tail", 0.01, natural_scatters, min_win=2000),
                Distribution(criteria="0", quota=0.4, win_criteria=0.0, conditions=dict(base_only)),
                Distribution(criteria="basegame", quota=0.49, conditions=dict(base_only)),
            ]

        def buy_distributions(tail_min):
            return [
                fs_dist("freegame", 0.98, {3: 1}, exact=3),
                fs_dist("freegame_tail", 0.02, {3: 1}, min_win=tail_min, exact=3),
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

        self.bet_modes = [
            mode("base", 1.0, spin_distributions(), False),
            mode("ante", 3.0, spin_distributions(), False),
            mode("bonus", 160.0, buy_distributions(2000), True),
            mode("blaze", 250.0, buy_distributions(4000), True),
            mode("eclipse", 500.0, buy_distributions(6000), True),
        ]
