"""Keris Wild board, wallet, expansion, and feature operations."""

from __future__ import annotations

from copy import deepcopy

from src.events.events import reveal_event, set_total_event, set_win_event, win_info_event

from game_calculations import GameCalculations, KerisWildMath
from game_events import (
    accumulated_set_win_event,
    big_win_tier_event,
    first_spin_boost_event,
    line_multiplier_events,
    respin_end_event,
    respin_reveal_event,
    respin_start_event,
    sticky_wild_set_event,
    wild_expand_event,
    wild_multiplier_update_event,
    wincap_event,
)


WINCAP_FS_STOPS = [
    [252, 57, 0, 84, 58],
    [49, 0, 208, 160, 94],
    [77, 220, 196, 229, 115],
    [213, 146, 8, 12, 236],
    [222, 268, 46, 186, 52],
    [259, 147, 190, 285, 80],
    [145, 171, 175, 244, 243],
    [23, 181, 298, 291, 267],
    [196, 29, 105, 173, 104],
    [92, 94, 16, 15, 78],
]
WINCAP_BASE_STOPS = {
    "BR0": [[4, 84, 3, 113, 16], [172, 93, 293, 234, 194]],
    "BR1": [[5, 121, 13, 15, 11], [172, 93, 293, 234, 194]],
}


