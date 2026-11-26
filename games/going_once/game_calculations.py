"""Line wins with one wild."""

from src.executables.executables import Executables


class GameCalculations(Executables):
    """Game specific calculations for Going Once."""

    def evaluate_lines(self, mult: int = 1) -> dict:
        """Pay every line from the leftmost reel, 3 of a kind or more; W substitutes for paying symbols.

        A line of wilds alone pays as H1. Every win is multiplied by `mult` (a base game gavel).
        """
        names = [[sym.name for sym in reel] for reel in self.board]
        result = {"totalWin": 0.0, "wins": []}
        for index, line in self.config.paylines.items():
            first, count, lead, leading = None, 0, 0, True
            for reel, row in enumerate(line):
                name = names[reel][row]
                if name == "W":
                    count += 1
                    lead += leading
                elif first is None and name in self.paying_set:
                    first, leading = name, False
                    count += 1
                elif name == first:
                    count += 1
                else:
                    break
            pay, symbol, kind = 0.0, None, 0
            if first is not None and count >= 3:
                pay, symbol, kind = self.config.paytable.get((count, first), 0.0), first, count
            if lead >= 3 and self.config.paytable[(lead, "W")] > pay:
                pay, symbol, kind = self.config.paytable[(lead, "W")], "W", lead
            if pay <= 0:
                continue
            win = round(pay * mult, 2)
            result["totalWin"] += win
            result["wins"].append(
                {
                    "symbol": symbol,
                    "kind": kind,
                    "win": win,
                    "positions": [{"reel": reel, "row": line[reel]} for reel in range(kind)],
                    "meta": {"lineIndex": index, "multiplier": mult, "winWithoutMult": pay, "globalMult": mult, "lineMultiplier": 1},
                }
            )
        result["totalWin"] = round(result["totalWin"], 2)
        return result
