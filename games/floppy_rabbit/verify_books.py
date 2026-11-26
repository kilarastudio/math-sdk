"""Replay the published books against the rules in readme.txt, independently of the game code.

Usage (from the math-sdk root):
    uv run python games/floppy_rabbit/verify_books.py [mode ...] [--limit N]

For every book of every mode it follows the events and checks that:
* the clusters paid are exactly the clusters of 5+ like symbols on the board (found here by an
  independent search), and each pays paytable × the sum of the footprints under it;
* a board that stops cascading holds no paying cluster;
* a hop lands within two positions of where the rabbit was, never on its own position or on
  another rabbit, and steps that footprint up (2x, then doubling to 4,096x);
* a flop doubles every footprint on the board and nothing else;
* the base game clears the footprints every round, hops exactly once at the reveal and once
  after every winning cascade, and flops only from the second cascade on;
* Flop Time starts on a clear board with the rabbits the scatters bring (3: one, 4: two, 5+:
  three), each on a 2x footprint, and every rabbit acts exactly once before each free spin is
  evaluated and after every winning cascade, in order; before the free spins the rules name,
  the first rabbit's action is a flop;
* 3+ scatters award 12 free spins and 5 more on a retrigger; a bought round has exactly the
  scatters its mode names;
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
BOUGHT = {"bonus": 3, "double": 4, "fluffle": 5}
RABBITS = {3: 1, 4: 2, 5: 3}
CAP = 4096
REACH = 2
BASE_FLOP_FROM = 2


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


def verify(book: dict, mode: str, config: GameConfig, payout_cents: int) -> None:
    wincap = config.wincap
    prints = [[0] * SIZE for _ in range(SIZE)]
    board = None  # [reel][row] symbols, padding rows included
    rabbits = []
    in_fs = False
    fs_spins = fs_total = 0
    total = 0.0
    cascade = 0
    pending = 0  # actions the rabbits still owe before the next evaluation
    acting = 0  # index of the rabbit that acts next
    expect_enter = False
    capped = False
    sure_due = False  # the next action must be the first rabbit's certain flop

    def scatters() -> int:
        return sum(1 for reel in range(SIZE) for row in range(1, SIZE + 1) if board[reel][row]["name"] == "S")

    def owe(count: int):
        nonlocal pending, acting
        pending, acting = count, 0

    for n, event in enumerate(book["events"]):
        kind = event["type"]
        if kind in ("rabbitHop", "rabbitFlop"):
            need(pending > 0, f"event {n}: a rabbit acted when none was due")
            need(event["rabbit"] == acting, f"event {n}: rabbit {event['rabbit']} acted, rabbit {acting} was due")
            if sure_due:
                need(kind == "rabbitFlop", f"event {n}: free spin {fs_spins} must open with the first rabbit's flop")
                sure_due = False
            if kind == "rabbitHop":
                end = (event["to"]["reel"], event["to"]["row"] - 1)
                if event["from"] is None:
                    need(not in_fs and cascade == 0 and not rabbits, f"event {n}: a hop from nowhere outside the base reveal")
                    rabbits.append(end)
                else:
                    start = (event["from"]["reel"], event["from"]["row"] - 1)
                    need(start == rabbits[acting], f"event {n}: hop starts at {start}, the rabbit is at {rabbits[acting]}")
                    need(end not in rabbits, f"event {n}: hop onto a rabbit's position")
                    need(max(abs(end[0] - start[0]), abs(end[1] - start[1])) <= REACH, f"event {n}: hop from {start} to {end} is out of reach")
                    rabbits[acting] = end
                value = prints[end[0]][end[1]]
                prints[end[0]][end[1]] = 2 if value == 0 else min(value * 2, CAP)
                need(event["value"] == prints[end[0]][end[1]], f"event {n}: hop value {event['value']}")
            else:
                need(in_fs or cascade >= BASE_FLOP_FROM, f"event {n}: base game flop after cascade {cascade}")
                at = (event["at"]["reel"], event["at"]["row"] - 1)
                need(at == rabbits[acting], f"event {n}: flop at {at}, the rabbit is at {rabbits[acting]}")
                prints = [[min(v * 2, CAP) if v else 0 for v in column] for column in prints]
            need(event["footprints"] == prints, f"event {n}: footprints after the action differ")
            pending -= 1
            acting += 1
            continue
        if kind == "rabbitsEnter":
            need(expect_enter, f"event {n}: rabbits entered outside the start of Flop Time")
            expect_enter = False
            rabbits = [(p["reel"], p["row"] - 1) for p in event["rabbits"]]
            need(len(set(rabbits)) == len(rabbits), f"event {n}: two rabbits on one position")
            need(len(rabbits) == RABBITS[min(trigger, 5)], f"event {n}: {len(rabbits)} rabbits for {trigger} scatters")
            prints = [[0] * SIZE for _ in range(SIZE)]
            for reel, row in rabbits:
                prints[reel][row] = 2
            need(event["footprints"] == prints, f"event {n}: footprints at the start of Flop Time differ")
            continue

        # Every other event comes after the rabbits have done what they owed.
        need(pending == 0, f"event {n} ({kind}): {pending} rabbit action(s) missing")
        need(not expect_enter, f"event {n} ({kind}): Flop Time went on before the rabbits entered")
        if kind == "reveal":
            board = [list(column) for column in event["board"]]
            cascade = 0
            if in_fs:
                owe(len(rabbits))
                sure_due = fs_spins in config.fs_sure_flop_spins
            else:
                prints = [[0] * SIZE for _ in range(SIZE)]
                rabbits = []
                owe(1)
        elif kind == "winInfo":
            clusters = find_clusters(board)
            paid = {}
            win_sum = 0.0
            for win in event["wins"]:
                cells = frozenset((p["reel"], p["row"] - 1) for p in win["positions"])
                need(clusters.get(cells) == win["symbol"], f"event {n}: a paid win is not a cluster of {win['symbol']} on the board")
                need(cells not in paid, f"event {n}: a cluster was paid twice")
                paid[cells] = True
                mult = max(sum(prints[reel][row] for reel, row in cells), 1)
                need(win["meta"]["clusterMult"] == mult, f"event {n}: multiplier {win['meta']['clusterMult']}, footprints say {mult}")
                pay = config.paytable[(len(cells), win["symbol"])]
                # the SDK writes a win that passes the max win as the max win
                need(abs(win["win"] / 100 - min(pay * mult, wincap)) < 0.006, f"event {n}: win {win['win']} for {pay} x {mult}")
                win_sum += pay * mult
            need(len(paid) == len(clusters), f"event {n}: {len(clusters)} clusters on the board, {len(paid)} paid")
            total += win_sum
            capped = total >= wincap
        elif kind == "tumbleBoard":
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
            cascade += 1
            owe(len(rabbits))
        elif kind in ("setWin", "setTotalWin"):
            # The board has stopped cascading: nothing on it pays, unless the max win ended the round.
            if kind == "setTotalWin" and not capped:
                need(not find_clusters(board), f"event {n}: the board stopped with a paying cluster on it")
        elif kind == "freeSpinTrigger":
            need(not in_fs, f"event {n}: Flop Time triggered twice")
            trigger = len(event["positions"])
            need(trigger == scatters(), f"event {n}: trigger positions differ from the board")
            need(trigger >= 3, f"event {n}: trigger with {trigger} scatters")
            if mode in BOUGHT:
                need(trigger == BOUGHT[mode], f"event {n}: {mode} round with {trigger} scatters")
            fs_total = config.freespin_triggers[config.basegame_type][trigger]
            need(fs_total == 12 and event["totalFs"] == fs_total, f"event {n}: {event['totalFs']} spins for {trigger} scatters")
            in_fs = True
            expect_enter = True
        elif kind == "updateFreeSpin":
            fs_spins += 1
            need(event["total"] == fs_total, f"event {n}: free spins total {event['total']}, expected {fs_total}")
        elif kind == "freeSpinRetrigger":
            need(scatters() >= 3, f"event {n}: retrigger with {scatters()} scatters")
            fs_total += 5
            need(event["totalFs"] == fs_total, f"event {n}: retrigger total {event['totalFs']}, expected {fs_total}")
        elif kind == "freeSpinEnd":
            need(fs_spins == fs_total or capped, f"event {n}: Flop Time ended after {fs_spins} of {fs_total}")
    need(pending == 0 or capped, "the book ends with a rabbit action missing")
    if mode in BOUGHT:
        need(in_fs, f"{mode} round without Flop Time")
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
