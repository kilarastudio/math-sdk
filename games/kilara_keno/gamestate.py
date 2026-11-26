"""One round: book `sim` is draw pattern `sim % patterns` of the mode, with its own numbers."""

import random

from game_override import GameStateOverride
from game_calculations import all_patterns, HIT, KILAU


class GameState(GameStateOverride):
    _patterns = {}

    def patterns_for(self, picks: int, draws: int, kilau: int) -> list:
        key = (picks, draws, kilau)
        if key not in self._patterns:
            self._patterns[key] = all_patterns(picks, draws, kilau)
        return self._patterns[key]

    def deal_numbers(self, pattern: list, picks: int, kilau: int) -> tuple:
        """A board that shows this pattern: selected numbers, Kilau numbers and the draw, in order."""
        board = range(1, self.config.board_numbers + 1)
        selected = sorted(random.sample(board, picks))
        others = [n for n in board if n not in selected]
        marked = sorted(random.sample(others, kilau))
        plain = [n for n in others if n not in marked]
        hits = random.sample(selected, pattern.count(HIT))
        glows = random.sample(marked, pattern.count(KILAU))
        misses = random.sample(plain, len(pattern) - len(hits) - len(glows))
        numbers = [hits.pop() if ball == HIT else glows.pop() if ball == KILAU else misses.pop() for ball in pattern]
        return selected, marked, numbers

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            level, picks, draws, kilau = self.config.mode_parts(self.betmode)
            patterns = self.patterns_for(picks, draws, kilau)
            pattern = patterns[sim % len(patterns)]
            selected, marked, numbers = self.deal_numbers(pattern, picks, kilau)
            result = self.evaluate_pattern(pattern, picks, level)

            self.win_manager.update_spinwin(result["win"])
            self.win_manager.update_gametype_wins(self.gametype)
            self.book.add_event(
                {
                    "index": len(self.book.events),
                    "type": "draw",
                    "level": level,
                    "picks": picks,
                    "draws": draws,
                    "selected": selected,
                    "kilau": marked,
                    "numbers": numbers,
                    "pattern": pattern,
                    "hits": result["hits"],
                    "streak": result["streak"],
                    "kilauHits": result["kilau"],
                    "multiplier": result["multiplier"],
                    "pay": int(round(result["pay"] * 100)),
                }
            )
            self.evaluate_finalwin()
        self.imprint_wins()

    def run_freespin(self):
        pass
