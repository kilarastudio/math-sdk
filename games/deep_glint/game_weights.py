"""Natural lookup tables for DEEP GLINT.

Instead of the Rust optimizer (which reshapes each category into its own trial distribution),
every book keeps its simulated, natural frequency. Per mode and category we only set:

* how often the category happens (1 in `hr` rounds), and
* its average win, by a smooth power tilt w ~ (1 + win) ** theta when it must move.

Free spins books at or above config.fs_tail_min also come from a dedicated "freegame_tail"
sample. All tail books share the tail's natural probability (the share of ordinary free spins
books that reach it), so the extra books add detail to the rare range without changing its weight.

So the published distribution has the shape the reels actually produce, with no gaps.
"""

import csv
import os

SCALE = 2**50  # total weight per mode; integer weights must fit in uint64
NATURAL = None  # keep the simulated average
REST = "rest"  # take whatever RTP the other categories leave

# Per mode, in evaluation order. hr = 1 in hr rounds; avg in multiples of the base bet.
# Spin modes: the zero-win category "0" takes the probability that is left.
TARGETS = {
    "base": {
        "wincap": {"hr": 5_000_000},
        "basegame": {"hr": 3.3, "avg": NATURAL},
        "freegame": {"hr": REST, "avg": NATURAL},
    },
    # Twice the base free spins chance. hr "base/2" is resolved from the base result.
    "ante": {
        "wincap": {"hr": 4_000_000},
        "freegame": {"hr": "base/2", "avg": NATURAL},
        "basegame": {"hr": 3.3, "avg": REST},
    },
    # Same free spins chance as base; the Glint Strike on every spin is what the extra cost buys.
    "boost": {
        "wincap": {"hr": 2_857_143},
        "freegame": {"hr": "base", "avg": NATURAL},
        "basegame": {"hr": 3.3, "avg": REST},
    },
    "bonus": {
        "wincap": {"hr": 37_500},
        "freegame": {"hr": REST, "avg": REST},
    },
    "super": {
        "wincap": {"hr": 12_500},
        "freegame": {"hr": REST, "avg": REST},
    },
}


def read_books(library_path: str, mode: str) -> list:
    """Return [(sim, criteria, payout_cents)] in lookup-table order."""
    payouts = {}
    with open(os.path.join(library_path, "lookup_tables", f"lookUpTable_{mode}.csv"), encoding="UTF-8") as f:
        for sim, _, cents in csv.reader(f):
            payouts[int(sim)] = int(cents)
    books = []
    with open(os.path.join(library_path, "lookup_tables", f"lookUpTableSegmented_{mode}.csv"), encoding="UTF-8") as f:
        for sim, criteria, _, _ in csv.reader(f):
            books.append((int(sim), criteria, payouts[int(sim)]))
    return books


def tilt(wins: list, base: list, target_avg: float) -> list:
    """Relative weights base * (1 + win) ** theta whose weighted average is target_avg."""

    def avg(theta):
        t = [b * (1 + w) ** theta for b, w in zip(base, wins)]
        return sum(ti * w for ti, w in zip(t, wins)) / sum(t)

    lo, hi = -4.0, 4.0
    assert avg(lo) <= target_avg <= avg(hi), f"average {target_avg} out of reach"
    for _ in range(100):
        mid = (lo + hi) / 2
        if avg(mid) < target_avg:
            lo = mid
        else:
            hi = mid
    theta = (lo + hi) / 2
    return [b * (1 + w) ** theta for b, w in zip(base, wins)], theta


def natural_shares(config, by_criteria: dict, criteria: str) -> tuple:
    """Books of a category with their natural relative weights.

    For free spins, books below the tail threshold keep the ordinary sample's frequency, and
    every tail book (ordinary or from freegame_tail) shares the tail's natural probability.
    """
    sims = by_criteria[criteria]
    if criteria != "freegame" or "freegame_tail" not in by_criteria:
        return sims, [1.0 / len(sims)] * len(sims)
    tail_min = config.fs_tail_min
    body = [(s, w) for s, w in sims if w < tail_min]
    tail = [(s, w) for s, w in sims if w >= tail_min] + by_criteria["freegame_tail"]
    tail_share = (len(sims) - len(body)) / len(sims)
    assert tail_share > 0, "no ordinary free spins book reached the tail; simulate more"
    base = [(1 - tail_share) / len(body)] * len(body) + [tail_share / len(tail)] * len(tail)
    return body + tail, base


