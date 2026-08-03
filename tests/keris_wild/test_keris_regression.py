"""Replay the byte-locked v2.2 RGS deterministic regression package."""

from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pytest


GAME_DIR = Path(__file__).resolve().parents[2] / "games" / "keris_wild"
sys.path.insert(0, str(GAME_DIR))

from game_calculations import KerisWildMath  # noqa: E402
from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402


REGRESSION_PATH = GAME_DIR / "regression" / "keris_wilds_regression_vectors.json"
REGRESSION_SHA256 = "640899e89a5a33025beed47feab2045d94ca1c77f5729049e78ee1de5cba7b54"


def load_vectors():
    assert hashlib.sha256(REGRESSION_PATH.read_bytes()).hexdigest() == REGRESSION_SHA256
    vectors = json.loads(REGRESSION_PATH.read_text())
    assert vectors["game"] == "KERIS WILDS v2.2 RGS"
    return vectors


def make_state(seed):
    state = GameState(GameConfig())
    state.betmode = "bonus_buy"
    state.criteria = "freegame"
    state.rng = np.random.default_rng(seed)
    return state


def row_major_names(state):
    return state.transpose_board_string(state.board_string(state.board))


def replay_base_spin(state):
    state.reset_book()
    state.draw_keris_board("BR0")
    stops = list(state.reel_positions)
    raw_board = row_major_names(state)
    scatter = state.scatter_snapshot()
    expanded = state.expand_current_wilds()
    initial_lines = KerisWildMath.evaluate_lines(state.board, state.config)
    total = initial_lines["totalWin"] + scatter["pay"]
    if expanded:
        state.draw_keris_board("BR0")
        state.apply_held_reels(set(expanded))
        state.expand_current_wilds(excluded_reels=set(expanded))
        total += KerisWildMath.evaluate_lines(state.board, state.config)["totalWin"]
    return {
        "stops": stops,
        "board": raw_board,
        "line_wins": [
            {
                "line": win["meta"]["lineIndex"] - 1,
                "symbol": win["symbol"],
                "kind": win["kind"],
                "mult": win["meta"]["lineMultiplier"],
                "win": win["win"],
            }
            for win in initial_lines["wins"]
        ],
        "total_win": round(total, 6),
        "expanded": bool(expanded),
        "triggered": scatter["count"] >= 3,
    }


def replay_fs_round(state):
    state.reset_book()
    state.betmode = "bonus_buy"
    state.criteria = "freegame"
    state.tot_fs = 10
    state.reset_fs_spin()
    state.run_freespin()
    return state.win_manager.freegame_wins, state.book.events


def test_first_twenty_base_spins_match_locked_vectors():
    vectors = load_vectors()
    state = make_state(vectors["seeds"]["base"])

    for expected in vectors["base_spins"]:
        actual = replay_base_spin(state)
        assert actual["stops"] == expected["stops"]
        assert actual["board"] == expected["board"]
        assert actual["line_wins"] == expected["line_wins"]
        assert actual["total_win"] == expected["total_win"]
        assert actual["expanded"] == ("wildExpand" in expected["events"])
        assert actual["triggered"] == ("fsTrigger" in expected["events"])


def test_first_twenty_free_spin_rounds_match_boards_and_totals():
    vectors = load_vectors()
    state = make_state(vectors["seeds"]["fs"])

    for expected_round in vectors["fs_rounds"]:
        total, events = replay_fs_round(state)
        reveals = [event for event in events if event["type"] == "reveal"]
        assert total == pytest.approx(expected_round["total_win"], abs=1e-9)
        assert len(reveals) == expected_round["spins_played"]
        sticky_at_start = [False, False, False]
        for expected_spin, reveal in zip(expected_round["spins"], reveals):
            assert reveal["paddingPositions"] == expected_spin["stops"]
            active_board = [reel[1:5] for reel in reveal["board"]]
            actual_board = [[cell["name"] for cell in row] for row in zip(*active_board)]
            expected_reveal = [
                [state.config.reels["FR0"][reel][(expected_spin["stops"][reel] + row) % 300]
                 for reel in range(5)]
                for row in range(4)
            ]
            for middle_index, reel in enumerate((1, 2, 3)):
                if sticky_at_start[middle_index]:
                    for row in range(4):
                        expected_reveal[row][reel] = "W"
            assert actual_board == expected_reveal
            sticky_at_start = expected_spin["sticky"]


