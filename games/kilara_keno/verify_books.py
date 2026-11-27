"""Independent checks of the published files.

    uv run python games/kilara_keno/verify_books.py

1. Every book's payoutMultiplier equals its lookup row, ids are 0-based and in order.
2. Every book's numbers show its pattern, and its win is recomputed from that pattern with
   the rules in readme.txt.
3. Kilau rounds (3 marked numbers in Low, High and Chain) carry exactly their share of a mode's
   weight.
4. A real keno draw (40 numbers, random picks, random draw order, a Kilau round at its share) is
   simulated for a few modes and compared with the exact RTP of the lookup table.
"""

import csv
import io
import json
import os
import random
import sys

import zstandard

sys.path.insert(0, os.path.dirname(__file__))
from game_config import GameConfig  # noqa: E402


def read_books(path):
    with open(path, "rb") as f:
        data = zstandard.ZstdDecompressor().stream_reader(f, read_across_frames=True).read()
    return [json.loads(line) for line in io.StringIO(data.decode()) if line.strip()]


def rule_win(cfg, level, picks, pattern):
    """The win of a draw order, written out again from readme.txt (not imported from the game).

    0 = miss, 1 = hit, 2 = Kilau ball.
    """
    hits = pattern.count(1)
    peak = run = 0
    for ball in pattern:
        if ball == 1:
            run += 1
        elif ball == 0:
            run = max(0, run - 1) if level in ("chain", "chainmax") else 0
        peak = max(peak, run)
    step = min(peak + pattern.count(2), 7)
    ladder = {0: 1, 1: 1, 2: 2, 3: 3, 4: 5, 5: 10, 6: 15, 7: 25}
    return round(cfg.pay_tables[level][picks][hits] * ladder[step] * 100)


def main():
    cfg = GameConfig()
    pub = cfg.publish_path
    exact, distinct = {}, {}
    for bm in cfg.bet_modes:
        mode = bm.get_name()
        level, picks, draws, options = cfg.mode_parts(mode)
        base_kilau = cfg.level_kilau[level]
        allowed = {kilau for kilau, _ in options}
        books = read_books(os.path.join(pub, f"books_{mode}.jsonl.zst"))
        with open(os.path.join(pub, f"lookUpTable_{mode}_0.csv"), encoding="UTF-8") as f:
            rows = [tuple(int(x) for x in r) for r in csv.reader(f)]
        assert len(books) == len(rows), mode
        total = paid = kilau_round_weight = 0
        boards = set()
        for i, (book, (sim, weight, cents)) in enumerate(zip(books, rows)):
            assert book["id"] == sim == i, (mode, i, book["id"], sim)
            assert book["payoutMultiplier"] == cents, (mode, i)
            draw = book["events"][0]
            assert draw["type"] == "draw" and len(draw["pattern"]) == draws and draw["picks"] == picks
            chosen, marked, numbers = draw["selected"], draw["kilau"], draw["numbers"]
            assert len(set(chosen)) == picks and len(set(numbers)) == draws
            assert len(set(marked)) == len(marked) and len(marked) in allowed and not set(marked) & set(chosen), (mode, i)
            assert draw["kilauRound"] == (len(marked) > base_kilau), (mode, i)
            assert all(1 <= n <= cfg.board_numbers for n in chosen + marked + numbers)
            assert [1 if n in chosen else 2 if n in marked else 0 for n in numbers] == draw["pattern"], (mode, i)
            boards.add((tuple(chosen), tuple(marked), tuple(numbers)))
            assert rule_win(cfg, level, picks, draw["pattern"]) == cents, (mode, i)
            assert cents <= cfg.wincap * 100 and weight > 0
            total += weight
            paid += weight * cents
            kilau_round_weight += weight * draw["kilauRound"]
        rounds, out_of = cfg.kilau_round_share if level in cfg.kilau_round_levels else (0, 1)
        assert kilau_round_weight * out_of == total * rounds, (mode, kilau_round_weight, total)
        exact[mode] = paid / total / 100 / bm.get_cost()
        distinct[mode] = len(boards)
        assert total < 2**64
    print(f"books and lookup tables agree for {len(exact)} modes")
    print("distinct boards per mode: " + ", ".join(f"{m} {n:,}" for m, n in distinct.items()))

    random.seed(7)
    board = list(range(1, cfg.board_numbers + 1))
    for mode, rounds in (("low_1", 2_000_000), ("low_2", 2_000_000), ("low_8", 3_000_000), ("high_5", 3_000_000), ("chain_10", 2_000_000), ("chainmax_10", 2_000_000)):
        level, picks, draws, options = cfg.mode_parts(mode)
        counts = [kilau for kilau, _ in options]
        shares = [share for _, share in options]
        cost = cfg.level_cost[level]
        paid = 0
        for _ in range(rounds):
            kilau = random.choices(counts, shares)[0]
            mine = random.sample(board, picks + kilau)
            mine, marked = set(mine[:picks]), set(mine[picks:])
            pattern = [1 if n in mine else 2 if n in marked else 0 for n in random.sample(board, draws)]
            paid += rule_win(cfg, level, picks, pattern)
        print(f"{mode}: real draws {100 * paid / rounds / 100 / cost:.3f}% over {rounds:,} rounds, lookup table {100 * exact[mode]:.3f}%")


if __name__ == "__main__":
    main()
