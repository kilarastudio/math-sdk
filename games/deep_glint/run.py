"""Main file for generating results for DEEP GLINT.

Usage (from the math-sdk root):
    uv run python games/deep_glint/run.py                   # full pipeline, every mode
    uv run python games/deep_glint/run.py --sims 1000 --raw  # books only
    uv run python games/deep_glint/run.py --skip-sims        # reweight existing books and re-check

Weights come from game_weights.py (natural frequencies), not the Rust optimizer.
"""

import argparse
import subprocess
import sys

from gamestate import GameState
from game_config import GameConfig
from game_weights import write_natural_lookups, describe_as_conditions
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

MODES = ["base", "ante", "boost", "bonus", "super"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sims", type=int, default=int(1e5), help="simulations per mode")
    parser.add_argument("--modes", nargs="+", default=MODES)
    parser.add_argument("--raw", action="store_true", help="only create books")
    parser.add_argument("--skip-sims", action="store_true", help="reuse the books already in library/")
    parser.add_argument("--threads", type=int, default=10)
    args = parser.parse_args()

    num_threads = args.threads
    batching_size = 10000 if args.sims >= 10000 * args.threads else max(1, args.sims // args.threads)
    compression = True
    profiling = False

    num_sim_args = {mode: args.sims for mode in args.modes}

    config = GameConfig()
    gamestate = GameState(config)

    if not args.skip_sims:
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )
    generate_configs(gamestate)

    if not args.raw:
        # Always reweight every mode: ante and boost take their free spins rate from base.
        report = write_natural_lookups(config, MODES)
        for mode, categories in report.items():
            print(f"\n{mode}:")
            for criteria, s in categories.items():
                print(
                    f"  {criteria:9s} 1 in {s['hr']:,.1f}  avg {s['avg']:.2f}x"
                    f"  (natural {s['natural_avg']:.2f}x, tilt {s['theta']:+.3f})"
                )
        config.opt_params = describe_as_conditions(config, report)
        generate_configs(gamestate)
        create_stat_sheet(gamestate, custom_keys=[{"symbol": "scatter"}])
        execute_all_tests(config)
        subprocess.run([sys.executable, __file__.replace("run.py", "check_limits.py")], check=True)
