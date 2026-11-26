"""Replay Dwanda's published books against the rules in readme.txt, independently of the game code.

Usage (from the math-sdk root):
    uv run python games/dwanda/verify_books.py [mode ...] [--limit N]

For every book of every mode it follows the events and checks that:
* the clusters paid are exactly the clusters of 5+ like symbols on the board (found here by an
  independent search), and each pays paytable x the sum of the Clash cells under it (none: x1);
* a board that stops cascading holds no paying cluster;
* after every winning cascade the territory changes exactly as readme.txt says, win by win in
  the order paid: unmarked cells take the cluster's side, the other side's cells become Clash
  cells at x2, Clash cells under the cluster double (cap x1,024); in the Duel the mark also
  spreads to the cells next to each cluster without doubling Clash cells there;
* the base game starts every round on an empty territory; the Duel starts on an empty territory,
  plus the Clash cells a bought mode names, and keeps it for the whole feature;
* 3/4/5 scatters award 10/12/15 free spins and 3+ during the Duel add 5; a bought round has 3;
* scatters never leave the board in a cascade;
* the round's payout is the sum of its wins, capped at the max win, and equals the lookup table.

It stops at the first book that breaks a rule and prints why. Exit code 1 on a failure.
"""

import csv
import io
import json
import os
import sys

import zstandard as zstd

from game_config import GameConfig

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLISH = os.path.join(HERE, "library", "publish_files")
SIZE = 7
BOUGHT = {"bonus": (0, 0), "blaze": (5, 4), "eclipse": (9, 8)}
FS = {3: 10, 4: 12, 5: 15}
CAP = 1024
NONE, PHOENIX, DRAGON, CLASH = 0, 1, 2, 3


class Broken(Exception):
    pass


def need(condition, message):
    if not condition:
        raise Broken(message)


def find_clusters(board) -> dict:
    """{frozenset of (reel, row)}: symbol} for clusters of 5+ on the visible rows (padding excluded)."""
    seen = set()
    found = {}
    for reel in range(SIZE):
        for row in range(SIZE):
            if (reel, row) in seen:
                continue
            name = board[reel][row + 1]["name"]
            seen.add((reel, row))
            if name == "S":
                continue
            group, stack = [], [(reel, row)]
            while stack:
                r, c = stack.pop()
                group.append((r, c))
                for r2, c2 in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= r2 < SIZE and 0 <= c2 < SIZE and (r2, c2) not in seen and board[r2][c2 + 1]["name"] == name:
                        seen.add((r2, c2))
                        stack.append((r2, c2))
            if len(group) >= 5:
                found[frozenset(group)] = name
    return found


def mark(marks, clash, wins, duel):
    """Apply one cascade's winning clusters to the territory, in the order they were paid."""
    for symbol, cells in wins:
        side = PHOENIX if symbol.startswith("P") else DRAGON
        if duel:
            edge = {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= r + dr < SIZE and 0 <= c + dc < SIZE
            } - set(cells)
            for r, c in edge:
                m = marks[r][c]
                if m == NONE:
                    marks[r][c] = side
                elif m != side and m != CLASH:
                    marks[r][c], clash[r][c] = CLASH, 2
        for r, c in cells:
            m = marks[r][c]
            if m == NONE:
                marks[r][c] = side
            elif m == CLASH:
                clash[r][c] = min(clash[r][c] * 2, CAP)
            elif m != side:
                marks[r][c], clash[r][c] = CLASH, 2


