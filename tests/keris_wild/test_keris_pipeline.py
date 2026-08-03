"""Production pipeline safeguards for Keris Wild publish artifacts."""

import importlib.util
from pathlib import Path
import sys


GAME_DIR = Path(__file__).resolve().parents[2] / "games" / "keris_wild"
sys.path.insert(0, str(GAME_DIR))

SPEC = importlib.util.spec_from_file_location("keris_wild_run", GAME_DIR / "run.py")
assert SPEC is not None and SPEC.loader is not None
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)


def test_default_pipeline_builds_optimized_publish_artifacts():
    assert RUN.NUM_THREADS == 8
    assert RUN.RUST_THREADS == 8
    assert RUN.BATCHING_SIZE == 6_250
    assert RUN.COMPRESSION is True
    assert RUN.NUM_SIM_ARGS == {
        "base": 1_000_000,
        "ante": 250_000,
        "bonus_buy": 250_000,
    }
    assert RUN.RUN_CONDITIONS == {
        "run_sims": True,
        "run_optimization": True,
        "run_analysis": True,
        "run_format_checks": True,
    }


def test_target_modes_follow_the_configured_simulation_modes():
    assert RUN.TARGET_MODES == list(RUN.NUM_SIM_ARGS)
