"""Floppy Rabbit design model.

A fast stand-alone model of the rules in MATH.md, used to check that the design adds up before
the SDK game is written. It is not the game: cells are drawn independently from symbol weights
(no reel strips), there is no wild, and nothing is weighted. Its numbers are marked "model" in
MATH.md and are replaced by SDK measurements once the game is simulated.

The runs behind MATH.md (W = 7,10,12,15,17,19,20):

    python3 design_model.py base --rounds 2000000 --weights W --scatter 0.0055 \
        --flop 0.2 --flop-radius 99 --flop-from-cascade 2
    python3 design_model.py bonus --rounds 600000 --weights W --scatter 0.0058 --scale 1 \
        --reveal-flop --flop-radius 99 --spins 12 --cap-level 12 --flop 0.195 --rabbits 1
    ... --flop 0.09 --rabbits 2        # Double Flop
    ... --flop 0.055 --rabbits 3       # Fluffle at about 430x; --flop 0.07 gives about 710x
"""

import argparse
import json
import random
from multiprocessing import Pool

SIZE = 7
CELLS = SIZE * SIZE  # index = column * SIZE + row, row 0 is the top

SYMBOLS = ["H1", "H2", "H3", "H4", "L1", "L2", "L3"]
SCATTER = 7
# Cluster size tiers 5, 6-8, 9-12, 13+ (shape of the SDK cluster sample; the scale is solved later).
PAYTABLE = [
    (5.0, 12.5, 25.0, 60.0),
    (2.0, 5.0, 10.0, 40.0),
    (1.3, 3.2, 7.0, 30.0),
    (1.0, 2.5, 6.0, 20.0),
    (0.6, 1.5, 4.0, 10.0),
    (0.4, 1.2, 3.5, 8.0),
    (0.2, 0.8, 2.5, 5.0),
]
SYMBOL_WEIGHTS = [10.1, 12.9, 13.5, 15.6, 15.3, 15.8, 15.6]

NEIGHBOURS = []
for c in range(SIZE):
    for r in range(SIZE):
        cell = []
        if r > 0:
            cell.append(c * SIZE + r - 1)
        if r < SIZE - 1:
            cell.append(c * SIZE + r + 1)
        if c > 0:
            cell.append((c - 1) * SIZE + r)
        if c < SIZE - 1:
            cell.append((c + 1) * SIZE + r)
        NEIGHBOURS.append(cell)


def reach_table(reach):
    table = []
    for c in range(SIZE):
        for r in range(SIZE):
            cells = []
            for c2 in range(SIZE):
                for r2 in range(SIZE):
                    if (c2, r2) != (c, r) and max(abs(c2 - c), abs(r2 - r)) <= reach:
                        cells.append(c2 * SIZE + r2)
            table.append(cells)
    return table


def tier(size):
    if size >= 13:
        return 3
    if size >= 9:
        return 2
    if size >= 6:
        return 1
    return 0


