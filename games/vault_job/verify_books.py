"""Replay The Vault Job's published books against readme.txt, independently of the game code.

Usage (from the math-sdk root):
    uv run python games/vault_job/verify_books.py [--modes base bonus ...] [--limit N]

For every book it rebuilds each board from its events and checks:
* line wins recomputed from the board (paytable, 20 lines, crew substitution, crew-only lines as
  H1, multiplier = sum of crew multipliers above x1 on the winning positions) equal winInfo;
* Muscle fills its reel except scatters and other crew; Hackers carry the highest other crew
  multiplier (at least x2);
* The Job: starts with a x1 Safecracker on reel 2 (plus the mode's extra crew), sticky crew keep
  their cells, Drivers move one reel left past sticky crew, Safecrackers on a winning line climb
  exactly one ladder step, every scatter adds one spin;
* the round's total (capped at 20,000x) equals the book's payoutMultiplier and the lookup table.
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
    "H1": (1.5, 6, 25), "H2": (1, 3, 12), "H3": (0.5, 2, 8), "H4": (0.4, 1.5, 6),
    "L1": (0.3, 0.7, 2.5), "L2": (0.2, 0.5, 2), "L3": (0.1, 0.4, 1.5), "L4": (0.1, 0.3, 1.2),
}
LINES = [
    "00000", "11111", "22222", "33333", "01210", "12321", "32123", "21012", "00100", "11211",
    "22322", "33233", "22122", "11011", "01110", "12221", "23332", "32223", "21112", "10001",
]
CREW = {"WD", "WC", "WM", "WH"}
LADDER = (1, 2, 3, 5, 8, 12, 20, 30, 50, 80, 120, 200, 300, 500, 1000)
FS = {3: 10, 4: 12, 5: 15}
START = {"bonus": [("WC", 1)], "inside": [("WC", 1), ("WC", 2)], "heist": [("WC", 1), ("WC", 3), ("WC", 3)]}
CAP = 20000


def books(mode):
    with open(os.path.join(PUBLISH, f"books_{mode}.jsonl.zst"), "rb") as f:
        text = io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(f, read_across_frames=True), encoding="utf-8")
        for line in text:
            if line.strip():
                yield json.loads(line)


def line_wins(board, mult):
    """board[reel][row] names without padding; mult[reel][row] crew multipliers."""
    total, wins = 0.0, []
    for index, pattern in enumerate(LINES, start=1):
        rows = [int(c) for c in pattern]
        names = [board[r][rows[r]] for r in range(5)]
        lead = 0
        while lead < 5 and names[lead] in CREW:
            lead += 1
        first = next((n for n in names if n not in CREW), None)
        count = 0
        if first in PAYS:
            for n in names:
                if n in CREW or n == first:
                    count += 1
                else:
                    break
        best, kind = 0.0, 0
        if first in PAYS and count >= 3:
            best, kind = PAYS[first][count - 3], count
        if lead >= 3 and PAYS["H1"][lead - 3] > best:
            best, kind = PAYS["H1"][lead - 3], lead
        if best <= 0:
            continue
        m = sum(mult[r][rows[r]] for r in range(kind) if mult[r][rows[r]] > 1)
        m = max(m, 1)
        win = round(best * m, 2)
        total += win
        wins.append((index, kind, win, {(r, rows[r]) for r in range(kind)}))
    return round(total, 2), wins


class Fail(Exception):
    pass


def check(cond, msg):
    if not cond:
        raise Fail(msg)


def verify(book, mode):
    ev = book["events"]
    i = 0
    total = 0.0
    sticky = {}
    in_job = False
    spins_total = spins_done = 0
    expect_moves = None
    stats = {"boards": 0, "job": 0}
    while i < len(ev):
        e = ev[i]
        t = e["type"]
        if t == "crewStart":
            in_job = True
            placed = [(c["crew"], c["multiplier"]) for c in e["crew"]]
            check(sorted(placed) == sorted(START.get(mode, [("WC", 1)])), f"start crew {placed}")
            for c in e["crew"]:
                cell = (c["cell"]["reel"], c["cell"]["row"] - 1)
                check(cell[0] == 1, "start crew off reel 2")
                sticky[cell] = (c["crew"], c["multiplier"])
            stats["job"] = 1
        elif t == "freeSpinTrigger":
            spins_total = e["totalFs"]
            check(spins_total == FS[len(e["positions"])], "free spins by scatters")
        elif t == "updateFreeSpin":
            spins_done += 1
            check(e["amount"] == spins_done, "spin counter")
            # Drivers move before the reels (crewMove only when there is a Driver).
            moved = {}
            for (cell, (name, m)) in sorted(sticky.items()):
                if name == "WD":
                    moved[cell] = m
            if moved:
                check(i + 1 < len(ev) and ev[i + 1]["type"] == "crewMove", "missing crewMove")
                mv = ev[i + 1]["moves"]
                for cell in sorted(moved, key=lambda c: c[0]):
                    sticky.pop(cell)
                for cell in sorted(moved, key=lambda c: c[0]):
                    target = cell[0] - 1
                    while target >= 0 and (target, cell[1]) in sticky:
                        target -= 1
                    rec = next(x for x in mv if (x["from"]["reel"], x["from"]["row"] - 1) == cell)
                    if target < 0:
                        check(rec["to"] is None, "driver should leave")
                    else:
                        check((rec["to"]["reel"], rec["to"]["row"] - 1) == (target, cell[1]), "driver target")
                        sticky[(target, cell[1])] = ("WD", moved[cell])
                i += 1
        elif t == "reveal":
            stats["boards"] += 1
            board = [[c["name"] for c in reel[1:-1]] for reel in e["board"]]
            job = e["gameType"] == "freegame"
            mult = [[0] * 4 for _ in range(5)]
            for (r, c), (name, m) in sticky.items():
                check(board[r][c] == name, f"sticky {name} missing at {(r, c)}")
                mult[r][c] = m
            for r in range(5):
                for c in range(4):
                    n = board[r][c]
                    if n in CREW:
                        check(r >= 1 or (r, c) in sticky, "crew on reel 1")
                        if (r, c) not in sticky:
                            mult[r][c] = {"WD": 2, "WC": 1 if job else 2, "WM": 1, "WH": 1}[n]
                            if job and n in ("WD", "WC"):
                                sticky[(r, c)] = (n, mult[r][c])
            # Muscle, then Hacker.
            for r in range(5):
                if "WM" in board[r]:
                    for c in range(4):
                        if board[r][c] not in CREW and board[r][c] != "S":
                            board[r][c] = "WM"
                            mult[r][c] = 1
            hackers = [(r, c) for r in range(5) for c in range(4) if board[r][c] == "WH"]
            if hackers:
                best = max([mult[r][c] for r in range(5) for c in range(4) if board[r][c] in CREW and board[r][c] != "WH"], default=1)
                for r, c in hackers:
                    mult[r][c] = max(best, 2)
            # The crewBoard event, when present, must agree with this board.
            j = i + 1
            while j < len(ev) and ev[j]["type"] in ("crewExpand", "crewHack"):
                j += 1
            if any(n in CREW for col in board for n in col):
                check(ev[j]["type"] == "crewBoard", "missing crewBoard")
                seen = {(x["cell"]["reel"], x["cell"]["row"] - 1): (x["crew"], x["multiplier"]) for x in ev[j]["crew"]}
                mine = {(r, c): (board[r][c], mult[r][c] or 1) for r in range(5) for c in range(4) if board[r][c] in CREW}
                check(seen == mine, "crewBoard differs from the replayed board")
            win, wins = line_wins(board, mult)
            k = j
            reported = 0.0
            while k < len(ev) and ev[k]["type"] not in ("reveal", "updateFreeSpin", "freeSpinTrigger", "freeSpinEnd", "finalWin"):
                if ev[k]["type"] == "winInfo":
                    reported = ev[k]["totalWin"] / 100
                if ev[k]["type"] == "crewUpgrade":
                    on = {cell for w in wins for cell in w[3]}
                    ups = {(x["cell"]["reel"], x["cell"]["row"] - 1): x["multiplier"] for x in ev[k]["upgrades"]}
                    want = {}
                    for cell, (name, m) in sticky.items():
                        if name == "WC" and cell in on and m < LADDER[-1]:
                            want[cell] = LADDER[LADDER.index(m) + 1]
                    check(ups == want, f"safecracker steps {ups} vs {want}")
                    for cell, m in ups.items():
                        sticky[cell] = ("WC", m)
                if ev[k]["type"] == "freeSpinRetrigger":
                    scat = sum(1 for col in board for n in col if n == "S")
                    check(ev[k]["totalFs"] - spins_total == scat, "retrigger adds one per scatter")
                    spins_total = ev[k]["totalFs"]
                k += 1
            if not any(ev[x]["type"] == "crewUpgrade" for x in range(j, k)) and job:
                on = {cell for w in wins for cell in w[3]}
                for cell, (name, m) in sticky.items():
                    check(not (name == "WC" and cell in on and m < LADDER[-1]), "safecracker should have climbed")
            if win > 0 or reported > 0:
                check(abs(min(win, CAP) - min(reported, CAP)) < 0.011, f"board win {win} vs winInfo {reported}")
            total += win
            i = k - 1
        i += 1
    if in_job:
        check(spins_done == spins_total or min(total, CAP) >= CAP, f"spins {spins_done} of {spins_total}")
    want = int(round(min(total, CAP) * 100))
    check(abs(want - book["payoutMultiplier"]) <= 1, f"payout {book['payoutMultiplier']} vs replay {want}")
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", nargs="+", default=["base", "bonus", "inside", "heist"])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    bad = 0
    for mode in args.modes:
        lut = {}
        with open(os.path.join(PUBLISH, f"lookUpTable_{mode}_0.csv")) as f:
            for sim, _, pay in csv.reader(f):
                lut[int(sim)] = int(pay)
        n = jobs = 0
        for book in books(mode):
            try:
                s = verify(book, mode)
                jobs += s["job"]
                if lut[book["id"]] != book["payoutMultiplier"]:
                    raise Fail("lookup table payout differs")
            except Fail as exc:
                bad += 1
                if bad <= 10:
                    print(f"{mode} book {book['id']}: {exc}")
            n += 1
            if args.limit and n >= args.limit:
                break
        print(f"{mode}: {n} books replayed, {jobs} with The Job")
    print("all books follow readme.txt" if bad == 0 else f"{bad} books FAILED")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
