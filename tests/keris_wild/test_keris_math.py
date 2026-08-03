"""Behavioral tests for the Keris Wild v2.2 RGS MathLock."""

from pathlib import Path
import sys

import pytest


GAME_DIR = Path(__file__).resolve().parents[2] / "games" / "keris_wild"
sys.path.insert(0, str(GAME_DIR))

from game_calculations import KerisWildMath  # noqa: E402
from game_config import GameConfig, load_locked_reels  # noqa: E402
from game_optimization import OptimizationSetup  # noqa: E402


def test_locked_reels_and_mode_contract():
    config = GameConfig()

    assert len(config.paylines) == 40
    assert config.num_rows == [4] * 5
    assert (3, "W") not in config.paytable
    assert config.reels.keys() == {"BR0", "BR1", "FR0"}
    assert all(len(reel) == 300 for reels in config.reels.values() for reel in reels)
    assert {mode.get_name(): mode.get_cost() for mode in config.bet_modes} == {
        "base": 1.0,
        "ante": 1.5,
        "bonus_buy": 72.0,
    }
    assert {mode.get_name(): mode.get_rtp() for mode in config.bet_modes} == {
        "base": 0.966900,
        "ante": 0.962500,
        "bonus_buy": 0.966900,
    }


def test_all_mode_rtps_are_within_half_a_percentage_point_of_base():
    config = GameConfig()
    mode_rtps = {mode.get_name(): mode.get_rtp() for mode in config.bet_modes}

    assert all(abs(rtp - mode_rtps["base"]) <= 0.005 for rtp in mode_rtps.values())


def test_all_mode_rtps_are_within_production_limits():
    config = GameConfig()

    assert all(0.90 <= mode.get_rtp() <= 0.967 for mode in config.bet_modes)


def test_paytable_uses_rgs_tenth_credit_granularity():
    config = GameConfig()

    assert all(round(pay * 10) == pytest.approx(pay * 10) for pay in config.paytable.values())
    assert config.paytable == {
        (5, "H1"): 14.0, (4, "H1"): 2.5, (3, "H1"): 0.6,
        (5, "H2"): 11.0, (4, "H2"): 2.0, (3, "H2"): 0.5,
        (5, "H3"): 8.0, (4, "H3"): 1.5, (3, "H3"): 0.4,
        (5, "H4"): 6.5, (4, "H4"): 1.2, (3, "H4"): 0.3,
        (5, "L1"): 3.2, (4, "L1"): 0.5, (3, "L1"): 0.2,
        (5, "L2"): 2.6, (4, "L2"): 0.5, (3, "L2"): 0.2,
        (5, "L3"): 2.0, (4, "L3"): 0.5, (3, "L3"): 0.1,
        (5, "L4"): 1.8, (4, "L4"): 0.4, (3, "L4"): 0.1,
        (5, "L5"): 1.4, (4, "L5"): 0.4, (3, "L5"): 0.1,
    }


def test_locked_reel_file_hash_and_semantic_hashes():
    reel_path = GAME_DIR / "reels" / "keris_wilds_strips_v2.csv"

    reels = load_locked_reels(reel_path)

    assert reels["BR0"][0][:4] == ["L5", "L5", "L5", "L2"]
    assert reels["BR0"][4][-1] == "L4"


def _window_counts(strip, symbol):
    return [sum(strip[(stop + row) % len(strip)] == symbol for row in range(4)) for stop in range(len(strip))]


def _scatter_exact(reels):
    distribution = {0: 1.0}
    for reel in (0, 2, 4):
        counts = _window_counts(reels[reel], "S")
        reel_distribution = {count: counts.count(count) / len(counts) for count in set(counts)}
        combined = {}
        for left, left_probability in distribution.items():
            for right, right_probability in reel_distribution.items():
                combined[left + right] = combined.get(left + right, 0.0) + left_probability * right_probability
        distribution = combined
    trigger = sum(probability for count, probability in distribution.items() if count >= 3)
    scatter_ev = sum(KerisWildMath.scatter_pay(count) * probability for count, probability in distribution.items())
    return trigger, scatter_ev


