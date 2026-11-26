from copy import deepcopy

RABBITS_ENTER = "rabbitsEnter"
RABBIT_HOP = "rabbitHop"
RABBIT_FLOP = "rabbitFlop"
UPDATE_FOOTPRINTS = "updateFootprints"


def _cell(gamestate, pos):
    """A board position as the frontend reads it: rows include the padding row, like winInfo."""
    if pos is None:
        return None
    padding = 1 if gamestate.config.include_padding else 0
    return {"reel": pos[0], "row": pos[1] + padding}


def update_footprints_event(gamestate):
    """Send the whole footprint grid, indexed [reel][row] without padding rows (0 = no footprint)."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": UPDATE_FOOTPRINTS,
            "footprints": deepcopy(gamestate.footprints),
        }
    )


def rabbits_enter_event(gamestate):
    """Flop Time starts: the rabbits take their cells, each on a fresh 2x footprint."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": RABBITS_ENTER,
            "rabbits": [_cell(gamestate, pos) for pos in gamestate.rabbits],
            "footprints": deepcopy(gamestate.footprints),
        }
    )


def rabbit_hop_event(gamestate, rabbit: int, start, end):
    """A rabbit hops and leaves a footprint where it lands. `from` is null for the base game's
    reveal hop (the rabbit may be anywhere). `footprints` is the grid afterwards."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": RABBIT_HOP,
            "rabbit": rabbit,
            "from": _cell(gamestate, start),
            "to": _cell(gamestate, end),
            "value": gamestate.footprints[end[0]][end[1]],
            "footprints": deepcopy(gamestate.footprints),
        }
    )


def rabbit_flop_event(gamestate, rabbit: int, at):
    """A rabbit flops where it is and every footprint on the board doubles."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": RABBIT_FLOP,
            "rabbit": rabbit,
            "at": _cell(gamestate, at),
            "footprints": deepcopy(gamestate.footprints),
        }
    )