def test_locked_10000_base_spin_fingerprint():
    vectors = load_vectors()
    state = make_state(vectors["seeds"]["base"])
    totals = []
    respins = triggers = hits = 0
    for _ in range(10_000):
        result = replay_base_spin(state)
        totals.append(result["total_win"])
        respins += result["expanded"]
        triggers += result["triggered"]
        hits += result["total_win"] > 0

    assert round(sum(totals), 6) == vectors["base_summary"]["total_win"]
    assert hits == vectors["base_summary"]["hit_count"]
    assert respins == vectors["base_summary"]["respin_count"]
    assert triggers == vectors["base_summary"]["trigger_count"]


def test_locked_2000_free_spin_round_fingerprint():
    vectors = load_vectors()
    state = make_state(vectors["seeds"]["fs"])
    totals = np.array([replay_fs_round(state)[0] for _ in range(2_000)])

    assert totals.mean() == pytest.approx(vectors["fs_summary"]["ev"], abs=1e-9)
    assert np.median(totals) == vectors["fs_summary"]["median"]
    assert (totals < 10).mean() == vectors["fs_summary"]["p_lt_10x"]
    assert totals.max() == vectors["fs_summary"]["max"]


def test_first_free_spin_round_event_schema_and_order():
    vectors = load_vectors()
    state = make_state(vectors["seeds"]["fs"])
    _, events = replay_fs_round(state)

    assert [event["index"] for event in events] == list(range(len(events)))
    assert [event["type"] for event in events] == [
        "updateFreeSpin", "reveal", "firstSpinBoost", "wildExpand", "stickyWildSet", "setTotalWin",
        "updateFreeSpin", "reveal", "setTotalWin", "updateFreeSpin", "reveal", "setTotalWin",
        "updateFreeSpin", "reveal", "setTotalWin", "updateFreeSpin", "reveal", "setTotalWin",
        "updateFreeSpin", "reveal", "setTotalWin", "updateFreeSpin", "reveal", "winInfo", "setWin",
        "setTotalWin", "wildMultiplierUpdate", "updateFreeSpin", "reveal", "setTotalWin",
        "updateFreeSpin", "reveal", "setTotalWin", "updateFreeSpin", "reveal", "winInfo",
        "lineMultiplier", "setWin", "setTotalWin", "wildMultiplierUpdate", "freeSpinEnd",
    ]
    assert all(len(reveal["board"]) == 5 and all(len(reel) == 6 for reel in reveal["board"])
               for reveal in events if reveal["type"] == "reveal")
    assert all(set(event) == {"index", "type", "line", "mult", "wilds"}
               for event in events if event["type"] == "lineMultiplier")


def test_retrigger_event_uses_sdk_counter_contract():
    vectors = load_vectors()
    state = make_state(vectors["seeds"]["fs"])
    retrigger = None
    for _ in range(2_000):
        _, events = replay_fs_round(state)
        retrigger = next((event for event in events if event["type"] == "freeSpinRetrigger"), None)
        if retrigger is not None:
            break

    assert retrigger is not None
    assert retrigger["addedSpins"] == 5
    assert retrigger["totalFs"] >= 15
    assert retrigger["spinsLeft"] == retrigger["totalFs"] - next(
        event["amount"] for event in reversed(events[: retrigger["index"]]) if event["type"] == "updateFreeSpin"
    ) - 1
    assert all(position["row"] >= 1 for position in retrigger["positions"])
