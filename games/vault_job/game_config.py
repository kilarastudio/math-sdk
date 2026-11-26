import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """The Vault Job: 5x4 lines with four crew wilds. Design and targets: MATH.md."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.game_id = "vault_job"
        self.game_name = "vault_job"
        self.provider_name = "kilara"
        self.provider_numer = 0
        self.working_name = "The Vault Job"
        self.wincap = 20000.0
        self.win_type = "lines"
        self.rtp = 0.967
        self.construct_paths()

        self.num_reels = 5
        self.num_rows = [4] * self.num_reels

        # Pays for 3, 4 and 5 of a kind on one line, in multiples of the base bet (20 lines).
        line_pays = {
            "H1": (1.5, 6.0, 25.0),
            "H2": (1.0, 3.0, 12.0),
            "H3": (0.5, 2.0, 8.0),
            "H4": (0.4, 1.5, 6.0),
            "L1": (0.3, 0.7, 2.5),
            "L2": (0.2, 0.5, 2.0),
            "L3": (0.1, 0.4, 1.5),
            "L4": (0.1, 0.3, 1.2),
        }
        self.paytable = {(k, sym): v for sym, pays in line_pays.items() for k, v in zip((3, 4, 5), pays)}
        # A line made of crew alone pays as H1.
        for k, v in zip((3, 4, 5), line_pays["H1"]):
            self.paytable[(k, "W")] = v

        self.paylines = {
            i + 1: line
            for i, line in enumerate(
                [
                    [0, 0, 0, 0, 0], [1, 1, 1, 1, 1], [2, 2, 2, 2, 2], [3, 3, 3, 3, 3],
                    [0, 1, 2, 1, 0], [1, 2, 3, 2, 1], [3, 2, 1, 2, 3], [2, 1, 0, 1, 2],
                    [0, 0, 1, 0, 0], [1, 1, 2, 1, 1], [2, 2, 3, 2, 2], [3, 3, 2, 3, 3],
                    [2, 2, 1, 2, 2], [1, 1, 0, 1, 1], [0, 1, 1, 1, 0], [1, 2, 2, 2, 1],
                    [2, 3, 3, 3, 2], [3, 2, 2, 2, 3], [2, 1, 1, 1, 2], [1, 0, 0, 0, 1],
                ]
            )
        }

        self.include_padding = True
        # Crew: WD Driver, WC Safecracker, WM Muscle, WH Hacker. All four are wild.
        self.crew = ("WD", "WC", "WM", "WH")
        self.special_symbols = {"wild": list(self.crew), "scatter": ["S"], "multiplier": list(self.crew)}

        # Multipliers each crew member carries when it lands. The Hacker copies the highest
        # multiplier on the board, at least hacker_min. A line is paid times the sum of the
        # multipliers of the crew on it (no crew multiplier above 1: x1).
        self.crew_mult = {"WD": 2, "WC": 2, "WM": 1}
        # In The Job a Safecracker starts at x1 and climbs safecracker_ladder.
        self.job_crew_mult = {"WD": 2, "WC": 1, "WM": 1}
        self.hacker_min = 2
        # The Job: a Safecracker steps up this ladder every time it is part of a win.
        # Reels (0-based) where the crew a round starts with is placed.
        self.start_reels = (1,)
        self.safecracker_ladder = (1, 2, 3, 5, 8, 12, 20, 30, 50, 80, 120, 200, 300, 500, 1000)

        # Scatters that start The Job -> free spins. Every scatter that lands during The Job adds
        # one spin.
        self.fs_by_scatters = {3: 10, 4: 12, 5: 15}
        self.freespin_triggers = {
            self.basegame_type: dict(self.fs_by_scatters),
            self.freegame_type: {n: n for n in range(1, 21)},
        }
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 99}

        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv"}
        self.reels = {r: self.read_reels_csv(os.path.join(self.reels_path, f)) for r, f in reels.items()}
        self.padding_reels[self.basegame_type] = self.reels["BR0"]
        self.padding_reels[self.freegame_type] = self.reels["FR0"]

        # Bought rounds start with this crew already on the board, sticky: (crew, multiplier).
        self.job_start_crew = [("WC", 1)]
        self.buy_start_crew = {"bonus": [], "inside": [("WC", 2)], "heist": [("WC", 3), ("WC", 3)]}

        # Scatters at the reveal of a base board forced to trigger: the mix unforced play gives
        # (run.py --natural).
        natural_scatters = {3: 34750, 4: 1356, 5: 18}

        def fs_dist(criteria, quota, scatters, min_win=None):
            conditions = {
                "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}},
                "scatter_triggers": scatters,
                "force_wincap": False,
                "force_freegame": True,
            }
            if min_win is not None:
                conditions["min_win"] = min_win
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
                fs_dist("freegame", 0.98, {3: 1}),
                fs_dist("freegame_tail", 0.02, {3: 1}, min_win=tail_min),
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
            mode("ante", 2.0, spin_distributions(), False),
            mode("bonus", 130.0, buy_distributions(2000), True),
            mode("inside", 290.0, buy_distributions(5000), True),
            mode("heist", 600.0, buy_distributions(8000), True),
        ]
