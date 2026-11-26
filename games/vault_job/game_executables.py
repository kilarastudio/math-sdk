"""The crew: Driver, Safecracker, Muscle, Hacker."""

import random

from game_calculations import GameCalculations
from game_events import crew_start_event, crew_move_event, crew_expand_event, crew_hack_event, crew_board_event, crew_upgrade_event
from src.events.events import reveal_event, update_freespin_event, fs_trigger_event, win_info_event, set_win_event, set_total_event


class GameExecutables(GameCalculations):
    """Game specific executable functions."""

    def setup_sets(self):
        self.crew_set = set(self.config.crew)
        self.paying_set = {sym for (_, sym) in self.config.paytable if sym != "W"}

    def make_crew(self, name: str, mult: int):
        sym = self.create_symbol(name)
        sym.multiplier = mult
        return sym

    def place_sticky(self):
        """Put the sticky crew (The Job) on the freshly drawn board."""
        for (reel, row), (name, mult) in self.sticky.items():
            self.board[reel][row] = self.make_crew(name, mult)

    def drive(self):
        """The Job: every Driver moves one reel to the left, past cells other sticky crew hold; off reel 1 it leaves."""
        moves = []
        drivers = sorted((cell for cell, (name, _) in self.sticky.items() if name == "WD"), key=lambda c: c[0])
        for reel, row in drivers:
            _, mult = self.sticky.pop((reel, row))
            target = reel - 1
            while target >= 0 and (target, row) in self.sticky:
                target -= 1
            if target < 0:
                moves.append(((reel, row), None, mult))
            else:
                self.sticky[(target, row)] = ("WD", mult)
                moves.append(((reel, row), (target, row), mult))
        if moves:
            crew_move_event(self, moves)

    def crew_land(self):
        """Give newly landed crew their multipliers; in The Job, Drivers and Safecrackers stay."""
        in_job = self.gametype == self.config.freegame_type
        for reel, column in enumerate(self.board):
            for row, sym in enumerate(column):
                if sym.name in self.crew_set and (reel, row) not in self.sticky:
                    mults = self.config.job_crew_mult if in_job else self.config.crew_mult
                    if sym.name in mults:
                        sym.multiplier = mults[sym.name]
                    if in_job and sym.name in ("WD", "WC"):
                        self.sticky[(reel, row)] = (sym.name, sym.multiplier)
                        self.crew_landed[sym.name] += 1

    def muscle_expand(self):
        """Every Muscle fills its reel; cells that hold other crew keep them."""
        expands = []
        for reel, column in enumerate(self.board):
            rows = [row for row, sym in enumerate(column) if sym.name == "WM"]
            if not rows:
                continue
            expands.append((reel, rows[0]))
            for row, sym in enumerate(column):
                if sym.name not in self.crew_set and sym.name != "S":
                    column[row] = self.make_crew("WM", 1)
        if expands:
            crew_expand_event(self, expands)

    def hacker_copy(self):
        """Every Hacker takes the highest multiplier any other crew member carries (at least hacker_min)."""
        hackers = [(reel, row) for reel, column in enumerate(self.board) for row, sym in enumerate(column) if sym.name == "WH"]
        if not hackers:
            return
        best = max(
            [sym.multiplier or 1 for column in self.board for sym in column if sym.name in self.crew_set and sym.name != "WH"],
            default=1,
        )
        mult = max(best, self.config.hacker_min)
        for reel, row in hackers:
            self.board[reel][row].multiplier = mult
        crew_hack_event(self, [(reel, row, mult) for reel, row in hackers])

    def play_board(self, emit: bool = True):
        """Draw, let the crew act and pay the lines. Returns the board's win."""
        if self.gametype == self.config.freegame_type:
            self.drive()
            self.create_board_reelstrips()
            self.place_sticky()
        elif self.quiet:
            # Unforced measurement: the reels as they fall, scatters included.
            self.create_board_reelstrips()
        else:
            self.draw_board(emit_event=False)
        self.crew_land()
        self.get_special_symbols_on_board()
        if emit:
            reveal_event(self)
        self.muscle_expand()
        self.hacker_copy()
        if emit and any(sym.name in self.crew_set for column in self.board for sym in column):
            crew_board_event(self)
        self.win_data = self.evaluate_lines()
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        if emit:
            if self.win_manager.spin_win > 0:
                win_info_event(self)
                self.evaluate_wincap()
                set_win_event(self)
            set_total_event(self)
        elif self.win_manager.running_bet_win >= self.config.wincap:
            self.wincap_triggered = True
        if self.gametype == self.config.freegame_type:
            self.safecrackers_grow(emit)
        return self.win_data["totalWin"]

    def safecrackers_grow(self, emit: bool):
        """Sticky Safecrackers on a winning line step up their ladder."""
        on_wins = {(p["reel"], p["row"]) for w in self.win_data["wins"] for p in w["positions"]}
        upgrades = []
        for cell, (name, mult) in list(self.sticky.items()):
            if name == "WC" and cell in on_wins and mult < self.config.safecracker_ladder[-1]:
                new = self.next_step(mult)
                self.sticky[cell] = (name, new)
                upgrades.append((cell[0], cell[1], new))
        if upgrades:
            self.upgrades += len(upgrades)
            if emit:
                crew_upgrade_event(self, upgrades)

    def next_step(self, mult: int) -> int:
        """The next value on the Safecracker's ladder."""
        return next(m for m in self.config.safecracker_ladder if m > mult)

    def start_crew(self):
        """The Job starts with a Safecracker in place; the bigger buys add more crew."""
        placed = []
        for name, mult in self.config.job_start_crew + self.config.buy_start_crew.get(self.betmode, []):
            free = [
                (reel, row)
                for reel in self.config.start_reels
                for row in range(self.config.num_rows[reel])
                if (reel, row) not in self.sticky
            ]
            cell = random.choice(free)
            self.sticky[cell] = (name, mult)
            placed.append((cell[0], cell[1], name, mult))
        crew_start_event(self, placed)

    def retrigger(self, emit: bool = True):
        """Every scatter that lands in The Job adds one spin."""
        n = self.count_special_symbols("scatter")
        if n:
            self.tot_fs += n
            if emit:
                fs_trigger_event(self, freegame_trigger=True, basegame_trigger=False)

    def update_freespin(self) -> None:
        self.fs += 1
        update_freespin_event(self)
        self.win_manager.reset_spin_win()
        self.win_data = {}
