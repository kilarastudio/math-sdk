"""Natural lookup tables for Floppy Rabbit.

Instead of the Rust optimizer (which reshapes each category into its own trial distribution),
every book keeps the frequency the reels give it. Nothing is placed by hand, the max win included:

* Base game. The share of spins that win without triggering free spins, and that share's
  average, are what unforced play gives (library/natural.json, from run.py --natural) and
  what the base game books average.
* Free spins. Books keep their simulated frequency. Books at or above the tail threshold
  also come from a dedicated "freegame_tail" sample; all tail books share the probability the
  reels give the tail (tail books kept / rounds tried), so the extra books add detail to the
  rare range, up to the max win, without changing its weight.
* The one free number per spin mode is how often free spins trigger. It is solved so the mode
  returns its RTP at its cost, and should land next to the natural rate in base.
  In ante it is what the higher cost buys.
* A bought mode is all free spins; its cost is their natural average / RTP, and the small
  remainder is closed by a smooth power tilt w ~ (1 + win) ** theta.

So the published distribution has the shape the reels actually produce, with no gaps.
"""

import csv
import json
import os

SCALE = 2**50  # total weight per mode; integer weights must fit in uint64
# Engine's RTP band ends at 96.70%. Aim a hair under the configured RTP so that rounding the
# weights to integers can never put a mode above it (the result still reads 96.70%).
RTP_MARGIN = 0.00002
# Spin modes and the mode whose unforced base game they play.
SPIN_MODES = {"base": "base", "ante": "base"}


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


def read_tail_attempts(library_path: str, mode: str) -> int:
    """Rounds tried while sampling the mode's tail books (recorded by gamestate.run_spin)."""
    with open(os.path.join(library_path, "forces", f"force_record_{mode}.json"), encoding="UTF-8") as f:
        records = json.load(f)
    attempts = 0
    for record in records:
        for key in record["search"]:
            if key["name"] == "tail_attempts":
                attempts += int(key["value"]) * len(record["bookIds"])
    return attempts


def tilt(wins: list, base: list, target_avg: float) -> tuple:
    """Relative weights base * (1 + win) ** theta whose weighted average is target_avg."""

    def avg(theta):
        t = [b * (1 + w) ** theta for b, w in zip(base, wins)]
        return sum(ti * w for ti, w in zip(t, wins)) / sum(t)

    lo, hi = -1.0, 1.0
    assert avg(lo) <= target_avg <= avg(hi), f"average {target_avg} is far from natural: change the cost or the feature"
    for _ in range(100):
        mid = (lo + hi) / 2
        if avg(mid) < target_avg:
            lo = mid
        else:
            hi = mid
    theta = (lo + hi) / 2
    return [b * (1 + w) ** theta for b, w in zip(base, wins)], theta


def freegame_shares(by_criteria: dict, tail_min, attempts: int) -> tuple:
    """Free spins books with their natural relative weights (summing to 1)."""
    sims = by_criteria["freegame"]
    if tail_min is None or "freegame_tail" not in by_criteria:
        return sims, [1.0 / len(sims)] * len(sims)
    tier = by_criteria["freegame_tail"]
    body = [(s, w) for s, w in sims if w < tail_min]
    tail = [(s, w) for s, w in sims if w >= tail_min] + tier
    # Pooled estimate of how often free spins reach the tail: ordinary books plus the tail sampling.
    tail_share = (len(sims) - len(body) + len(tier)) / (len(sims) + attempts)
    base = [(1 - tail_share) / len(body)] * len(body) + [tail_share / len(tail)] * len(tail)
    return body + tail, base


def build_mode(config, mode: str, books: list, natural: dict) -> tuple:
    """Return ({sim: probability}, summary) for one mode."""
    betmode = next(bm for bm in config.bet_modes if bm.get_name() == mode)
    cost = betmode.get_cost()
    target = (config.rtp - RTP_MARGIN) * cost  # expected payout per round, in base bets
    tail_min = None
    for d in betmode.get_distributions():
        tail_min = d._conditions.get("min_win", tail_min)
    by_criteria = {}
    for sim, criteria, cents in books:
        by_criteria.setdefault(criteria, []).append((sim, cents / 100))

    attempts = read_tail_attempts(config.library_path, mode) if "freegame_tail" in by_criteria else 0
    fs_sims, fs_base = freegame_shares(by_criteria, tail_min, attempts)
    fs_wins = [w for _, w in fs_sims]
    fs_natural_avg = sum(b * w for b, w in zip(fs_base, fs_wins))
    probs, summary = {}, {}

    if mode not in SPIN_MODES:
        rel, theta = tilt(fs_wins, fs_base, target) if abs(target - fs_natural_avg) > 1e-9 else (fs_base, 0.0)
        total = sum(rel)
        for (sim, _), r in zip(fs_sims, rel):
            probs[sim] = r / total
        summary["freegame"] = {"hr": 1.0, "avg": target, "natural_hr": 1.0, "natural_avg": fs_natural_avg, "theta": theta}
        return probs, summary

    nat = natural[SPIN_MODES[mode]]
    hit_given_no_fs = nat["p_basegame"] / (1 - nat["p_freegame"])
    base_sims = by_criteria["basegame"]
    base_avg = sum(w for _, w in base_sims) / len(base_sims)
    base_value = hit_given_no_fs * base_avg  # a spin that does not trigger free spins
    p_fs = (target - base_value) / (fs_natural_avg - base_value)
    assert 0 < p_fs < 1, f"{mode}: free spins rate {p_fs} is not a probability; check the cost"
    p_base = (1 - p_fs) * hit_given_no_fs
    p_zero = 1 - p_fs - p_base
    for (sim, _), share in zip(fs_sims, fs_base):
        probs[sim] = p_fs * share
    for sim, _ in base_sims:
        probs[sim] = p_base / len(base_sims)
    zeros = by_criteria["0"]
    for sim, _ in zeros:
        probs[sim] = p_zero / len(zeros)
    summary["freegame"] = {
        "hr": 1 / p_fs,
        "avg": fs_natural_avg,
        "natural_hr": 1 / nat["p_freegame"],
        "natural_avg": fs_natural_avg,
        "theta": 0.0,
    }
    summary["basegame"] = {
        "hr": 1 / p_base,
        "avg": base_avg,
        "natural_hr": 1 / nat["p_basegame"],
        "natural_avg": nat["basegame_avg"],
        "theta": 0.0,
    }
    summary["0"] = {
        "hr": 1 / p_zero,
        "avg": 0.0,
        "natural_hr": 1 / (1 - nat["p_freegame"] - nat["p_basegame"]),
        "natural_avg": 0.0,
        "theta": 0.0,
    }
    return probs, summary


def write_natural_lookups(config, modes: list) -> dict:
    """Write library/publish_files/lookUpTable_<mode>_0.csv for each mode and return a summary."""
    with open(os.path.join(config.library_path, "natural.json"), encoding="UTF-8") as f:
        natural = json.load(f)
    report = {}
    for mode in modes:
        books = read_books(config.library_path, mode)
        probs, summary = build_mode(config, mode, books, natural)
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
