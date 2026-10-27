"""Stake Engine risk checks, as the Studio math-verification page defines them.

utils/rgs_verification.py does not divide ETL by the mode cost, so it flags the buy modes
wrongly. This reads the published lookup tables and applies the page's definitions.

Usage: python games/deep_glint/check_limits.py [publish_files dir]
Wins are multiples of the base bet.
"""

import csv
import json
import math
import os
import sys

pub = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "library", "publish_files")
index = json.load(open(os.path.join(pub, "index.json")))

LIMITS_3 = {"std": 60, "cvar_stake": 700, "cvar_abs": 50000, "p5k": 0.05, "p10k": 0.01, "etl40": 0.9, "etl10k": 0.8, "etl_sum": 1.5, "etl_abs": 10000}
LIMITS_2 = {"std": 50, "cvar_stake": 700, "cvar_abs": 20000, "p5k": 0.010, "p10k": 0.005, "etl40": 0.8, "etl10k": 0.6, "etl_sum": 1.3, "etl_abs": 3000}

rows_out = []
for mode in index["modes"]:
    name, cost = mode["name"], float(mode["cost"])
    dist = {}
    with open(os.path.join(pub, mode["weights"])) as f:
        for _, w, p in csv.reader(f):
            win = int(p) / 100
            dist[win] = dist.get(win, 0) + int(w)
    total = sum(dist.values())
    probs = sorted(((win, w / total) for win, w in dist.items()), key=lambda x: x[0])
    mean = sum(w * p for w, p in probs)
    rtp = mean / cost
    std = math.sqrt(sum(p * (w / cost - rtp) ** 2 for w, p in probs))
    hit = 1 / sum(p for w, p in probs if w > 0)
    p5k = sum(p for w, p in probs if w >= 5000)
    p10k = sum(p for w, p in probs if w >= 10000)
    etl40_abs = sum(w * p for w, p in probs if w > 40 * cost)
    etl10k_abs = sum(w * p for w, p in probs if w > 10000)
    # CVaR 99.9%: expected payout over the worst 0.1% of outcomes.
    tail, acc, need = 0.0, 0.0, 0.001
    for w, p in reversed(probs):
        take = min(p, need - acc)
        tail += w * take
        acc += take
        if acc >= need:
            break
    cvar = tail / need
    maxwin = probs[-1][0]
    maxwin_every = 1 / probs[-1][1]
    zero = dict(probs).get(0.0, 0)
    r = {
        "mode": name,
        "cost": cost,
        "rtp": rtp,
        "std": std,
        "hit": hit,
        "p_zero": zero,
        "max_win": maxwin,
        "max_every": maxwin_every,
        "p5k": p5k,
        "p10k": p10k,
        "cvar_stake": cvar / cost,
        "cvar_abs": cvar,
        "etl40": etl40_abs / cost,
        "etl10k": etl10k_abs / cost,
        "etl_sum": (etl40_abs + etl10k_abs) / cost,
        "etl_abs": etl40_abs + etl10k_abs,
    }
    rows_out.append(r)

for r in rows_out:
    fails3 = [k for k, lim in LIMITS_3.items() if r[k] > lim]
    fails2 = [k for k, lim in LIMITS_2.items() if r[k] > lim]
    print(
        f"{r['mode']:6s} cost {r['cost']:>6g} | RTP {100 * r['rtp']:.2f}% std {r['std']:.2f} hit 1/{r['hit']:.2f} "
        f"zero {100 * r['p_zero']:.1f}% | max {r['max_win']:.0f}x every {r['max_every']:,.0f} | "
        f"P5k {r['p5k']:.2e} P10k {r['p10k']:.2e} | CVaR {r['cvar_abs']:.0f} ({r['cvar_stake']:.1f}/stake) | "
        f"ETL40 {r['etl40']:.3f} ETL10k {r['etl10k']:.3f} sum {r['etl_sum']:.3f} abs {r['etl_abs']:.1f} "
        f"| 3★ fails: {fails3 or 'none'} | 2★ fails: {fails2 or 'none'}"
    )
