from copy import deepcopy

UPDATE_GLINT = "updateGlint"
GLINT_STRIKE = "glintStrike"
GLINT_GAZE = "glintGaze"


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


def glint_gaze_event(gamestate, eyes: list, reels: list):
    """The dragon's gaze doubles every spot on the listed reels.

    `eyes` are the scatters that just landed and caused it (rows include the padding row, like
    winInfo positions); it is empty when the gaze is the hoard mode's sweep. `reels` lists one
    reel per gaze, so a reel named twice was doubled twice. `glint` is the grid afterwards.
    """
    padding = 1 if gamestate.config.include_padding else 0
    event = {
        "index": len(gamestate.book.events),
        "type": GLINT_GAZE,
        "eyes": [{"reel": e["reel"], "row": e["row"] + padding} for e in eyes],
        "reels": list(reels),
        "glint": deepcopy(gamestate.glint),
    }
    gamestate.book.add_event(event)