class Model:
    def __init__(self, cfg, seed):
        self.cfg = cfg
        self.rng = random.Random(seed)
        total = sum(cfg["weights"])
        scatter = cfg["scatter"]
        weights = [w / total * (1 - scatter) for w in cfg["weights"]] + [scatter]
        self.cum = []
        acc = 0.0
        for w in weights:
            acc += w
            self.cum.append(acc)
        self.pop = list(range(len(weights)))
        self.reach = reach_table(cfg["reach"])
        self.flop_reach = [cells + [i] for i, cells in enumerate(reach_table(max(1, min(cfg["flop_radius"], SIZE))))]
        self.cap = cfg["cap_level"]

    def draw(self, n):
        return self.rng.choices(self.pop, cum_weights=self.cum, k=n)

    def step_up(self, levels, cell):
        if levels[cell] < self.cap:
            levels[cell] += 1

    def act(self, levels, rabbits, allow_flop, stats):
        """Every rabbit takes its actions: flop where it is, or hop within reach."""
        rng = self.rng
        for i in range(len(rabbits)):
            for _ in range(self.cfg["actions"]):
                if allow_flop and rng.random() < self.cfg["flop"]:
                    stats["flops"] += 1
                    radius = self.cfg["flop_radius"]
                    if radius == 0:
                        self.step_up(levels, rabbits[i])
                    else:
                        # The flop doubles every footprint within the radius (99 = the whole board).
                        targets = range(CELLS) if radius >= SIZE else self.flop_reach[rabbits[i]]
                        for cell in targets:
                            if levels[cell]:
                                self.step_up(levels, cell)
                else:
                    rabbits[i] = rng.choice(self.reach[rabbits[i]])
                    stats["hops"] += 1
                    self.step_up(levels, rabbits[i])

    def spin(self, levels, rabbits, free, stats):
        """One board with its tumbles. Returns (win in paytable units, scatters on the board)."""
        rng = self.rng
        board = self.draw(CELLS)
        if free and self.cfg["reveal_flop"]:
            # Free spins: the action before each spin is a hop or a flop, like any other action.
            saved = self.cfg["actions"]
            self.cfg["actions"] = 1
            self.act(levels, rabbits, True, stats)
            self.cfg["actions"] = saved
        elif self.cfg["reveal_hop"]:
            for i in range(len(rabbits)):
                if free:
                    rabbits[i] = rng.choice(self.reach[rabbits[i]])
                else:
                    rabbits[i] = rng.randrange(CELLS)
                self.step_up(levels, rabbits[i])
                stats["hops"] += 1
        total = 0.0
        cascade = 0
        while True:
            seen = [False] * CELLS
            removed = None
            for start in range(CELLS):
                sym = board[start]
                if seen[start] or sym == SCATTER:
                    continue
                stack = [start]
                seen[start] = True
                group = []
                while stack:
                    cell = stack.pop()
                    group.append(cell)
                    for n in NEIGHBOURS[cell]:
                        if not seen[n] and board[n] == sym:
                            seen[n] = True
                            stack.append(n)
                if len(group) >= 5:
                    mult = 0
                    for cell in group:
                        if levels[cell]:
                            mult += 1 << levels[cell]
                    if mult:
                        stats["mult_wins"] += 1
                    win = PAYTABLE[sym][tier(len(group))] * (mult or 1)
                    total += win
                    if mult > stats["top_mult"]:
                        stats["top_mult"] = mult
                    if removed is None:
                        removed = set()
                    removed.update(group)
            if removed is None:
                break
            cascade += 1
            stats["cascades"] += 1
            for c in range(SIZE):
                column = [board[c * SIZE + r] for r in range(SIZE) if (c * SIZE + r) not in removed]
                fill = self.draw(SIZE - len(column))
                column = fill + column
                board[c * SIZE : c * SIZE + SIZE] = column
            self.act(levels, rabbits, cascade >= self.cfg["flop_from_cascade"], stats)
        return total, board.count(SCATTER)


def new_stats():
    return {"hops": 0, "flops": 0, "cascades": 0, "mult_wins": 0, "top_mult": 0}


def run_base(args):
    cfg, seed, rounds = args
    m = Model(cfg, seed)
    wins = []
    triggers = 0
    stats = new_stats()
    for _ in range(rounds):
        levels = [0] * CELLS
        rabbits = [0] * cfg["rabbits"]
        win, scatters = m.spin(levels, rabbits, False, stats)
        if scatters >= 3:
            triggers += 1
        wins.append(win)
    return wins, triggers, stats


def run_bonus(args):
    cfg, seed, rounds = args
    m = Model(cfg, seed)
    out = []
    for _ in range(rounds):
        stats = new_stats()
        levels = [cfg["start_level"]] * CELLS
        rabbits = [m.rng.randrange(CELLS) for _ in range(cfg["rabbits"])]
        for cell in rabbits:
            m.step_up(levels, cell)
        spins = cfg["spins"]
        played = 0
        total = 0.0
        while played < spins:
            played += 1
            win, scatters = m.spin(levels, rabbits, True, stats)
            total += win
            if scatters >= 3 and spins < cfg["spins"] + 20:
                spins += 5
        out.append((total, max(levels), stats["hops"], stats["flops"], sum(1 for v in levels if v)))
    return out


