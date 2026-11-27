"""Generate the books and exact lookup tables of Keno Chain.

Usage (from the math-sdk root):
    uv run python games/keno_chain/run.py

Every mode is enumerated in full: each round (an order of hits, misses and Kilau balls, on a
board that marks 1 or 3 Kilau numbers) is published the same number of times, each copy with
its own numbers, at least 100,000 books per mode. Weights come from game_weights.py. The design
is in MATH.md.

Afterwards, from the math-sdk root:
    uv run python games/keno_chain/verify_books.py
    uv run python -m utils.rgs_verification -g keno_chain
"""

import glob
import os

from gamestate import GameState
from game_config import GameConfig
from game_calculations import mode_rounds
from game_weights import write_exact_lookups
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":
    config = GameConfig()
    gamestate = GameState(config)
    num_sim_args = {}
    for bm in config.bet_modes:
        _, picks, draws, options = config.mode_parts(bm.get_name())
        rounds = len(mode_rounds(picks, draws, options, config.board_numbers))
        num_sim_args[bm.get_name()] = rounds * -(-config.min_books // rounds)
    create_books(gamestate, config, num_sim_args, 300000, 1, True, False)  # one batch: batches drop a remainder
    generate_configs(gamestate)
    # create_books leaves a books_<mode>.verification.json per mode. With every mode made in one
    # call, each of those files also counts the modes made before it, and the SDK's format check
    # trusts them when they exist. Without them it reads the books themselves.
    for sidecar in glob.glob(os.path.join(config.library_path, "configs", "books_*.verification.json")):
        os.remove(sidecar)
    for mode, r in write_exact_lookups(config).items():
        print(f"{mode:10s} books={r['books']:5d} rtp={100 * r['rtp']:.4f}%")
