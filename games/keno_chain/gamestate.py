"""One round: book `sim` is round `sim % rounds` of the mode, with its own numbers."""

import random

from game_override import GameStateOverride
from game_calculations import mode_rounds, HIT, KILAU


class GameState(GameStateOverride):
    _rounds = {}

    def rounds_for(self, mode: str) -> list:
        if mode not in self._rounds:
            _, picks, draws, options = self.config.mode_parts(mode)
            self._rounds[mode] = mode_rounds(picks, draws, options, self.config.board_numbers)
        return self._rounds[mode]

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
            level, picks, draws, _ = self.config.mode_parts(self.betmode)
            rounds = self.rounds_for(self.betmode)
            pattern, kilau, _ = rounds[sim % len(rounds)]
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
                    # a Kilau round: this level marks 1 number, this round marks 3
                    "kilauRound": kilau > self.config.level_kilau[level],
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
