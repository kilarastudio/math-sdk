"""Events beyond the SDK's standard ones."""

from copy import deepcopy

TERRITORY = "territory"


def territory_event(gamestate, reason: str):
    """The whole territory: `marks` [reel][row] is 0 none, 1 phoenix, 2 dragon, 3 clash; `clash`
    holds each Clash cell's value (0 elsewhere). Rows exclude the padding rows. `reason` is
    "marked" after a winning cascade, "start" when a bought Duel begins with Clash cells. The
    territory is empty at every base round's reveal and when the Duel begins; no event says so."""
    if getattr(gamestate, "quiet", False):
        return
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": TERRITORY,
            "reason": reason,
            "marks": deepcopy(gamestate.marks),
            "clash": deepcopy(gamestate.clash),
        }
    )
