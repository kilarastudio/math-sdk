"""Round orchestration for the Keris Wild v2.2 RGS MathLock."""

from src.events.events import final_win_event, reveal_event

from game_calculations import KerisWildMath
from game_events import (
    enter_bonus_event,
    free_spin_end_event,
    free_spin_retrigger_event,
    free_spin_trigger_event,
    update_freespin_event,
)
from game_override import GameStateOverride


class GameState(GameStateOverride):
    """Resolve one paid round, including its optional respin and free spins."""

    def run_spin(self, sim, simulation_seed=None):
        self.reset_seed(sim, seed_override=simulation_seed)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.prepare_forced_wincap()
            if self.betmode == "bonus_buy":
                self.start_freespins([], reason="bonusBuy")
            else:
                self.run_basegame()
            self.update_final_win()
            final_win_event(self)
            self.check_repeat()
        self.imprint_wins()

    def run_basegame(self) -> None:
        reelset = self.base_reelset()
        conditions = self.get_current_distribution_conditions()
        for _ in range(self.config.MAX_FORCE_DRAWS):
            self.draw_keris_board(reelset)
            scatter = self.scatter_snapshot()
            wants_feature = conditions.get("force_freegame", False)
            if wants_feature == (scatter["count"] >= 3):
                break
        else:
            raise RuntimeError(
                f"Unable to draw a valid {self.criteria!r} base board after "
                f"{self.config.MAX_FORCE_DRAWS} attempts"
            )

        self.initial_scatter = scatter
        reveal_event(self)
        expanded_reels = [
            reel for reel in (1, 2, 3) if any(symbol.name == "W" for symbol in self.board[reel])
        ]
        initial_win = self.resolve_base_reveal(scatter, has_respin=bool(expanded_reels))
        if expanded_reels and not self.wincap_triggered:
            self.resolve_base_respin(set(expanded_reels), initial_win=initial_win)

        if scatter["count"] >= 3 and not self.wincap_triggered:
            self.record({"kind": scatter["count"], "symbol": "scatter", "gametype": self.gametype})
            self.start_freespins(scatter["positions"], reason="scatter")

    def start_freespins(self, trigger_positions: list[dict], reason: str) -> None:
        self.tot_fs = 10
        free_spin_trigger_event(self, trigger_positions)
        enter_bonus_event(self, reason)
        self.reset_fs_spin()
        self.run_freespin()

    def run_freespin(self):
        while self.fs < self.tot_fs and not self.wincap_triggered:
            update_freespin_event(self)
            first_spin = self.fs == 0
            sticky_at_start = set(self.sticky_reels)
            self.fs += 1
            self.draw_keris_board("FR0")
            scatter = self.scatter_snapshot(excluded_reels=sticky_at_start)
            self.apply_held_reels(sticky_at_start, self.sticky_multipliers)
            reveal_event(self)
            self.resolve_freegame_reveal(scatter, first_spin=first_spin)

            if scatter["count"] >= 3 and not self.wincap_triggered:
                self.tot_fs += self.config.RETRIGGER_SPINS
                self.record(
                    {"kind": scatter["count"], "symbol": "scatter", "gametype": self.gametype}
                )
                free_spin_retrigger_event(self, scatter["positions"])
        free_spin_end_event(self)
