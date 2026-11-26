"""Replay Going Once's published books against readme.txt, independently of the game code.

Usage (from the math-sdk root):
    uv run python games/going_once/verify_books.py [--modes base bonus ...] [--limit N]

For every book it checks:
* base board line wins recomputed from the revealed board (20 lines, W substitutes, a wild-only
  line pays as H1, a gavel on reel 3 doubles every line) equal winInfo;
* the auction starts from exactly the lots on the board (6+ in base; the mode's count in a buy),
  respins reset to 3 whenever anything lands and count down otherwise, it ends at 0 respins or
  15 lots, only empty cells receive symbols;
* a buyer becomes the sum of the other lots in its reel (at least 1x), then every gavel doubles
  every lot; a buy mode's opening gavel strikes double the opening lots;
* Last Bid is one of the listed multipliers and the auction pays lots x bid (x2 on a Full House);
* the round's total (capped at 25,000x) equals payoutMultiplier and the lookup table.
"""

import argparse
import csv
import io
import json
import os
import sys

import zstandard

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLISH = os.path.join(HERE, "library", "publish_files")
PAYS = {
    "H1": (3, 12, 45), "H2": (2, 7.5, 25), "H3": (1.5, 4.5, 15), "H4": (1.2, 3, 12),
    "L1": (0.8, 1.5, 6), "L2": (0.6, 1.2, 4.5), "L3": (0.4, 1, 3.8), "L4": (0.3, 0.8, 3),
}
LINES = [
    "11111", "00000", "22222", "01210", "21012", "00100", "22122", "10001", "12221", "01010",
    "21212", "11011", "11211", "01110", "21112", "10101", "12121", "00200", "22022", "02020",
]
LOT_VALUES = {1, 2, 3, 5, 10, 25, 50}
BIDS = {1, 2, 3, 5, 10, 25, 50, 100}
BUY = {"bonus": (6, 0), "gavel": (6, 1), "private": (9, 2)}
CAP = 25000


class Fail(Exception):
    pass


def check(cond, msg):
    if not cond:
        raise Fail(msg)


def books(mode):
    with open(os.path.join(PUBLISH, f"books_{mode}.jsonl.zst"), "rb") as f:
        text = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(f, read_across_frames=True), encoding="utf-8")
        for line in text:
            if line.strip():
                yield json.loads(line)


def line_total(board, mult):
    total = 0.0
    for pattern in LINES:
        names = [board[r][int(pattern[r])] for r in range(5)]
        lead = 0
        while lead < 5 and names[lead] == "W":
            lead += 1
        first = next((n for n in names if n != "W"), None)
        count = 0
        if first in PAYS:
            for n in names:
                if n == "W" or n == first:
                    count += 1
                else:
                    break
        best = 0.0
        if first in PAYS and count >= 3:
            best = PAYS[first][count - 3]
        if lead >= 3:
            best = max(best, PAYS["H1"][lead - 3])
        total += round(best * mult, 2)
    return round(total, 2)


