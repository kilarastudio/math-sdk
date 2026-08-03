"""Round lifecycle and output-contract tests for Keris Wild."""

from pathlib import Path
import sys

import src.state.state as state_module


GAME_DIR = Path(__file__).resolve().parents[2] / "games" / "keris_wild"
sys.path.insert(0, str(GAME_DIR))

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402


def create_state(mode="base", criteria="basegame"):
    state = GameState(GameConfig())
    state.betmode = mode
    state.criteria = criteria
    return state


def event_types(state):
    return [event["type"] for event in state.book.events]


def test_forced_stops_map_to_reference_raw_board():
    state = create_state()
    state.reset_book()

    state.draw_keris_board("BR0", stops=[167, 61, 14, 221, 178])

    assert state.transpose_board_string(state.board_string(state.board)) == [
        ["L1", "H1", "W", "H4", "L4"],
        ["L3", "L5", "L5", "W", "L5"],
        ["L1", "L4", "L2", "H2", "S"],
        ["L2", "L3", "L3", "L1", "L3"],
    ]
    assert state.reel_positions == [167, 61, 14, 221, 178]


def test_scatter_snapshot_excludes_held_reels_and_survives_expansion():
    state = create_state()
    state.reset_book()
    state.draw_keris_board("BR0", stops=[4, 84, 3, 113, 16])

    raw_scatter = state.scatter_snapshot(excluded_reels={2})
    expanded_reels = state.expand_current_wilds()

    assert raw_scatter["count"] == 2
    assert raw_scatter["pay"] == 0.0
    assert expanded_reels == [1, 3]
    assert state.board[1][0].name == "W"
    assert all(symbol.name == "W" for symbol in state.board[1])


def test_base_feature_orders_respin_before_free_spins():
    state = create_state(criteria="wincap")

    state.run_spin(sim=0, simulation_seed=20250102)

    types = event_types(state)
    assert types.index("respinStart") < types.index("respinEnd")
    assert types.index("respinEnd") < types.index("freeSpinTrigger")
    assert types.index("freeSpinTrigger") < types.index("enterBonus")
    assert types.count("respinStart") == 1
    respin_start = types.index("respinStart")
    respin_end = types.index("respinEnd")
    assert "setTotalWin" not in types[:respin_start]
    assert types[respin_end + 1 : respin_end + 3] == ["setWin", "setTotalWin"]


def test_forced_wincap_trajectory_is_reachable_and_output_safe():
    state = create_state(mode="bonus_buy", criteria="wincap")

    state.run_spin(sim=0, simulation_seed=20250102)
    book = state.library[1]

    assert book["payoutMultiplier"] == 1_000_000
    assert book["baseGameWins"] == 0.0
    assert book["freeGameWins"] == 10_000.0
    assert [event["index"] for event in book["events"]] == list(range(len(book["events"])))
    assert [event["type"] for event in book["events"]].count("wincap") == 1
    assert next(event for event in book["events"] if event["type"] == "wincap") == {
        "index": next(i for i, event in enumerate(book["events"]) if event["type"] == "wincap"),
        "type": "wincap",
        "amount": 1_000_000,
        "unit": "wager",
    }
    assert book["events"][-1] == {
        "index": len(book["events"]) - 1,
        "type": "finalWin",
        "amount": 1_000_000,
    }
    assert {event["tier"] for event in book["events"] if event["type"] == "bigWinTier"} == {2, 3}


def test_seeded_wincap_book_is_deterministic():
    first = create_state(mode="bonus_buy", criteria="wincap")
    second = create_state(mode="bonus_buy", criteria="wincap")

    first.run_spin(sim=0, simulation_seed=20250102)
    second.run_spin(sim=0, simulation_seed=20250102)

    assert first.library[1] == second.library[1]


def test_respin_scatter_is_neither_paid_nor_triggered():
    state = create_state()
    state.reset_book()
    state.forced_base_stops = [[4, 172, 3, 234, 16]]

    respin_win = state.resolve_base_respin(set())
    scatter = state.scatter_snapshot()

    assert scatter["count"] == 3
    assert scatter["pay"] == 2.5
    assert state.win_manager.running_bet_win == respin_win
    assert "freeSpinTrigger" not in event_types(state)


def test_reset_book_clears_feature_state():
    state = create_state()
    state.sticky_multipliers = {1: 3, 2: 2}
    state.sticky_reels = {1, 2}
    state.respin_held_reels = {3}

    state.reset_book()

    assert state.sticky_multipliers == {}
    assert state.sticky_reels == set()
    assert state.respin_held_reels == set()


def test_run_sims_scopes_payout_sidecar_values_to_the_current_mode(monkeypatch):
    state = create_state()
    captured = {}
    state._payout_ints = [999]

    def fake_run_spin(sim, simulation_seed=None):
        state.sim = sim
        state.reset_book()
        state.book.payout_multiplier = 0.1
        state.imprint_wins()

    monkeypatch.setattr(state, "run_spin", fake_run_spin)
    monkeypatch.setattr(
        state_module,
        "write_json",
        lambda _state, _filename, payout_ints=None: captured.update(payouts=list(payout_ints)),
    )
    monkeypatch.setattr(state_module, "print_recorded_wins", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(state_module, "make_lookup_tables", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(state_module, "make_lookup_pay_split", lambda *_args, **_kwargs: None)

    state.run_sims(
        betmode_copy_list=[],
        betmode="base",
        sim_to_criteria=["basegame"],
        total_threads=1,
        total_repeats=1,
        num_sims=1,
        thread_index=0,
        repeat_count=0,
        compress=False,
        write_event_list=False,
        simulation_seeds=[1],
    )

    assert captured["payouts"] == [10]