class GameExecutables(GameCalculations):
    """Operations composed by the base and free-spin state machines."""

    def prepare_forced_wincap(self) -> None:
        conditions = self.get_current_distribution_conditions()
        if not conditions.get("force_wincap"):
            return
        if self.betmode != "bonus_buy":
            reelset = self.base_reelset()
            self.forced_base_stops = deepcopy(WINCAP_BASE_STOPS[reelset])
        self.forced_fs_stops = deepcopy(WINCAP_FS_STOPS)
        self.forced_boost = (0.34988497477779557, 1)

    def base_reelset(self) -> str:
        return "BR1" if self.betmode == "ante" else "BR0"

    def _next_stops(self, reelset: str) -> list[int]:
        queue = self.forced_fs_stops if reelset == "FR0" else self.forced_base_stops
        if queue:
            return queue.pop(0)
        return self.rng.integers(0, len(self.config.reels[reelset][0]), size=5).tolist()

    def draw_keris_board(self, reelset: str, stops: list[int] | None = None, emit_event: bool = False) -> None:
        """Draw one window using the locked `(stop + row) mod 300` contract."""
        strips = self.config.reels[reelset]
        stops = list(stops) if stops is not None else self._next_stops(reelset)
        if len(stops) != self.config.num_reels:
            raise ValueError("Keris Wild requires exactly five reel stops")

        self.reelstrip_id = reelset
        self.reelstrip = strips
        self.reel_positions = stops
        self.padding_position = [
            (stops[reel] + self.config.num_rows[reel] + 1) % len(strips[reel])
            for reel in range(self.config.num_reels)
        ]
        self.anticipation = [0] * self.config.num_reels
        self.board = []
        self.top_symbols = []
        self.bottom_symbols = []
        for reel in range(self.config.num_reels):
            length = len(strips[reel])
            self.board.append(
                [self.create_symbol(strips[reel][(stops[reel] + row) % length]) for row in range(4)]
            )
            self.top_symbols.append(self.create_symbol(strips[reel][(stops[reel] - 1) % length]))
            self.bottom_symbols.append(self.create_symbol(strips[reel][(stops[reel] + 4) % length]))
        self.get_special_symbols_on_board()
        if emit_event:
            reveal_event(self)

    def scatter_snapshot(self, excluded_reels: set[int] | None = None) -> dict:
        excluded_reels = excluded_reels or set()
        positions = [
            {"reel": reel, "row": row}
            for reel in range(self.config.num_reels)
            if reel not in excluded_reels
            for row, symbol in enumerate(self.board[reel])
            if symbol.name == "S"
        ]
        return {
            "count": len(positions),
            "positions": positions,
            "pay": KerisWildMath.scatter_pay(len(positions)),
        }

    def _set_wild_reel(self, reel: int, multiplier: int = 1) -> None:
        wilds = []
        for _ in range(self.config.num_rows[reel]):
            symbol = self.create_symbol("W")
            symbol.assign_attribute({"multiplier": multiplier})
            wilds.append(symbol)
        self.board[reel] = wilds

    def expand_current_wilds(self, excluded_reels: set[int] | None = None) -> list[int]:
        excluded_reels = excluded_reels or set()
        reels = [
            reel
            for reel in (1, 2, 3)
            if reel not in excluded_reels and any(symbol.name == "W" for symbol in self.board[reel])
        ]
        for reel in reels:
            self._set_wild_reel(reel)
        self.get_special_symbols_on_board()
        return reels

    def apply_held_reels(self, held_reels: set[int], multipliers: dict[int, int] | None = None) -> None:
        multipliers = multipliers or {}
        for reel in held_reels:
            self._set_wild_reel(reel, multipliers.get(reel, 1))
        self.get_special_symbols_on_board()

    def scatter_win_data(self, snapshot: dict) -> dict:
        if snapshot["pay"] <= 0:
            return {"totalWin": 0.0, "wins": []}
        return {
            "totalWin": snapshot["pay"],
            "wins": [
                {
                    "symbol": "S",
                    "kind": snapshot["count"],
                    "win": snapshot["pay"],
                    "positions": deepcopy(snapshot["positions"]),
                    "meta": {
                        "multiplier": 1,
                        "winWithoutMult": snapshot["pay"],
                        "globalMult": 1,
                        "lineMultiplier": 1,
                        "stickyReels": [],
                    },
                }
            ],
        }

    @staticmethod
    def merge_win_data(*parts: dict) -> dict:
        return {
            "totalWin": sum(part["totalWin"] for part in parts),
            "wins": [deepcopy(win) for part in parts for win in part["wins"]],
        }

    def cap_win_data(self, win_data: dict) -> dict:
        remaining = max(0.0, self.config.wincap - self.win_manager.running_bet_win)
        capped_wins = []
        credited = 0.0
        for original in win_data["wins"]:
            if remaining <= 0:
                break
            win = deepcopy(original)
            amount = min(float(win["win"]), remaining)
            if amount <= 0:
                continue
            win["win"] = round(amount, 10)
            capped_wins.append(win)
            credited += amount
            remaining -= amount
        return {"totalWin": round(credited, 10), "wins": capped_wins}

    def apply_win_data(
        self,
        win_data: dict,
        *,
        emit_set_win: bool = True,
        emit_total: bool = True,
    ) -> float:
        """Credit one reveal, then emit wallet events in SDK units."""
        self.win_data = self.cap_win_data(win_data)
        self.win_manager.reset_spin_win()
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        for win in self.win_data["wins"]:
            if "lineIndex" in win.get("meta", {}):
                self.record(
                    {
                        "kind": win["kind"],
                        "symbol": win["symbol"],
                        "mult": win["meta"]["lineMultiplier"],
                        "gametype": self.gametype,
                    }
                )

        if self.win_data["totalWin"] > 0:
            win_info_event(self)
            line_multiplier_events(self, self.win_data["wins"])
            big_win_tier_event(self, self.win_data["totalWin"])
        self.win_manager.update_gametype_wins(self.gametype)
        self.evaluate_wincap()
        if self.win_data["totalWin"] > 0 and emit_set_win:
            set_win_event(self)
        if emit_total:
            set_total_event(self)
        return self.win_data["totalWin"]

    def evaluate_wincap(self) -> bool:
        if self.win_manager.running_bet_win >= self.config.wincap and not self.wincap_triggered:
            self.wincap_triggered = True
            wincap_event(self)
            return True
        return False

    def resolve_base_reveal(self, scatter: dict, *, has_respin: bool = False) -> float:
        expanded_reels = self.expand_current_wilds()
        if expanded_reels:
            wild_expand_event(self, expanded_reels)
        line_data = KerisWildMath.evaluate_lines(self.board, self.config)
        return self.apply_win_data(
            self.merge_win_data(line_data, self.scatter_win_data(scatter)),
            emit_total=not has_respin,
        )

    def resolve_base_respin(self, held_reels: set[int], initial_win: float = 0.0) -> float:
        self.respin_held_reels = set(held_reels)
        respin_start_event(self, held_reels)
        self.draw_keris_board(self.base_reelset())
        self.apply_held_reels(held_reels)
        respin_reveal_event(self)
        new_reels = self.expand_current_wilds(excluded_reels=held_reels)
        if new_reels:
            wild_expand_event(self, new_reels)
        win = self.apply_win_data(
            KerisWildMath.evaluate_lines(self.board, self.config),
            emit_set_win=False,
            emit_total=False,
        )
        respin_end_event(self, win)
        accumulated_set_win_event(self, initial_win + win)
        set_total_event(self)
        return win

    def apply_first_spin_boost(self) -> int | None:
        if self.forced_boost is not None:
            roll, reel = self.forced_boost
            self.forced_boost = None
        else:
            roll = float(self.rng.random())
            reel = int(self.rng.integers(0, 3)) + 1 if roll < self.config.BOOST_PROBABILITY else None
        if roll >= self.config.BOOST_PROBABILITY:
            return None
        self._set_wild_reel(reel)
        first_spin_boost_event(self, reel)
        return reel

    def resolve_freegame_reveal(self, scatter: dict, first_spin: bool) -> float:
        if first_spin:
            self.apply_first_spin_boost()
        expanded = self.expand_current_wilds(excluded_reels=self.sticky_reels)
        new_sticky = sorted(set(expanded) - self.sticky_reels)
        self.sticky_reels.update(new_sticky)
        for reel in new_sticky:
            self.sticky_multipliers[reel] = 1
        for reel in self.sticky_reels:
            self._set_wild_reel(reel, self.sticky_multipliers[reel])
        if expanded:
            wild_expand_event(self, expanded)
        if new_sticky:
            sticky_wild_set_event(self, new_sticky)

        wins = KerisWildMath.evaluate_lines(
            self.board,
            self.config,
            sticky_multipliers=self.sticky_multipliers,
        )
        credited = self.apply_win_data(wins)
        if not self.wincap_triggered:
            self.sticky_multipliers, changes = KerisWildMath.increment_sticky_multipliers(
                self.sticky_multipliers,
                self.win_data["wins"],
                self.config.STICKY_MULTIPLIER_CAP,
            )
            wild_multiplier_update_event(self, changes)
        return credited
