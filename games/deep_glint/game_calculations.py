"""Scatter pays evaluated through the Glint Spot grid."""

from collections import defaultdict
from src.executables.executables import Executables
from src.calculations.scatter import Scatter


class GameCalculations(Executables):
    """Game specific calculations for DEEP GLINT."""

    def evaluate_scatter_with_glint(self) -> dict:
        """Pay every symbol with 8+ copies on the board, multiplied by the lit spots under it.

        A symbol win's multiplier combines the lit spots (value 2+) under its positions,
        by sum or max per the glint rule, or is 1x when none is lit. Primed spots (value 1) add nothing.
        """
        board = self.board
        return_data = {"totalWin": 0, "wins": []}
        rows_for_overlay = []
        symbols_on_board = defaultdict(list)
        for reel_idx, reel in enumerate(board):
            for row_idx, symbol in enumerate(reel):
                symbols_on_board[symbol.name].append({"reel": reel_idx, "row": row_idx})

        total_win = 0.0
        for sym, positions in symbols_on_board.items():
            win_size = len(positions)
            if (win_size, sym) not in self.config.paytable:
                continue
            lit = [self.glint[p["reel"]][p["row"]] for p in positions if self.glint[p["reel"]][p["row"]] >= 2]
            combine = sum if self.config.glint_rule["combine"] == "sum" else max
            symbol_mult = combine(lit) if lit else 1
            for p in positions:
                board[p["reel"]][p["row"]].explode = True

            base_win = self.config.paytable[(win_size, sym)]
            overlay_position = Scatter.get_central_scatter_position(
                rows_for_overlay, positions, len(board), len(board[0])
            )
            rows_for_overlay.append(overlay_position[1])
            symbol_win = base_win * symbol_mult
            total_win += symbol_win
            return_data["wins"].append(
                {
                    "symbol": sym,
                    "win": symbol_win,
                    "positions": positions,
                    "meta": {
                        "globalMult": 1,
                        "clusterMult": symbol_mult,
                        "winWithoutMult": base_win,
                        "overlay": {"reel": overlay_position[0], "row": overlay_position[1]},
                    },
                }
            )

        return_data["totalWin"] = total_win
        return return_data
