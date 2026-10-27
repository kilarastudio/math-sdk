from copy import deepcopy

UPDATE_GLINT = "updateGlint"
GLINT_STRIKE = "glintStrike"


def update_glint_event(gamestate):
    """Send the whole Glint Spot grid, indexed [reel][row] without padding rows."""
    event = {
        "index": len(gamestate.book.events),
        "type": UPDATE_GLINT,
        "glint": deepcopy(gamestate.glint),
    }
    gamestate.book.add_event(event)


def glint_strike_event(gamestate, spots: list):
    """The character lights spots on the revealed board, before it is evaluated.

    Spot rows include the padding row, like winInfo positions.
    """
    padding = 1 if gamestate.config.include_padding else 0
    event = {
        "index": len(gamestate.book.events),
        "type": GLINT_STRIKE,
        "spots": [{"reel": s["reel"], "row": s["row"] + padding, "value": s["value"]} for s in spots],
        "glint": deepcopy(gamestate.glint),
    }
    gamestate.book.add_event(event)
