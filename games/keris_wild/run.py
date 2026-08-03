"""Generate optimized, production-ready Keris Wild publish artifacts."""

from game_config import GameConfig
from game_optimization import OptimizationSetup
from gamestate import GameState
from optimization_program.run_script import OptimizationExecution
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests


NUM_THREADS = 8
RUST_THREADS = 8
BATCHING_SIZE = 6_250
COMPRESSION = True
PROFILING = False
NUM_SIM_ARGS = {"base": 1_000_000, "ante": 250_000, "bonus_buy": 250_000}
RUN_CONDITIONS = {
    "run_sims": True,
    "run_optimization": True,
    "run_analysis": True,
    "run_format_checks": True,
}
TARGET_MODES = list(NUM_SIM_ARGS)


def main():
    """Run the complete SDK pipeline used by MTools publish output."""

    config = GameConfig()
    gamestate = GameState(config)
    if RUN_CONDITIONS["run_optimization"] or RUN_CONDITIONS["run_analysis"]:
        OptimizationSetup(config)

    if RUN_CONDITIONS["run_sims"]:
        create_books(
            gamestate,
            config,
            NUM_SIM_ARGS,
            BATCHING_SIZE,
            NUM_THREADS,
            COMPRESSION,
            PROFILING,
        )
    generate_configs(gamestate)

    if RUN_CONDITIONS["run_optimization"]:
        OptimizationExecution().run_all_modes(config, TARGET_MODES, RUST_THREADS)
        generate_configs(gamestate)
    if RUN_CONDITIONS["run_analysis"]:
        create_stat_sheet(gamestate, custom_keys=[{"symbol": "scatter"}])
    if RUN_CONDITIONS["run_format_checks"]:
        execute_all_tests(config)


if __name__ == "__main__":
    main()