def quantile(sorted_values, q):
    return sorted_values[min(len(sorted_values) - 1, int(q * len(sorted_values)))]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["base", "bonus"])
    p.add_argument("--rounds", type=int, default=200000)
    p.add_argument("--procs", type=int, default=10)
    p.add_argument("--scatter", type=float, default=0.012, help="share of cells that are scatters")
    p.add_argument("--flop", type=float, default=0.5, help="chance an action is a flop")
    p.add_argument("--reach", type=int, default=2, help="hop range in cells (1 = neighbours)")
    p.add_argument("--cap-level", type=int, default=10, help="10 = 1,024x, 9 = 512x")
    p.add_argument("--flop-radius", type=int, default=0, help="0 = own cell, 1 = 3x3, 99 = whole board")
    p.add_argument("--actions", type=int, default=1, help="actions per rabbit after a winning cascade")
    p.add_argument("--rabbits", type=int, default=1)
    p.add_argument("--flop-from-cascade", type=int, default=1)
    p.add_argument("--no-reveal-hop", action="store_true")
    p.add_argument("--reveal-flop", action="store_true", help="free spins: the action before a spin may be a flop")
    p.add_argument("--start-level", type=int, default=0, help="footprint level on every cell at the start")
    p.add_argument("--spins", type=int, default=10)
    p.add_argument("--price", type=float, default=0, help="bonus: scale so the mean is price x 0.967")
    p.add_argument("--scale", type=float, default=0, help="bonus: fixed paytable scale instead of --price")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--weights", type=str, default="", help="seven symbol weights, comma separated")
    a = p.parse_args()
    if a.weights:
        SYMBOL_WEIGHTS[:] = [float(v) for v in a.weights.split(",")]
    cfg = {
        "weights": list(SYMBOL_WEIGHTS),
        "scatter": a.scatter,
        "flop": a.flop,
        "reach": a.reach,
        "flop_radius": a.flop_radius,
        "cap_level": a.cap_level,
        "actions": a.actions,
        "rabbits": a.rabbits,
        "flop_from_cascade": a.flop_from_cascade,
        "reveal_hop": not a.no_reveal_hop,
        "reveal_flop": a.reveal_flop,
        "start_level": a.start_level,
        "spins": a.spins,
    }
    per = a.rounds // a.procs
    jobs = [(cfg, a.seed * 1000 + i, per) for i in range(a.procs)]
    with Pool(a.procs) as pool:
        if a.kind == "base":
            parts = pool.map(run_base, jobs)
        else:
            parts = pool.map(run_bonus, jobs)

    if a.kind == "base":
        wins = [w for part in parts for w in part[0]]
        n = len(wins)
        triggers = sum(part[1] for part in parts)
        stats = new_stats()
        for part in parts:
            for k in stats:
                stats[k] = max(stats[k], part[2][k]) if k == "top_mult" else stats[k] + part[2][k]
        hits = [w for w in wins if w > 0]
        mean = sum(wins) / n
        print(json.dumps({
            "rounds": n,
            "mean_square": round(sum(w * w for w in wins) / n, 3),
            "win_below_bet_of_hits": round(sum(1 for w in hits if w < 1) / len(hits), 3),
            "hit_rate": round(len(hits) / n, 4),
            "mean_win_paytable_units": round(mean, 4),
            "mean_hit": round(sum(hits) / len(hits), 3),
            "cascades_per_spin": round(stats["cascades"] / n, 3),
            "share_of_wins_multiplied": round(stats["mult_wins"] / max(1, stats["cascades"]), 3),
            "feature_every": round(n / max(1, triggers), 1),
            "top_mult": stats["top_mult"],
        }, indent=1))
        return

    rows = [row for part in parts for row in part]
    n = len(rows)
    raw = sorted(r[0] for r in rows)
    mean = sum(raw) / n
    scale = a.scale or ((a.price * 0.967 / mean) if a.price else 1.0)
    cost = (mean * scale / 0.967)
    report = {
        "sessions": n,
        "mean_raw": round(mean, 3),
        "scale": round(scale, 4),
        "mean_win": round(mean * scale, 2),
        "natural_price": round(cost, 1),
        "median_of_cost": round(quantile(raw, 0.5) * scale / cost, 3),
        "pays_back_cost": round(sum(1 for v in raw if v * scale >= cost) / n, 4),
        "below_tenth_of_cost": round(sum(1 for v in raw if v * scale < cost / 10) / n, 4),
        "p90_of_cost": round(quantile(raw, 0.9) * scale / cost, 2),
        "p99_of_cost": round(quantile(raw, 0.99) * scale / cost, 2),
        "p999_of_cost": round(quantile(raw, 0.999) * scale / cost, 2),
        "max_x": round(raw[-1] * scale, 0),
    }
    for threshold in (1000, 5000, 10000, 25000, 50000):
        k = sum(1 for v in raw if v * scale >= threshold)
        report[f"p_ge_{threshold}"] = f"{k}/{n} = 1 in {round(n / k) if k else 'inf'}"
    capped = sum(min(v * scale, 50000) for v in raw) / n
    report["rtp_lost_to_50k_cap"] = round((mean * scale - capped) / cost, 4)
    for cap in (25000, 50000):
        m1 = sum(min(v * scale, cap) for v in raw) / n
        m2 = sum(min(v * scale, cap) ** 2 for v in raw) / n
        report[f"capped_{cap}"] = {"mean": round(m1, 2), "mean_square": round(m2, 1), "std_in_costs": round((m2 - m1 * m1) ** 0.5 / cost, 2)}
    levels = {}
    for r in rows:
        levels[r[1]] = levels.get(r[1], 0) + 1
    report["top_cell_multiplier_share"] = {f"{1 << k}x": round(v / n, 4) for k, v in sorted(levels.items())}
    report["hops_per_session"] = round(sum(r[2] for r in rows) / n, 1)
    report["flops_per_session"] = round(sum(r[3] for r in rows) / n, 1)
    report["footprint_cells_at_end"] = round(sum(r[4] for r in rows) / n, 1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