def verify(book: dict, mode: str, config: GameConfig, payout_cents: int) -> None:
    wincap = config.wincap
    marks = [[NONE] * SIZE for _ in range(SIZE)]
    clash = [[0] * SIZE for _ in range(SIZE)]
    board = None
    in_fs = False
    fs_spins = fs_total = 0
    total = 0.0
    capped = False
    last_wins = []
    expect_start = False

    def scatters() -> int:
        return sum(1 for reel in range(SIZE) for row in range(1, SIZE + 1) if board[reel][row]["name"] == "S")

    for n, event in enumerate(book["events"]):
        kind = event["type"]
        if kind == "territory":
            if event["reason"] == "start":
                need(expect_start, f"event {n}: Clash cells placed outside the start of a bought Duel")
                count, value = BOUGHT[mode]
                cells = [(r, c) for r in range(SIZE) for c in range(SIZE) if event["marks"][r][c] == CLASH]
                need(len(cells) == count, f"event {n}: {len(cells)} starting Clash cells, {mode} brings {count}")
                need(all(event["clash"][r][c] == value for r, c in cells), f"event {n}: starting Clash values")
                need(all(event["marks"][r][c] in (NONE, CLASH) for r in range(SIZE) for c in range(SIZE)), f"event {n}: sides at the start")
                marks = [list(col) for col in event["marks"]]
                clash = [list(col) for col in event["clash"]]
                expect_start = False
            else:
                need(last_wins, f"event {n}: territory changed without a winning cascade")
                mark(marks, clash, last_wins, in_fs)
                need(event["marks"] == marks and event["clash"] == clash, f"event {n}: territory differs from the replay")
                last_wins = []
            continue
        if kind == "updateFreeSpin" and expect_start:
            need(BOUGHT.get(mode, (0, 0))[0] == 0, f"event {n}: the bought Duel did not place its Clash cells")
            expect_start = False
        if kind == "reveal":
            board = [list(column) for column in event["board"]]
            if not in_fs:
                marks = [[NONE] * SIZE for _ in range(SIZE)]
                clash = [[0] * SIZE for _ in range(SIZE)]
            last_wins = []
        elif kind == "winInfo":
            clusters = find_clusters(board)
            paid = {}
            win_sum = 0.0
            wins = []
            for win in event["wins"]:
                cells = frozenset((p["reel"], p["row"] - 1) for p in win["positions"])
                need(clusters.get(cells) == win["symbol"], f"event {n}: a paid win is not a cluster of {win['symbol']} on the board")
                need(cells not in paid, f"event {n}: a cluster was paid twice")
                paid[cells] = True
                mult = max(sum(clash[r][c] for r, c in cells), 1)
                need(win["meta"]["clusterMult"] == mult, f"event {n}: multiplier {win['meta']['clusterMult']}, Clash cells say {mult}")
                pay = config.paytable[(len(cells), win["symbol"])]
                need(abs(win["win"] / 100 - min(pay * mult, wincap)) < 0.006, f"event {n}: win {win['win']} for {pay} x {mult}")
                win_sum += pay * mult
                wins.append((win["symbol"], [(p["reel"], p["row"] - 1) for p in win["positions"]]))
            need(len(paid) == len(clusters), f"event {n}: {len(clusters)} clusters on the board, {len(paid)} paid")
            total += win_sum
            capped = total >= wincap
            last_wins = wins
        elif kind == "tumbleBoard":
            # A winning cascade marks the territory before the board tumbles; a territory event
            # is sent only when something changed, so replay a silent one here.
            if last_wins:
                before = ([list(c) for c in marks], [list(c) for c in clash])
                mark(marks, clash, last_wins, in_fs)
                need((marks, clash) == before, f"event {n}: the territory changed but no territory event was sent")
                last_wins = []
            gone = {}
            for p in event["explodingSymbols"]:
                gone.setdefault(p["reel"], set()).add(p["row"])
            for reel in range(SIZE):
                rows = gone.get(reel, set())
                new = event["newSymbols"][reel]
                need(len(new) == len(rows), f"event {n}: reel {reel} lost {len(rows)} and gained {len(new)}")
                if not rows:
                    continue
                need(all(board[reel][row]["name"] != "S" for row in rows), f"event {n}: a scatter left the board")
                kept = [sym for row, sym in enumerate(board[reel]) if row not in rows]
                board[reel] = list(new) + kept
        elif kind in ("setWin", "setTotalWin"):
            if kind == "setTotalWin" and not capped:
                need(not find_clusters(board), f"event {n}: the board stopped with a paying cluster on it")
        elif kind == "freeSpinTrigger":
            need(not in_fs, f"event {n}: the Duel triggered twice")
            trigger = len(event["positions"])
            need(trigger == scatters(), f"event {n}: trigger positions differ from the board")
            if mode in BOUGHT:
                need(trigger == 3, f"event {n}: {mode} round with {trigger} scatters")
            fs_total = FS.get(trigger, 15)
            need(event["totalFs"] == fs_total, f"event {n}: {event['totalFs']} spins for {trigger} scatters")
            in_fs = True
            marks = [[NONE] * SIZE for _ in range(SIZE)]
            clash = [[0] * SIZE for _ in range(SIZE)]
            expect_start = mode in BOUGHT and BOUGHT[mode][0] > 0
            last_wins = []
        elif kind == "updateFreeSpin":
            fs_spins += 1
            need(event["total"] == fs_total, f"event {n}: free spins total {event['total']}, expected {fs_total}")
        elif kind == "freeSpinRetrigger":
            need(scatters() >= 3, f"event {n}: retrigger with {scatters()} scatters")
            fs_total += 5
            need(event["totalFs"] == fs_total, f"event {n}: retrigger total {event['totalFs']}, expected {fs_total}")
        elif kind == "freeSpinEnd":
            need(fs_spins == fs_total or capped, f"event {n}: the Duel ended after {fs_spins} of {fs_total}")
    if mode in BOUGHT:
        need(in_fs, f"{mode} round without the Duel")
    paid = min(total, wincap)
    need(abs(paid - book["payoutMultiplier"] / 100) < 0.011, f"wins add up to {paid}, the book pays {book['payoutMultiplier'] / 100}")
    need(book["payoutMultiplier"] == payout_cents, f"book pays {book['payoutMultiplier']}, lookup table says {payout_cents}")


def run(mode: dict, config: GameConfig, limit) -> int:
    payouts = {}
    with open(os.path.join(PUBLISH, mode["weights"]), encoding="UTF-8") as f:
        for sim, _, cents in csv.reader(f):
            payouts[int(sim)] = int(cents)
    checked = 0
    with open(os.path.join(PUBLISH, mode["events"]), "rb") as raw:
        reader = io.TextIOWrapper(zstd.ZstdDecompressor().stream_reader(raw, read_across_frames=True), encoding="UTF-8")
        for line in reader:
            book = json.loads(line)
            try:
                verify(book, mode["name"], config, payouts[book["id"]])
            except Broken as broken:
                print(f"{mode['name']}: book {book['id']} breaks a rule: {broken}")
                return -1
            checked += 1
            if limit and checked >= limit:
                break
    return checked


if __name__ == "__main__":
    args = sys.argv[1:]
    limit = None
    if "--limit" in args:
        k = args.index("--limit")
        limit = int(args[k + 1])
        del args[k : k + 2]
    config = GameConfig()
    index = json.load(open(os.path.join(PUBLISH, "index.json"), encoding="UTF-8"))
    failed = False
    for mode in index["modes"]:
        if args and mode["name"] not in args:
            continue
        checked = run(mode, config, limit)
        if checked < 0:
            failed = True
        else:
            print(f"{mode['name']}: {checked:,} books follow the rules")
    sys.exit(1 if failed else 0)
