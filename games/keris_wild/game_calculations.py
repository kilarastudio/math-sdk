"""Pure Keris Wild math helpers kept local to the game."""

from __future__ import annotations

from copy import copy

from src.executables.executables import Executables


def _name(symbol) -> str:
    return symbol if isinstance(symbol, str) else symbol.name


class KerisWildMath:
    """Reference-compatible calculations without SDK multiplier side effects."""

    @staticmethod
    def scatter_pay(count: int) -> float:
        if count >= 6:
            return 25.0
        return {3: 2.5, 4: 6.0, 5: 12.0}.get(count, 0.0)

    @staticmethod
    def line_multiplier(
        span_length: int,
        sticky_multipliers: dict[int, int] | None,
        line_cap: int = 20,
    ) -> tuple[int, list[int]]:
        sticky_multipliers = sticky_multipliers or {}
        used_reels = sorted(reel for reel in sticky_multipliers if reel < span_length)
        multiplier = 1
        for reel in used_reels:
            multiplier *= sticky_multipliers[reel]
        return min(multiplier, line_cap), used_reels

    @staticmethod
    def evaluate_lines(board: list[list], config, sticky_multipliers: dict[int, int] | None = None) -> dict:
        result = {"totalWin": 0.0, "wins": []}
        for line_index, line in config.paylines.items():
            cells = [board[reel][line[reel]] for reel in range(config.num_reels)]
            paying_symbol = next(
                (_name(cell) for cell in cells if _name(cell) not in {"W", "S"}),
                None,
            )
            if paying_symbol is None:
                continue

            span = 0
            for cell in cells:
                symbol_name = _name(cell)
                if symbol_name == "S" or symbol_name not in {paying_symbol, "W"}:
                    break
                span += 1

            base_win = config.paytable.get((span, paying_symbol), 0.0)
            if base_win <= 0:
                continue
            multiplier, sticky_reels = KerisWildMath.line_multiplier(
                span,
                sticky_multipliers,
                getattr(config, "LINE_MULTIPLIER_CAP", 20),
            )
            win = round(base_win * multiplier, 10)
            result["totalWin"] += win
            result["wins"].append(
                {
                    "symbol": paying_symbol,
                    "kind": span,
                    "win": win,
                    "positions": [{"reel": reel, "row": line[reel]} for reel in range(span)],
                    "meta": {
                        "lineIndex": line_index,
                        "multiplier": multiplier,
                        "winWithoutMult": base_win,
                        "globalMult": 1,
                        "lineMultiplier": multiplier,
                        "stickyReels": sticky_reels,
                    },
                }
            )
        result["totalWin"] = round(result["totalWin"], 10)
        return result

    @staticmethod
    def expand_wild_reels(board: list[list], symbol_factory=None) -> tuple[list[list], list[int]]:
        expanded = [list(reel) for reel in board]
        expanded_reels = [reel for reel in (1, 2, 3) if any(_name(symbol) == "W" for symbol in board[reel])]
        for reel in expanded_reels:
            replacement = "W" if symbol_factory is None else symbol_factory
            expanded[reel] = [replacement() if callable(replacement) else replacement for _ in board[reel]]
        return expanded, expanded_reels

    @staticmethod
    def increment_sticky_multipliers(
        sticky_multipliers: dict[int, int],
        wins: list[dict],
        multiplier_cap: int = 3,
    ) -> tuple[dict[int, int], list[dict]]:
        updated = copy(sticky_multipliers)
        paid_reels = {
            position["reel"]
            for win in wins
            if win["win"] > 0
            for position in win["positions"]
        }
        changes = []
        for reel in sorted(updated):
            old_multiplier = updated[reel]
            if reel in paid_reels and old_multiplier < multiplier_cap:
                updated[reel] += 1
                changes.append(
                    {
                        "reel": reel,
                        "oldMultiplier": old_multiplier,
                        "newMultiplier": updated[reel],
                    }
                )
        return updated, changes


class GameCalculations(Executables):
    """Game inheritance hook plus pure helper access."""

    math = KerisWildMath
