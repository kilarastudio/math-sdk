"""Locked configuration for Keris Wilds: Pusaka Sang Raja v2.2 RGS."""

from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path

from src.config.betmode import BetMode
from src.config.config import Config
from src.config.distributions import Distribution


LOCKED_CSV_SHA256 = "d3a70618b4a5cb9a9beb6b932b56387b2355c3ce70fcb5bc5e061573383136ca"
LOCKED_STRIP_HASHES = {
    "BR0": "e45092885d982714944d8965d10cc16c9d2b274eea2c555534b5156a935389a1",
    "BR1": "0cf08ac940e4738a1d98aac7781149d34ff20a92b0785190e08af98dda2fa514",
    "FR0": "2c337483f216686682e9df266f9b32e591c1f9a5cc4489949766f1fa6ca901fc",
}
SYMBOL_IDS = {symbol: idx for idx, symbol in enumerate((*[f"H{i}" for i in range(1, 5)], *[f"L{i}" for i in range(1, 6)], "W", "S"))}

PAYLINES = [
    (0, 0, 0, 0, 0), (1, 1, 1, 1, 1), (2, 2, 2, 2, 2), (3, 3, 3, 3, 3),
    (0, 1, 2, 1, 0), (3, 2, 1, 2, 3), (1, 2, 3, 2, 1), (2, 1, 0, 1, 2),
    (0, 1, 1, 1, 0), (3, 2, 2, 2, 3), (1, 2, 2, 2, 1), (2, 1, 1, 1, 2),
    (1, 0, 0, 0, 1), (2, 3, 3, 3, 2), (0, 0, 1, 0, 0), (3, 3, 2, 3, 3),
    (1, 1, 0, 1, 1), (2, 2, 3, 2, 2), (1, 1, 2, 1, 1), (2, 2, 1, 2, 2),
    (0, 1, 0, 1, 0), (3, 2, 3, 2, 3), (1, 0, 1, 0, 1), (2, 3, 2, 3, 2),
    (1, 2, 1, 2, 1), (2, 1, 2, 1, 2), (0, 0, 1, 2, 1), (3, 3, 2, 1, 2),
    (1, 1, 2, 3, 2), (2, 2, 1, 0, 1), (1, 0, 1, 2, 1), (2, 3, 2, 1, 2),
    (1, 2, 1, 0, 1), (2, 1, 2, 3, 2), (0, 1, 2, 3, 2), (3, 2, 1, 0, 1),
    (1, 0, 0, 1, 2), (2, 3, 3, 2, 1), (1, 2, 3, 3, 2), (2, 1, 0, 0, 1),
]


def _semantic_strip_hash(reels: list[list[str]]) -> str:
    raw = bytes(SYMBOL_IDS[symbol] for reel in reels for symbol in reel)
    return hashlib.sha256(raw).hexdigest()


def load_locked_reels(path: str | os.PathLike[str]) -> dict[str, list[list[str]]]:
    """Load the published long-form reel CSV and reject any drift."""
    reel_path = Path(path)
    file_hash = hashlib.sha256(reel_path.read_bytes()).hexdigest()
    if file_hash != LOCKED_CSV_SHA256:
        raise ValueError(f"Locked reel CSV hash mismatch: {file_hash}")

    loaded: dict[str, dict[int, list[str]]] = {}
    with reel_path.open("r", encoding="utf-8", newline="") as reel_file:
        for row in csv.DictReader(reel_file):
            reelset, reel_number = row["reel"].rsplit("_R", 1)
            reel_index = int(reel_number) - 1
            target = loaded.setdefault(reelset, {}).setdefault(reel_index, [])
            position = int(row["position"])
            if position != len(target):
                raise ValueError(f"Non-contiguous position in {row['reel']}: {position}")
            if row["symbol"] not in SYMBOL_IDS:
                raise ValueError(f"Unknown locked symbol: {row['symbol']}")
            target.append(row["symbol"])

    if set(loaded) != set(LOCKED_STRIP_HASHES):
        raise ValueError(f"Unexpected reelsets: {sorted(loaded)}")

    result: dict[str, list[list[str]]] = {}
    for reelset, expected_hash in LOCKED_STRIP_HASHES.items():
        reels = loaded[reelset]
        if set(reels) != set(range(5)) or any(len(reels[idx]) != 300 for idx in range(5)):
            raise ValueError(f"Invalid shape for locked reelset {reelset}")
        ordered = [reels[idx] for idx in range(5)]
        actual_hash = _semantic_strip_hash(ordered)
        if actual_hash != expected_hash:
            raise ValueError(f"Locked strip hash mismatch for {reelset}: {actual_hash}")
        result[reelset] = ordered
    return result


