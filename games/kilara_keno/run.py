"""Generate the books and exact lookup tables of Kilara Keno.

Usage (from the math-sdk root):
    uv run python games/kilara_keno/run.py

Every mode is enumerated in full: each hit/miss order of the draw is published the same number
of times (each copy with its own numbers), at least 100,000 books per mode. Weights come from game_weights.py. The design is in MATH.md.
"""

from gamestate import GameState
from game_config import GameConfig
from game_calculations import all_patterns
from game_weights import write_exact_lookups
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":
    config = GameConfig()
    gamestate = GameState(config)
    num_sim_args = {}
    for bm in config.bet_modes:
        patterns = len(all_patterns(*config.mode_parts(bm.get_name())[1:]))
        num_sim_args[bm.get_name()] = patterns * -(-config.min_books // patterns)
    create_books(gamestate, config, num_sim_args, 300000, 1, True, False)  # one batch: batches drop a remainder
    generate_configs(gamestate)
    for mode, r in write_exact_lookups(config).items():
        print(f"{mode:10s} books={r['books']:5d} rtp={100 * r['rtp']:.4f}%")
