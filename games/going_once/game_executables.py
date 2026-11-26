"""The base game's gavel and the auction."""

import random

from game_calculations import GameCalculations
from game_events import (
    base_gavel_event,
    auction_start_event,
    auction_respin_event,
    buyer_collect_event,
    gavel_strike_event,
    auction_end_event,
    last_bid_event,
)
from src.calculations.statistics import get_random_outcome
from src.events.events import reveal_event, win_info_event, set_win_event, set_total_event


class GameExecutables(GameCalculations):
    """Game specific executable functions."""

    def setup_sets(self):
        self.paying_set = {sym for (_, sym) in self.config.paytable if sym != "W"}
        self.cells = [(reel, row) for reel in range(self.config.num_reels) for row in range(self.config.num_rows[reel])]

    def assign_lot(self, sym):
        table = "auction" if self.gametype == self.config.freegame_type else "base"
        sym.prize = get_random_outcome(self.config.lot_values[table])

    def lots_on_board(self) -> list:
        return [(reel, row) for reel, row in self.cells if self.board[reel][row].name == "P"]

    def draw_base_board(self):
        """Draw the opening board for the round's criteria."""
        trigger = self.config.auction_trigger
        start = self.config.buy_start.get(self.betmode)
        if self.unforced:
            self.create_board_reelstrips()
        elif start is not None:
            # A bought round: a board with fewer lots than the buy brings, then lots on random
            # cells (not wilds or gavels) until it holds exactly that many.
            self.create_board_reelstrips()
            while len(self.lots_on_board()) > start["lots"]:
                self.create_board_reelstrips()
            free = [c for c in self.cells if self.board[c[0]][c[1]].name in self.paying_set]
            for reel, row in random.sample(free, start["lots"] - len(self.lots_on_board())):
                self.board[reel][row] = self.create_symbol("P")
        elif self.get_current_distribution_conditions()["force_freegame"]:
            self.create_board_reelstrips()
            while len(self.lots_on_board()) < trigger:
                self.create_board_reelstrips()
        else:
            self.create_board_reelstrips()
            while len(self.lots_on_board()) >= trigger:
                self.create_board_reelstrips()

    def play_board(self):
        """The base game spin: draw, a gavel multiplies, lines pay. Returns the win."""
        self.draw_base_board()
        self.get_special_symbols_on_board()
        if not self.quiet:
            reveal_event(self)
        mult = 1
        gavels = [(reel, row) for reel, row in self.cells if self.board[reel][row].name == "G"]
        if gavels:
            mult = self.config.base_gavel_mult
            base_gavel_event(self, gavels[0], mult)
        self.win_data = self.evaluate_lines(mult)
        self.win_manager.update_spinwin(self.win_data["totalWin"])
        if not self.quiet:
            if self.win_manager.spin_win > 0:
                win_info_event(self)
                self.evaluate_wincap()
                set_win_event(self)
            set_total_event(self)
        return self.win_data["totalWin"]

    def auction_triggered(self) -> bool:
        return len(self.lots_on_board()) >= self.config.auction_trigger

    def strike(self, cell):
        for key in self.lots:
            self.lots[key] *= 2
        self.gavels += 1
        gavel_strike_event(self, cell)

    def run_auction(self):
        """Hold & win: lots stay, empty cells respin; anything landing resets the respins."""
        self.reset_fs_spin()
        self.lots = {(reel, row): self.board[reel][row].prize for reel, row in self.lots_on_board()}
        self.respins_left = self.config.respins
        self.tot_fs = self.respins_left
        auction_start_event(self)
        start = self.config.buy_start.get(self.betmode)
        for _ in range(start["gavels"] if start else 0):
            self.strike(None)
        draw = self.config.respin_draw
        p_lot, p_gavel, p_buyer = draw["P"], draw["P"] + draw["G"], draw["P"] + draw["G"] + draw["B"]
        size = len(self.cells)
        number = 0
        while self.respins_left > 0 and len(self.lots) < size:
            number += 1
            self.respins_left -= 1
            landed, buyers, gavels = [], [], []
            for cell in self.cells:
                if cell in self.lots:
                    continue
                r = random.randrange(1000)
                if r < p_lot:
                    value = get_random_outcome(self.config.lot_values["auction"])
                    self.lots[cell] = value
                    landed.append((cell, "P", value))
                elif r < p_gavel:
                    gavels.append(cell)
                    landed.append((cell, "G", 0))
                elif r < p_buyer:
                    buyers.append(cell)
                    landed.append((cell, "B", 0))
            if landed:
                self.respins_left = self.config.respins
            auction_respin_event(self, number, landed)
            for reel, row in buyers:
                value = max(1, sum(v for (r, _), v in self.lots.items() if r == reel))
                self.lots[(reel, row)] = value
                self.buyers += 1
                buyer_collect_event(self, (reel, row), value)
            for cell in gavels:
                self.strike(cell)
        self.respins_played = number
        total = sum(self.lots.values())
        bid = get_random_outcome(self.config.last_bid)
        last_bid_event(self, bid, total)
        total *= bid
        self.bid = bid
        full = len(self.lots) == size
        if full:
            total *= self.config.full_house_mult
        self.full_house = full
        self.win_manager.update_spinwin(total)
        auction_end_event(self, total, full)
        if not self.quiet:
            self.evaluate_wincap()
            set_win_event(self)
            set_total_event(self)
        self.win_manager.update_gametype_wins(self.gametype)
        if not self.quiet:
            self.end_freespin()
