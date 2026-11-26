"""Events beyond the SDK's standard ones. Rows include the padding row, like winInfo."""

CREW_MOVE = "crewMove"
CREW_EXPAND = "crewExpand"
CREW_HACK = "crewHack"
CREW_BOARD = "crewBoard"
CREW_UPGRADE = "crewUpgrade"
CREW_START = "crewStart"


def _cell(gamestate, reel, row):
    padding = 1 if gamestate.config.include_padding else 0
    return {"reel": reel, "row": row + padding}


def _add(gamestate, event: dict):
    if getattr(gamestate, "quiet", False):
        return
    event["index"] = len(gamestate.book.events)
    gamestate.book.add_event(event)


def crew_move_event(gamestate, moves: list):
    """The Job: Drivers drive one reel to the left before the reels spin. `to` is None when one leaves."""
    _add(
        gamestate,
        {
            "type": CREW_MOVE,
            "moves": [
                {
                    "from": _cell(gamestate, *start),
                    "to": None if end is None else _cell(gamestate, *end),
                    "multiplier": mult,
                }
                for start, end, mult in moves
            ],
        },
    )


def crew_expand_event(gamestate, reels: list):
    """A Muscle fills its reel with Muscle wilds (cells held by other crew keep them)."""
    _add(gamestate, {"type": CREW_EXPAND, "reels": [{"reel": reel, "from": _cell(gamestate, reel, row)} for reel, row in reels]})


def crew_hack_event(gamestate, hacks: list):
    """A Hacker copies the highest multiplier on the board."""
    _add(gamestate, {"type": CREW_HACK, "hacks": [{"cell": _cell(gamestate, reel, row), "multiplier": m} for reel, row, m in hacks]})


def crew_board_event(gamestate):
    """Every crew member on the board as the lines are paid: cell, role, multiplier, sticky."""
    crew = []
    for reel, column in enumerate(gamestate.board):
        for row, sym in enumerate(column):
            if sym.name in gamestate.crew_set:
                crew.append(
                    {
                        "cell": _cell(gamestate, reel, row),
                        "crew": sym.name,
                        "multiplier": sym.multiplier or 1,
                        "sticky": (reel, row) in gamestate.sticky,
                    }
                )
    _add(gamestate, {"type": CREW_BOARD, "crew": crew})


def crew_upgrade_event(gamestate, upgrades: list):
    """The Job: Safecrackers that took part in a win double their multiplier."""
    _add(
        gamestate,
        {"type": CREW_UPGRADE, "upgrades": [{"cell": _cell(gamestate, reel, row), "multiplier": m} for reel, row, m in upgrades]},
    )


def crew_start_event(gamestate, placed: list):
    """The Job begins: the crew it starts with take their cells (sticky)."""
    _add(
        gamestate,
        {"type": CREW_START, "crew": [{"cell": _cell(gamestate, reel, row), "crew": name, "multiplier": m} for reel, row, name, m in placed]},
    )