def verify(book, mode):
    ev = book["events"]
    reveal = ev[0]
    check(reveal["type"] == "reveal", "first event is the reveal")
    board = [[c["name"] for c in reel[1:-1]] for reel in reveal["board"]]
    values = {(r, c): reveal["board"][r][c + 1].get("prize") for r in range(5) for c in range(3) if board[r][c] == "P"}
    check(all(v in LOT_VALUES for v in values.values()), "lot value outside the table")
    check(all(board[r][c] != "W" or 1 <= r <= 3 for r in range(5) for c in range(3)), "wild off reels 2-4")
    check(all(board[r][c] != "G" or r == 2 for r in range(5) for c in range(3)), "gavel off reel 3")
    mult = 2 if any(n == "G" for col in board for n in col) else 1
    total = line_total(board, mult)
    reported = next((e["totalWin"] / 100 for e in ev if e["type"] == "winInfo"), 0.0)
    check(abs(total - reported) < 0.011, f"line wins {total} vs winInfo {reported}")
    auction = [e for e in ev if e["type"].startswith("auction") or e["type"] in ("gavelStrike", "buyerCollect", "lastBid")]
    if mode in BUY:
        check(len(values) == BUY[mode][0], f"opening lots {len(values)}")
    if len(values) >= 6:
        check(auction and auction[0]["type"] == "auctionStart", "6+ lots must start the auction")
        lots = dict(values)
        start = {(x["cell"]["reel"], x["cell"]["row"] - 1): x["value"] for x in auction[0]["lots"]}
        check(start == lots, "auction starts from the board's lots")
        respins = 3
        opening = BUY[mode][1] if mode in BUY else 0
        k = 1
        for _ in range(opening):
            check(auction[k]["type"] == "gavelStrike" and auction[k]["cell"] is None, "opening gavel strike")
            lots = {c: v * 2 for c, v in lots.items()}
            k += 1
        bid = None
        while k < len(auction):
            e = auction[k]
            if e["type"] == "auctionRespin":
                check(respins > 0 and len(lots) < 15, "respin after the auction should have ended")
                landed = e["landed"]
                for x in landed:
                    cell = (x["cell"]["reel"], x["cell"]["row"] - 1)
                    check(cell not in lots, "symbol landed on a held lot")
                    if x["kind"] == "P":
                        check(x["value"] in LOT_VALUES, "respin lot value")
                        lots[cell] = x["value"]
                respins = 3 if landed else respins - 1
                check(e["respinsLeft"] == respins, "respin count")
                buyers = [(x["cell"]["reel"], x["cell"]["row"] - 1) for x in landed if x["kind"] == "B"]
                gavels = [(x["cell"]["reel"], x["cell"]["row"] - 1) for x in landed if x["kind"] == "G"]
                k += 1
                for cell in buyers:
                    b = auction[k]
                    check(b["type"] == "buyerCollect", "buyer event")
                    value = max(1, sum(v for (r, _), v in lots.items() if r == cell[0]))
                    check(b["value"] == value, f"buyer value {b['value']} vs {value}")
                    lots[cell] = value
                    k += 1
                for cell in gavels:
                    g = auction[k]
                    check(g["type"] == "gavelStrike", "gavel event")
                    lots = {c: v * 2 for c, v in lots.items()}
                    after = {(x["cell"]["reel"], x["cell"]["row"] - 1): x["value"] for x in g["lots"]}
                    check(after == lots, "gavel doubles every lot")
                    k += 1
                continue
            if e["type"] == "lastBid":
                check(respins == 0 or len(lots) == 15, "hammer before the auction ended")
                check(e["multiplier"] in BIDS, "bid multiplier")
                check(e["before"] == sum(lots.values()) * 100, "bid applies to the lots' total")
                bid = e["multiplier"]
            if e["type"] == "auctionEnd":
                full = len(lots) == 15
                check(e["fullHouse"] == full, "full house flag")
                pay = sum(lots.values()) * bid * (2 if full else 1)
                check(e["total"] == pay * 100, "auction total")
                total += pay
            k += 1
        check(bid is not None, "auction without a hammer")
    else:
        check(not auction, "auction without 6 lots")
    want = int(round(min(total, CAP) * 100))
    check(abs(want - book["payoutMultiplier"]) <= 1, f"payout {book['payoutMultiplier']} vs replay {want}")
    return len(values) >= 6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", nargs="+", default=["base", "bonus", "gavel", "private"])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    bad = 0
    for mode in args.modes:
        lut = {}
        with open(os.path.join(PUBLISH, f"lookUpTable_{mode}_0.csv")) as f:
            for sim, _, pay in csv.reader(f):
                lut[int(sim)] = int(pay)
        n = auctions = 0
        for book in books(mode):
            try:
                auctions += verify(book, mode)
                if lut[book["id"]] != book["payoutMultiplier"]:
                    raise Fail("lookup table payout differs")
            except Fail as exc:
                bad += 1
                if bad <= 10:
                    print(f"{mode} book {book['id']}: {exc}")
            n += 1
            if args.limit and n >= args.limit:
                break
        print(f"{mode}: {n} books replayed, {auctions} auctions")
    print("all books follow readme.txt" if bad == 0 else f"{bad} books FAILED")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