def _conditions(base_reel: str, *, force_freegame: bool = False, force_wincap: bool = False) -> dict:
    return {
        "reel_weights": {
            "basegame": {base_reel: 1},
            "freegame": {"FR0": 1},
        },
        "force_freegame": force_freegame,
        "force_wincap": force_wincap,
    }


class GameConfig(Config):
    """MathLock configuration and optimizer sampling distributions."""

    BOOST_PROBABILITY = 0.537
    STICKY_MULTIPLIER_CAP = 3
    LINE_MULTIPLIER_CAP = 20
    RETRIGGER_SPINS = 5
    MAX_FORCE_DRAWS = 100_000

    def __init__(self):
        super().__init__()
        self.game_id = "keris_wild"
        self.provider_number = 0
        self.provider_name = "kilara"
        self.working_name = "Keris Wilds: Pusaka Sang Raja"
        self.game_name = "keris_wilds"
        self.rtp = 0.967118
        self.wincap = 10000.0
        self.min_denomination = 0.1
        self.win_type = "lines"
        self.output_regular_json = True
        self.write_event_list = True
        self.construct_paths()

        self.num_reels = 5
        self.num_rows = [4] * self.num_reels
        # v2.2 RGS retune: every award is an exact 0.10x credit increment.
        self.paytable = {
            (5, "H1"): 14.0, (4, "H1"): 2.5, (3, "H1"): 0.6,
            (5, "H2"): 11.0, (4, "H2"): 2.0, (3, "H2"): 0.5,
            (5, "H3"): 8.0, (4, "H3"): 1.5, (3, "H3"): 0.4,
            (5, "H4"): 6.5, (4, "H4"): 1.2, (3, "H4"): 0.3,
            (5, "L1"): 3.2, (4, "L1"): 0.5, (3, "L1"): 0.2,
            (5, "L2"): 2.6, (4, "L2"): 0.5, (3, "L2"): 0.2,
            (5, "L3"): 2.0, (4, "L3"): 0.5, (3, "L3"): 0.1,
            (5, "L4"): 1.8, (4, "L4"): 0.4, (3, "L4"): 0.1,
            (5, "L5"): 1.4, (4, "L5"): 0.4, (3, "L5"): 0.1,
        }
        self.paylines = {idx: list(line) for idx, line in enumerate(PAYLINES, start=1)}
        self.include_padding = True
        self.special_symbols = {"wild": ["W"], "scatter": ["S"], "multiplier": ["W"]}
        self.freespin_triggers = {
            self.basegame_type: {count: 10 for count in range(3, 13)},
            self.freegame_type: {count: self.RETRIGGER_SPINS for count in range(3, 13)},
        }
        self.anticipation_triggers = {self.basegame_type: 2, self.freegame_type: 2}

        self.reels = load_locked_reels(Path(self.reels_path) / "keris_wilds_strips_v2.csv")
        self.padding_reels = {
            self.basegame_type: self.reels["BR0"],
            self.freegame_type: self.reels["FR0"],
        }

        self.bet_modes = self._build_bet_modes()

    def _build_bet_modes(self) -> list[BetMode]:
        mode_specs = {
            "base": (1.0, 0.967118, "BR0", [
                ("wincap", 0.00001, True, True, self.wincap),
                ("0", 0.68692, False, False, 0.0),
                ("freegame", 0.00455, True, False, None),
                ("basegame", 0.30852, False, False, None),
            ]),
            # Compliance retune: keep ante within 0.5pp of the base-mode RTP.
            "ante": (1.5, 0.962500, "BR1", [
                ("wincap", 0.00001, True, True, self.wincap),
                ("0", 0.68540, False, False, 0.0),
                ("freegame", 0.01140, True, False, None),
                ("basegame", 0.30319, False, False, None),
            ]),
            "bonus_buy": (72.0, 0.967703, "BR0", [
                ("wincap", 0.00002, True, True, self.wincap),
                ("0", 0.03754, True, False, 0.0),
                ("freegame", 0.96244, True, False, None),
            ]),
        }
        modes = []
        for name, (cost, rtp, base_reel, distributions) in mode_specs.items():
            modes.append(
                BetMode(
                    name=name,
                    cost=cost,
                    rtp=rtp,
                    max_win=self.wincap,
                    auto_close_disabled=False,
                    is_feature=name != "bonus_buy",
                    is_buybonus=name == "bonus_buy",
                    distributions=[
                        Distribution(
                            criteria=criteria,
                            quota=quota,
                            win_criteria=win_criteria,
                            conditions=_conditions(
                                base_reel,
                                force_freegame=force_freegame,
                                force_wincap=force_wincap,
                            ),
                        )
                        for criteria, quota, force_freegame, force_wincap, win_criteria in distributions
                    ],
                )
            )
        return modes
