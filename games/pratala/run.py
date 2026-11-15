"""Main file for generating results for Pratala.

Usage (from the math-sdk root):
    uv run python games/pratala/run.py                    # full pipeline, every mode
    uv run python games/pratala/run.py --sims 2000 --raw  # books only, small sample
    uv run python games/pratala/run.py --natural 2000000  # only measure what the reels do unforced
    uv run python games/pratala/run.py --skip-sims        # reweight existing books and re-check

Weights come from game_weights.py (natural frequencies), not the Rust optimizer.
The design, its targets and the last measurements are in MATH.md.
"""

import argparse
import json
import os
import random
import subprocess
import sys
from multiprocessing import Pool

from gamestate import GameState
from game_config import GameConfig
from game_weights import write_natural_lookups, describe_as_conditions
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

MODES = ["base", "ante", "boost", "bonus", "super", "hoard"]
# Spin modes get more books: only a tenth of them are free spins.
DEFAULT_SIMS = {"base": 200_000, "ante": 200_000, "boost": 200_000, "bonus": 100_000, "super": 100_000, "hoard": 100_000}
# Modes whose base game differs (Glint Strike rate); ante plays the base mode's base game.
NATURAL_MODES = ["base", "boost"]


def natural_chunk(args) -> dict:
    """Play unforced base spins of one mode and count what happens."""
    mode, spins, seed = args
    gamestate = GameState(GameConfig())
    gamestate.betmode, gamestate.criteria = mode, "basegame"
    random.seed(seed)
    out = {"spins": spins, "hits": 0, "win": 0.0, "win_sq": 0.0, "triggers": {}}
    trigger = min(gamestate.config.freespin_triggers[gamestate.config.basegame_type])
    for _ in range(spins):
        win, scatters = gamestate.run_natural_spin()
        if scatters >= trigger:
            out["triggers"][scatters] = out["triggers"].get(scatters, 0) + 1
        elif win > 0:
            out["hits"] += 1
            out["win"] += win
            out["win_sq"] += win * win
    return out


def measure_natural(config, spins: int, threads: int) -> dict:
    """Unforced base game numbers per mode, written to library/natural.json for game_weights.py."""
    result = {}
    per = spins // threads
    # Each worker builds its own game state, which creates the SDK's output folders if they are
    # missing; make them here first so the workers do not race to create the same one.
    GameState(config)
    for mode in NATURAL_MODES:
        with Pool(threads) as pool:
            parts = pool.map(natural_chunk, [(mode, per, 7919 * (i + 1)) for i in range(threads)])
        n = sum(p["spins"] for p in parts)
        triggers = {}
        for p in parts:
            for k, v in p["triggers"].items():
                triggers[k] = triggers.get(k, 0) + v
        n_trigger = sum(triggers.values())
        result[mode] = {
            "spins": n,
            "p_freegame": n_trigger / n,
            "p_basegame": sum(p["hits"] for p in parts) / n,
            "basegame_avg": sum(p["win"] for p in parts) / max(1, sum(p["hits"] for p in parts)),
            "basegame_win_sq": sum(p["win_sq"] for p in parts) / n,
            "trigger_scatters": {str(k): v for k, v in sorted(triggers.items())},
        }
        r = result[mode]
        print(
            f"natural {mode}: free spins 1 in {1 / r['p_freegame']:.1f}, base win 1 in {1 / r['p_basegame']:.2f} "
            f"averaging {r['basegame_avg']:.3f}x, scatters at trigger {r['trigger_scatters']}"
        )
    with open(os.path.join(config.library_path, "natural.json"), "w", encoding="UTF-8") as f:
        json.dump(result, f, indent=1)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sims", type=int, default=None, help="simulations per mode (default: 200k spin modes, 100k buy modes)")
    parser.add_argument("--modes", nargs="+", default=MODES)
    parser.add_argument("--raw", action="store_true", help="only create books")
    parser.add_argument("--skip-sims", action="store_true", help="reuse the books already in library/")
    parser.add_argument("--natural", type=int, default=None, help="only measure this many unforced base spins per mode")
    parser.add_argument("--threads", type=int, default=10)
    args = parser.parse_args()

    num_threads = args.threads
    compression = True
    profiling = False

    config = GameConfig()
    gamestate = GameState(config)

    if args.natural is not None:
        measure_natural(config, args.natural, num_threads)
        sys.exit(0)

    if not args.skip_sims:
        num_sim_args = {mode: args.sims or DEFAULT_SIMS[mode] for mode in args.modes}
        fewest = min(num_sim_args.values())
        batching_size = 10000 if fewest >= 10000 * num_threads else max(1, fewest // num_threads)
        create_books(gamestate, config, num_sim_args, batching_size, num_threads, compression, profiling)
        if not os.path.exists(os.path.join(config.library_path, "natural.json")):
            measure_natural(config, 4_000_000, num_threads)
    generate_configs(gamestate)

    if not args.raw:
        # Always reweight every mode: the published index lists them all.
        report = write_natural_lookups(config, MODES)
        for mode, categories in report.items():
            print(f"\n{mode}:")
            for criteria, s in categories.items():
                print(
                    f"  {criteria:9s} 1 in {s['hr']:,.2f}  avg {s['avg']:.2f}x"
                    f"  (natural: 1 in {s['natural_hr']:,.2f}, avg {s['natural_avg']:.2f}x, tilt {s['theta']:+.4f})"
                )
        config.opt_params = describe_as_conditions(config, report)
        generate_configs(gamestate)
        create_stat_sheet(gamestate, custom_keys=[{"symbol": "scatter"}])
        execute_all_tests(config)
        # Engine's limits and the design targets are checked by the studio's two scripts, when present.
        workspace = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
        audit = os.path.join(workspace, ".claude", "skills", "stake-reviewer", "scripts", "math_audit.py")
        profile = os.path.join(workspace, ".claude", "skills", "stake-math", "scripts", "math_profile.py")
        game_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(audit):
            subprocess.run([sys.executable, audit, config.publish_path], check=False)
        if os.path.exists(profile):
            subprocess.run(
                [sys.executable, profile, game_dir, "--targets", os.path.join(game_dir, "math_targets.json")], check=False
            )