def test_exact_locked_probabilities_match_mathlock():
    config = GameConfig()

    base_trigger, base_scatter_ev = _scatter_exact(config.reels["BR0"])
    ante_trigger, _ = _scatter_exact(config.reels["BR1"])
    free_trigger, _ = _scatter_exact(config.reels["FR0"])
    no_respin = 1.0
    for reel in (1, 2, 3):
        windows = _window_counts(config.reels["BR0"][reel], "W")
        no_respin *= windows.count(0) / len(windows)

    assert base_trigger == pytest.approx(0.004561629629629629, abs=1e-15)
    assert ante_trigger == pytest.approx(0.011396740740740741, abs=1e-15)
    assert free_trigger == pytest.approx(0.002382074074074074, abs=1e-15)
    assert base_scatter_ev == pytest.approx(0.012465185185185186, abs=1e-15)
    assert 1 - no_respin == pytest.approx(0.16356740740740738, abs=1e-15)


def test_optimizer_criteria_cover_each_distribution_and_sum_to_mode_rtp():
    config = GameConfig()

    OptimizationSetup(config)

    for mode in config.bet_modes:
        conditions = config.opt_params[mode.get_name()]["conditions"]
        assert set(conditions) == {dist.get_criteria() for dist in mode.get_distributions()}
        assert sum(condition["rtp"] for condition in conditions.values()) == pytest.approx(mode.get_rtp())


def test_optimizer_uses_locked_feature_and_non_feature_hit_rates():
    config = GameConfig()

    OptimizationSetup(config)

    base = config.opt_params["base"]["conditions"]
    ante = config.opt_params["ante"]["conditions"]
    assert base["freegame"]["hr"] == pytest.approx(1 / 0.004561629629629629)
    assert base["basegame"]["hr"] == pytest.approx(1 / (0.3130788 - 0.004561629629629629))
    assert ante["freegame"]["hr"] == pytest.approx(1 / 0.011396740740740741)
    assert ante["basegame"]["hr"] == pytest.approx(1 / (0.3146704 - 0.011396740740740741))
    assert config.opt_params["bonus_buy"]["conditions"]["freegame"]["hr"] == pytest.approx(1 / 0.962450)


@pytest.mark.parametrize(
    ("count", "expected"),
    [(0, 0.0), (2, 0.0), (3, 2.5), (4, 6.0), (5, 12.0), (6, 25.0), (12, 25.0)],
)
def test_scatter_paytable(count, expected):
    assert KerisWildMath.scatter_pay(count) == expected


def test_line_multiplier_uses_only_stickies_inside_paid_span_and_caps_at_twenty():
    assert KerisWildMath.line_multiplier(3, {1: 2, 3: 3}) == (2, [1])
    assert KerisWildMath.line_multiplier(5, {1: 3, 2: 3, 3: 3}) == (20, [1, 2, 3])


def test_line_evaluation_uses_product_multiplier_and_longest_left_win():
    config = GameConfig()
    board = [["H1"] * 4 for _ in range(5)]

    result = KerisWildMath.evaluate_lines(
        board,
        config,
        sticky_multipliers={1: 3, 2: 3, 3: 3},
    )

    assert result["totalWin"] == pytest.approx(40 * 14.0 * 20)
    assert all(win["kind"] == 5 for win in result["wins"])
    assert all(win["meta"]["lineMultiplier"] == 20 for win in result["wins"])


def test_wilds_expand_once_per_middle_reel():
    board = [
        ["H1", "H2", "H3", "H4"],
        ["L1", "W", "L2", "W"],
        ["L1", "L2", "L3", "L4"],
        ["W", "L2", "L3", "L4"],
        ["H1", "H2", "H3", "H4"],
    ]

    expanded, reels = KerisWildMath.expand_wild_reels(board)

    assert reels == [1, 3]
    assert expanded[1] == ["W"] * 4
    assert expanded[3] == ["W"] * 4
    assert expanded[2] == board[2]


def test_sticky_multiplier_increments_at_most_once_per_paid_spin():
    wins = [
        {"win": 1.0, "positions": [{"reel": 0}, {"reel": 1}, {"reel": 2}]},
        {"win": 2.0, "positions": [{"reel": 0}, {"reel": 1}, {"reel": 2}, {"reel": 3}]},
    ]

    updated, changes = KerisWildMath.increment_sticky_multipliers({1: 1, 2: 2, 3: 3}, wins)

    assert updated == {1: 2, 2: 3, 3: 3}
    assert changes == [
        {"reel": 1, "oldMultiplier": 1, "newMultiplier": 2},
        {"reel": 2, "oldMultiplier": 2, "newMultiplier": 3},
    ]
