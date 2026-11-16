"""Replay the published books against the rules in readme.txt, independently of the game code.

Usage (from the math-sdk root):
    uv run python games/pratala/verify_books.py [mode ...] [--limit N]

For every book of every mode it follows the events and checks that:
* a symbol win pays paytable × the brightest lit spot under it, and its count is 8 or more;
* after a win the spots under it go unlit -> primed -> 2x -> 4x -> 8x and no further;
* a Glint Strike only raises spots, to 2x, 4x or 8x, on the number of spots the rules allow;
* a Dragon's Gaze happens only in free spins, doubles exactly the reels it lists (an unlit or
  primed spot lights at 2x, the cap is 4,096x), and each eye it names is a scatter that just
  landed and had not gazed before;
* every scatter that lands in free spins gazes, before the next evaluation;
* free spins start with the floor the trigger and the mode give (128x with six or more
  scatters, 8x in super, 4x in hoard) and with the spins the scatters award;
* hoard sweeps one reel before every free spin, in order, and no other mode does;
* 3 or more scatters at the end of a free spin add 5 spins;
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
ROWS, REELS = 5, 6
FLOOR = {"super": 8, "hoard": 4}
SWEEP = {"hoard"}


class Broken(Exception):
    pass


def need(condition, message):
    if not condition:
        raise Broken(message)


def verify(book: dict, mode: str, config: GameConfig, payout_cents: int) -> None:
    rule = config.glint_rule
    wincap = config.wincap
    glint = [[0] * ROWS for _ in range(REELS)]
    board = None  # [reel][row] names, padding rows included
    gazed = set()  # scatters (reel, id) that have gazed; ids follow a scatter as it falls
    scatters = {}  # reel -> list of [row, id]
    next_id = 0
    in_fs = False
    fs_spins = fs_total = 0
    pending_gaze = []  # scatters that landed and have not gazed yet
    expect_floor = None
    expect_sweep = False
    total = 0.0
    trigger_eyes = 0
    events = book["events"]

    def find_scatters():
        nonlocal next_id
        found = {}
        landed = []
        for reel in range(REELS):
            found[reel] = []
            for row in range(1, ROWS + 1):
                if board[reel][row]["name"] == "S":
                    found[reel].append([row, next_id])
                    landed.append((reel, row, next_id))
                    next_id += 1
        return found, landed

    for n, event in enumerate(events):
        kind = event["type"]
        if kind == "reveal":
            need(not pending_gaze, f"event {n}: scatters landed in free spins without a gaze")
            need(not expect_sweep, f"event {n}: hoard free spin revealed without its sweep")
            board = [list(column) for column in event["board"]]
            scatters, landed = find_scatters()
            if in_fs:
                pending_gaze = landed
            else:
                # the base game starts every round with a clear floor
                glint = [[0] * ROWS for _ in range(REELS)]
        elif kind == "glintStrike":
            spots = event["spots"]
            low, high = (8, 15) if in_fs else (3, 6)
            need(low <= len(spots) <= high, f"event {n}: strike on {len(spots)} spots")
            for spot in spots:
                reel, row = spot["reel"], spot["row"] - 1
                need(spot["value"] >= glint[reel][row], f"event {n}: strike lowered a spot")
                if spot["value"] != glint[reel][row]:
                    need(spot["value"] in (2, 4, 8), f"event {n}: strike value {spot['value']}")
                glint[reel][row] = spot["value"]
            need(event["glint"] == glint, f"event {n}: grid after the strike differs")
        elif kind == "glintGaze":
            need(in_fs, f"event {n}: gaze outside free spins")
            eyes = event["eyes"]
            if eyes:
                want = sorted((reel, row) for reel, row, _ in pending_gaze)
                got = sorted((eye["reel"], eye["row"]) for eye in eyes)
                need(want == got, f"event {n}: gaze eyes {got}, scatters that landed {want}")
                need([eye["reel"] for eye in eyes] == event["reels"], f"event {n}: gaze reels differ from its eyes")
                for _, _, scatter_id in pending_gaze:
                    need(scatter_id not in gazed, f"event {n}: a scatter gazed twice")
                    gazed.add(scatter_id)
                pending_gaze = []
            else:
                need(mode in SWEEP and expect_sweep, f"event {n}: sweep gaze not expected here")
                need(event["reels"] == [(fs_spins - 1) % REELS], f"event {n}: sweep on reel {event['reels']}")
                expect_sweep = False
            for reel in event["reels"]:
                for row in range(ROWS):
                    value = glint[reel][row]
                    glint[reel][row] = 2 if value < 2 else min(value * 2, rule["cap"])
            need(event["glint"] == glint, f"event {n}: grid after the gaze differs")
        elif kind == "winInfo":
            need(not pending_gaze, f"event {n}: evaluated before the scatters that landed gazed")
            exploded = set()
            win_sum = 0.0
            for win in event["wins"]:
                cells = [(p["reel"], p["row"] - 1) for p in win["positions"]]
                need(len(cells) >= 8, f"event {n}: win with {len(cells)} symbols")
                for reel, row in cells:
                    need(board[reel][row + 1]["name"] == win["symbol"], f"event {n}: win position holds another symbol")
                lit = [glint[reel][row] for reel, row in cells if glint[reel][row] >= 2]
                mult = max(lit) if lit else 1
                need(win["meta"]["clusterMult"] == mult, f"event {n}: multiplier {win['meta']['clusterMult']}, floor says {mult}")
                pay = config.paytable[(len(cells), win["symbol"])]
                # the SDK writes a win that passes the max win as the max win
                need(abs(win["win"] / 100 - min(pay * mult, wincap)) < 0.006, f"event {n}: win {win['win']} for {pay} x {mult}")
                win_sum += pay * mult
                exploded.update(cells)
            total += win_sum
            for reel, row in exploded:
                value = glint[reel][row]
                if value == 0:
                    glint[reel][row] = 1
                elif value == 1:
                    glint[reel][row] = 2
                elif value < rule["explode_cap"]:
                    glint[reel][row] = min(value * 2, rule["explode_cap"])
        elif kind == "updateGlint":
            if expect_floor is not None:
                floor = expect_floor
                expect_floor = None
                need(event["glint"] == [[floor] * ROWS for _ in range(REELS)], f"event {n}: free spins floor is not {floor}x everywhere")
                glint = [list(column) for column in event["glint"]]
            else:
                need(event["glint"] == glint, f"event {n}: grid after the win differs")
        elif kind == "tumbleBoard":
            gone = {}
            for p in event["explodingSymbols"]:
                gone.setdefault(p["reel"], set()).add(p["row"])
            landed = []
            for reel in range(REELS):
                rows = gone.get(reel, set())
                new = event["newSymbols"][reel]
                need(len(new) == len(rows), f"event {n}: reel {reel} lost {len(rows)} and gained {len(new)}")
                if not rows:
                    continue
                need(all(board[reel][row]["name"] != "S" for row in rows), f"event {n}: a scatter exploded")
                kept = [(row, sym) for row, sym in enumerate(board[reel]) if row not in rows]
                moved = {old: k + len(new) for k, (old, _) in enumerate(kept)}
                board[reel] = list(new) + [sym for _, sym in kept]
                for entry in scatters.get(reel, []):
                    entry[0] = moved[entry[0]]
                # the old top padding symbol and the new ones are now visible in rows 1..len(new)
                known = {entry[0] for entry in scatters.get(reel, [])}
                for row in range(1, len(new) + 1):
                    if board[reel][row]["name"] == "S" and row not in known:
                        scatters.setdefault(reel, []).append([row, next_id])
                        landed.append((reel, row, next_id))
                        next_id += 1
            if in_fs:
                pending_gaze = landed
        elif kind == "freeSpinTrigger":
            need(not in_fs, f"event {n}: free spins triggered twice")
            trigger_eyes = len(event["positions"])
            need(trigger_eyes == sum(len(v) for v in scatters.values()), f"event {n}: trigger positions differ from the board")
            need(trigger_eyes >= 4, f"event {n}: trigger with {trigger_eyes} scatters")
            fs_total = config.freespin_triggers[config.basegame_type][trigger_eyes]
            need(event["totalFs"] == fs_total, f"event {n}: {event['totalFs']} spins for {trigger_eyes} scatters")
            in_fs = True
            floor = FLOOR.get(mode, 0)
            for eyes, value in config.fs_trigger_glint.items():
                if trigger_eyes >= eyes:
                    floor = max(floor, value)
            expect_floor = floor
            glint = [[0] * ROWS for _ in range(REELS)]
        elif kind == "updateFreeSpin":
            need(not pending_gaze, f"event {n}: scatters landed in free spins without a gaze")
            fs_spins += 1
            need(event["total"] == fs_total, f"event {n}: free spins total {event['total']}, expected {fs_total}")
            expect_sweep = mode in SWEEP
        elif kind == "freeSpinRetrigger":
            count = sum(len(v) for v in scatters.values())
            need(count >= 3, f"event {n}: retrigger with {count} scatters")
            fs_total += 5
            need(event["totalFs"] == fs_total, f"event {n}: retrigger total {event['totalFs']}, expected {fs_total}")
        elif kind == "freeSpinEnd":
            need(fs_spins == fs_total or total >= wincap, f"event {n}: free spins ended after {fs_spins} of {fs_total}")
    need(not pending_gaze, "the book ends with a scatter that never gazed")
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