def build_mode(config, mode: str, books: list, resolved_hr: dict) -> tuple:
    """Return ({sim: probability}, summary) for one mode."""
    cost = next(bm.get_cost() for bm in config.bet_modes if bm.get_name() == mode)
    rtp_left = config.rtp * cost  # expected payout per round, in base bets
    prob_left = 1.0
    by_criteria = {}
    for sim, criteria, cents in books:
        by_criteria.setdefault(criteria, []).append((sim, cents / 100))

    probs, summary = {}, {}
    plan = list(TARGETS[mode].items())
    # Fixed-RTP categories first, then the one that takes the rest.
    plan.sort(key=lambda kv: REST in (kv[1].get("hr"), kv[1].get("avg")))
    for criteria, target in plan:
        sims, base = natural_shares(config, by_criteria, criteria)
        wins = [w for _, w in sims]
        natural_avg = sum(b * w for b, w in zip(base, wins))
        hr = target["hr"]
        if isinstance(hr, str) and hr != REST:
            hr = resolved_hr["base"] / 2 if hr == "base/2" else resolved_hr["base"]
        avg = target.get("avg", NATURAL)
        if hr == REST and avg == REST:
            # Buy modes: this category is every round that is not a max win.
            p = prob_left
            avg = rtp_left / p
        elif hr == REST:
            avg = natural_avg if avg is NATURAL else avg
            p = rtp_left / avg
        else:
            p = 1 / hr
            avg = (rtp_left / p) if avg == REST else (natural_avg if avg is NATURAL else avg)
        rel, theta = tilt(wins, base, avg) if abs(avg - natural_avg) > 1e-9 else (base, 0.0)
        total = sum(rel)
        for (sim, _), r in zip(sims, rel):
            probs[sim] = p * r / total
        rtp_left -= p * avg
        prob_left -= p
        summary[criteria] = {"hr": 1 / p, "avg": avg, "natural_avg": natural_avg, "theta": theta}
        if criteria == "freegame":
            resolved_hr[mode] = 1 / p

    if "0" in by_criteria:
        zeros = by_criteria["0"]
        assert prob_left > 0, f"{mode}: no probability left for zero wins"
        for sim, _ in zeros:
            probs[sim] = prob_left / len(zeros)
        summary["0"] = {"hr": 1 / prob_left, "avg": 0.0, "natural_avg": 0.0, "theta": 0.0}
    else:
        assert abs(prob_left) < 1e-9 and abs(rtp_left) < 1e-6, f"{mode}: targets do not close"
    return probs, summary


def write_natural_lookups(config, modes: list) -> dict:
    """Write library/publish_files/lookUpTable_<mode>_0.csv for each mode and return a summary."""
    resolved_hr, report = {}, {}
    order = sorted(modes, key=lambda m: m != "base")  # base first: ante and boost refer to it
    for mode in order:
        books = read_books(config.library_path, mode)
        probs, summary = build_mode(config, mode, books, resolved_hr)
        path = os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv")
        with open(path, "w", encoding="UTF-8") as f:
            for sim, _, cents in books:
                f.write(f"{sim},{max(1, round(probs[sim] * SCALE))},{cents}\n")
        report[mode] = summary
    return report


def describe_as_conditions(config, report: dict) -> dict:
    """Express the chosen categories in the optimizer's `opt_params` shape.

    Only descriptive: the SDK writes them to math_config.json, and the stat sheet reads them
    to split each mode into base game and free spins.
    """
    costs = {bm.get_name(): bm.get_cost() for bm in config.bet_modes}
    opt_params = {}
    for mode, categories in report.items():
        conditions = {}
        for criteria, s in categories.items():
            conditions[criteria] = {
                "hr": round(s["hr"], 4),
                "av_win": round(s["avg"], 4),
                "rtp": round(s["avg"] / s["hr"] / costs[mode], 6),
                "search_range": (-1, -1),
                "force_search": {},
            }
        opt_params[mode] = {"conditions": conditions, "scaling": [], "parameters": {}}
    return opt_params
