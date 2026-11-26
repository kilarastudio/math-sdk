"""Line wins with crew wilds."""

from src.executables.executables import Executables


class GameCalculations(Executables):
    """Game specific calculations for The Vault Job."""

    def crew_mult_at(self, reel: int, row: int) -> int:
        sym = self.board[reel][row]
        return sym.multiplier or 1

    def evaluate_lines(self) -> dict:
        """Pay every line from the leftmost reel, 3 of a kind or more; crew substitute for any paying symbol.

        A line made only of crew pays as H1. A win is multiplied by the sum of the multipliers of
        the crew on its winning positions that carry more than x1 (none: x1).
        """
        crew = self.crew_set
        names = [[sym.name for sym in reel] for reel in self.board]
        result = {"totalWin": 0.0, "wins": []}
        for index, line in self.config.paylines.items():
            first = None
            count = 0
            for reel, row in enumerate(line):
                name = names[reel][row]
                if name in crew:
                    count += 1
                elif first is None and name in self.paying_set:
                    first = name
                    count += 1
                elif name == first:
                    count += 1
                else:
                    break
            # Leading crew alone (before the first paying symbol) may pay more as a crew line.
            lead = 0
            for reel, row in enumerate(line):
                if names[reel][row] in crew:
                    lead += 1
                else:
                    break
            pay, symbol, kind = 0.0, None, 0
            if first is not None and count >= 3:
                pay, symbol, kind = self.config.paytable.get((count, first), 0.0), first, count
            if lead >= 3 and self.config.paytable[(lead, "W")] > pay:
                pay, symbol, kind = self.config.paytable[(lead, "W")], "W", lead
            if pay <= 0:
                continue
            positions = [{"reel": reel, "row": line[reel]} for reel in range(kind)]
            mult = sum(m for m in (self.crew_mult_at(p["reel"], p["row"]) for p in positions) if m > 1)
            mult = max(mult, 1)
            win = round(pay * mult, 2)
            result["totalWin"] += win
            result["wins"].append(
                {
                    "symbol": symbol,
                    "kind": kind,
                    "win": win,
                    "positions": positions,
                    "meta": {
                        "lineIndex": index,
                        "multiplier": mult,
                        "winWithoutMult": pay,
                        "globalMult": 1,
                        "lineMultiplier": mult,
                    },
                }
            )
        result["totalWin"] = round(result["totalWin"], 2)
        return result
