"""Events beyond the SDK's standard ones. Rows include the padding row, like winInfo."""

BASE_GAVEL = "baseGavel"
AUCTION_START = "auctionStart"
AUCTION_RESPIN = "auctionRespin"
GAVEL_STRIKE = "gavelStrike"
BUYER_COLLECT = "buyerCollect"
AUCTION_END = "auctionEnd"
LAST_BID = "lastBid"


def _cell(gamestate, reel, row):
    padding = 1 if gamestate.config.include_padding else 0
    return {"reel": reel, "row": row + padding}


def _add(gamestate, event: dict):
    if getattr(gamestate, "quiet", False):
        return
    event["index"] = len(gamestate.book.events)
    gamestate.book.add_event(event)


def _lots(gamestate):
    return [{"cell": _cell(gamestate, reel, row), "value": value} for (reel, row), value in sorted(gamestate.lots.items())]


def base_gavel_event(gamestate, cell, mult):
    """Base game: a gavel on the board multiplies the spin's line wins."""
    _add(gamestate, {"type": BASE_GAVEL, "cell": _cell(gamestate, *cell), "multiplier": mult})


def auction_start_event(gamestate):
    """The auction opens: the lots that stay on the board and the respins."""
    _add(gamestate, {"type": AUCTION_START, "lots": _lots(gamestate), "respins": gamestate.respins_left})


def auction_respin_event(gamestate, number: int, landed: list):
    """One respin of the empty cells: what landed (kind P/G/B, value for lots) and respins left after it."""
    _add(
        gamestate,
        {
            "type": AUCTION_RESPIN,
            "respin": number,
            "landed": [{"cell": _cell(gamestate, reel, row), "kind": kind, "value": value} for (reel, row), kind, value in landed],
            "respinsLeft": gamestate.respins_left,
        },
    )


def buyer_collect_event(gamestate, cell, value):
    """A buyer becomes a lot worth every other lot in its reel (at least 1x)."""
    _add(gamestate, {"type": BUYER_COLLECT, "cell": _cell(gamestate, *cell), "value": value})


def gavel_strike_event(gamestate, cell):
    """A gavel doubles every lot on the board, then leaves; `lots` is the board after the strike."""
    _add(gamestate, {"type": GAVEL_STRIKE, "cell": None if cell is None else _cell(gamestate, *cell), "lots": _lots(gamestate)})


def auction_end_event(gamestate, total, full_house: bool):
    """Sold: the auction's total (before the cap), and whether all 15 cells held lots."""
    _add(gamestate, {"type": AUCTION_END, "lots": _lots(gamestate), "total": int(round(total * 100)), "fullHouse": full_house})


def last_bid_event(gamestate, mult: int, total_before):
    """The hammer falls: the final bid multiplies the lots' total (x1 when nobody raises)."""
    _add(gamestate, {"type": LAST_BID, "multiplier": mult, "before": int(round(total_before * 100))})
