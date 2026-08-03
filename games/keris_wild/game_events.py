"""Keris-specific event adapters using the SDK's zero-based reel coordinates."""

from copy import deepcopy

from src.events.events import json_ready_sym


def _add(gamestate, event_type: str, **payload) -> None:
    gamestate.book.add_event(
        {"index": len(gamestate.book.events), "type": event_type, **payload}
    )


def _client_board(gamestate) -> list[list[dict]]:
    attributes = list(gamestate.config.special_symbols)
    board = [
        [json_ready_sym(symbol, attributes) for symbol in reel]
        for reel in gamestate.board
    ]
    if gamestate.config.include_padding:
        for reel in range(gamestate.config.num_reels):
            board[reel] = [json_ready_sym(gamestate.top_symbols[reel], attributes), *board[reel]]
            board[reel].append(json_ready_sym(gamestate.bottom_symbols[reel], attributes))
    return board


def wild_expand_event(gamestate, reels: list[int]) -> None:
    for reel in reels:
        _add(
            gamestate,
            "wildExpand",
            reel=reel,
            positions=[
                {"reel": reel, "row": row + int(gamestate.config.include_padding)}
                for row in range(gamestate.config.num_rows[reel])
            ],
        )


def respin_start_event(gamestate, held_reels: set[int]) -> None:
    _add(gamestate, "respinStart", heldReels=sorted(held_reels))


def respin_reveal_event(gamestate) -> None:
    _add(
        gamestate,
        "respinReveal",
        board=_client_board(gamestate),
        paddingPositions=deepcopy(gamestate.reel_positions),
        heldReels=sorted(gamestate.respin_held_reels),
    )


def respin_end_event(gamestate, respin_win: float) -> None:
    _add(gamestate, "respinEnd", respinWin=int(round(respin_win * 100)))


def first_spin_boost_event(gamestate, reel: int) -> None:
    _add(gamestate, "firstSpinBoost", reel=reel)


def sticky_wild_set_event(gamestate, reels: list[int]) -> None:
    for reel in reels:
        _add(gamestate, "stickyWildSet", reel=reel, multiplier=1)


def wild_multiplier_update_event(gamestate, changes: list[dict]) -> None:
    for change in changes:
        _add(gamestate, "wildMultiplierUpdate", **change)


def line_multiplier_events(gamestate, wins: list[dict]) -> None:
    for win in wins:
        if win["meta"].get("lineMultiplier", 1) > 1:
            _add(
                gamestate,
                "lineMultiplier",
                line=win["meta"]["lineIndex"],
                mult=win["meta"]["lineMultiplier"],
                wilds=deepcopy(win["meta"].get("stickyReels", [])),
            )


def big_win_tier_event(gamestate, win: float) -> None:
    tier = 3 if win >= 50 else 2 if win >= 25 else 1 if win >= 10 else None
    if tier is not None:
        _add(gamestate, "bigWinTier", tier=tier)


def accumulated_set_win_event(gamestate, amount: float) -> None:
    if not gamestate.wincap_triggered:
        _add(
            gamestate,
            "setWin",
            amount=int(round(amount * 100)),
            winLevel=gamestate.config.get_win_level(amount, "standard"),
        )


def free_spin_trigger_event(gamestate, positions: list[dict]) -> None:
    adjusted = [
        {"reel": pos["reel"], "row": pos["row"] + int(gamestate.config.include_padding)}
        for pos in positions
    ]
    _add(gamestate, "freeSpinTrigger", totalFs=gamestate.tot_fs, positions=adjusted)


def enter_bonus_event(gamestate, reason: str) -> None:
    _add(gamestate, "enterBonus", reason=reason)


def update_freespin_event(gamestate) -> None:
    _add(gamestate, "updateFreeSpin", amount=gamestate.fs, total=gamestate.tot_fs)


def free_spin_retrigger_event(gamestate, positions: list[dict]) -> None:
    adjusted = [
        {"reel": pos["reel"], "row": pos["row"] + int(gamestate.config.include_padding)}
        for pos in positions
    ]
    _add(
        gamestate,
        "freeSpinRetrigger",
        totalFs=gamestate.tot_fs,
        addedSpins=gamestate.config.RETRIGGER_SPINS,
        spinsLeft=gamestate.tot_fs - gamestate.fs,
        positions=adjusted,
    )


def free_spin_end_event(gamestate) -> None:
    _add(
        gamestate,
        "freeSpinEnd",
        amount=int(round(min(gamestate.win_manager.freegame_wins, gamestate.config.wincap) * 100)),
        winLevel=gamestate.config.get_win_level(gamestate.win_manager.freegame_wins, "endFeature"),
    )


def wincap_event(gamestate) -> None:
    _add(
        gamestate,
        "wincap",
        amount=int(round(gamestate.config.wincap * 100)),
        unit="wager",
    )
